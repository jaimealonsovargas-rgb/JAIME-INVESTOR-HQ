"""Reviewed pilot links, derived from preserved evidence; never merge provider records."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

from sqlalchemy import select
from app.data_identity import fingerprint
from app.filing_reconciliation import xml_document, XBRLI
from app.sec_http import MAX_BYTES, statement_url
from app.sec_store import FILINGS, SNAPSHOTS
from app.universe_store import LISTINGS, VERSIONS, utc_text
from app.ibkr_contract_evidence import contract_evidence

PILOT = json.loads(Path(__file__).with_name('pilot_identity.json').read_text(encoding='utf-8'))


def archived_bytes(folder, digest, suffix='.json.gz'):
    if not re.fullmatch('[a-f0-9]{64}', digest):
        raise ValueError('INVALID_ARCHIVE_REFERENCE')
    with gzip.open(folder / (digest + suffix), 'rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('ARCHIVE_INTEGRITY_FAILED')
    return raw


def common_stock_cover(raw, cik, symbol, venue):
    """A bond may reuse the common-stock ticker: all three fields must share a context."""
    root, _ = xml_document(raw)
    fields = {'EntityCentralIndexKey', 'DocumentPeriodEndDate', 'Security12bTitle', 'TradingSymbol', 'SecurityExchangeName'}
    groups, identifiers, periods = {}, set(), set()
    contexts = {e.get('id'): e for e in root.findall(XBRLI+'context')}
    for element in root:
        name = re.fullmatch(r'\{https?://xbrl\.sec\.gov/dei/\d{4}\}([A-Za-z0-9]+)', element.tag)
        if not name or name[1] not in fields:
            continue
        field, context = name[1], element.get('contextRef')
        text = ' '.join(''.join(element.itertext()).split())
        if not context or context not in contexts or len(text) > 500:
            raise ValueError('INVALID_COVER_CONTEXT')
        group = groups.setdefault(context, {})
        if field in group and group[field] != text:
            raise ValueError('CONFLICTING_COVER_FACT')
        group[field] = text
        if field == 'EntityCentralIndexKey': identifiers.add(text)
        if field == 'DocumentPeriodEndDate': periods.add(text)
    if identifiers != {cik} or len(periods) != 1:
        raise ValueError('FILER_IDENTITY_CONFLICT')
    matches = []
    for context, fields in groups.items():
        if (fields.get('TradingSymbol') != symbol or fields.get('SecurityExchangeName') != venue
                or not re.fullmatch(r'Common stock(?:, .+)?', fields.get('Security12bTitle', ''), re.I)):
            continue
        entity = contexts[context].find(XBRLI+'entity/'+XBRLI+'identifier')
        end = contexts[context].find(XBRLI+'period/'+XBRLI+'endDate')
        if (entity is None or entity.text != cik or entity.get('scheme') != 'http://www.sec.gov/CIK'
                or end is None or end.text not in periods):
            raise ValueError('COVER_CONTEXT_IDENTITY_CONFLICT')
        matches.append(dict(context_id=context, security_title=fields['Security12bTitle'], report_end=end.text))
    if len(matches) != 1:
        raise ValueError('COMMON_STOCK_CLASS_AMBIGUOUS')
    return matches[0]


def identity_evidence(connection, sec_root, listing_id, cutoff, pilot=None, contract_review=None):
    cutoff = cutoff.astimezone(timezone.utc)
    pilot = PILOT if pilot is None else pilot
    base = dict(state='UNREVIEWED', reason='Instrumento fuera del piloto de identidad revisado.',
        cik=None, instrument_id=None, market_listing_id=None, sec_listing_id=None,
        security_title=None, known_from=None, evidence=[], native_currency=None,
        native_currency_state='UNVERIFIED', native_currency_reason='Requiere un vínculo de empresa y clase documentado y evidencia de divisa independiente.',
        current_contract=None, price_unit=None, historical_identity=False)
    spec = next((s for s in pilot['items'] if listing_id in (s['sec_listing_id'],s['market_listing_id'])),None)
    if spec is None or datetime.fromisoformat(pilot['reviewed_at']) > cutoff:
        return base
    base.update(state='REVIEW_REQUIRED', reason='La evidencia no permite confirmar el vínculo vigente.')
    try:
        rows = {}
        for provider,key in [('SEC','sec'),('ALPACA','market')]:
            ident = spec[key+'_listing_id']
            row = connection.execute(select(LISTINGS).where(LISTINGS.c.id==ident)).mappings().one_or_none()
            version = connection.execute(select(VERSIONS).where(VERSIONS.c.listing_id==ident,
                VERSIONS.c.known_from<=utc_text(cutoff)).order_by(VERSIONS.c.known_from.desc()).limit(1)).mappings().first()
            if not row or not version:
                raise ValueError('CATALOGUE_EVIDENCE_MISSING')
            # Current assertions are not used to reconstruct an older identity silently.
            payload = {k:v for k,v in version['payload'].items() if k!='state'}
            if (version['payload'].get('state')!='IDENTIFIED' or row['state']!='IDENTIFIED'
                    or fingerprint(payload)!=spec[key+'_identity_hash']
                    or fingerprint(row['payload'])!=spec[key+'_identity_hash']
                    or row['provider']!=provider or row['symbol']!=spec['symbol'] or row['venue']!='NASDAQ'):
                raise ValueError('CATALOGUE_IDENTITY_CHANGED')
            peers = list(connection.scalars(select(LISTINGS.c.id).where(LISTINGS.c.provider==provider,
                LISTINGS.c.symbol==row['symbol'], LISTINGS.c.venue==row['venue'], LISTINGS.c.state!='NOT_OBSERVED')))
            if peers!=[ident]:
                raise ValueError('CATALOGUE_AMBIGUOUS')
            rows[key] = row
            base['evidence'].append(dict(kind='CATALOGUE_'+provider,id=version['id'],
                sha256=version['payload_hash'],url=version['source'],received_at=version['known_from']))
        if rows['sec']['cik']!=spec['cik'] or rows['market']['payload'].get('category')!='US_EQUITY':
            raise ValueError('CATALOGUE_CLASS_CONFLICT')
        if (rows['market']['payload'].get('provider_status')!='active'
                or not rows['market']['name'].lower().endswith(' common stock')):
            raise ValueError('PROVIDER_CLASS_UNVERIFIED')
        receipt = spec['filing']
        path = sec_root/'statements'/spec['cik']/(receipt['accession']+'.json')
        if json.loads(path.read_text(encoding='utf-8'))!=receipt or datetime.fromisoformat(receipt['received_at'])>cutoff:
            raise ValueError('FILING_RECEIPT_CHANGED')
        ref = receipt['instance']
        if receipt['cik']!=spec['cik'] or ref['url']!=statement_url(spec['cik'],receipt['accession'],receipt['primary'],'instance'):
            raise ValueError('FILING_SOURCE_INVALID')
        cover = common_stock_cover(archived_bytes(sec_root/'statements/raw',ref['sha256'],'.xml.gz'),
            spec['cik'],spec['symbol'],'NASDAQ')
        document = connection.execute(select(FILINGS.c.payload).join(SNAPSHOTS, SNAPSHOTS.c.id==FILINGS.c.snapshot_id).where(
            SNAPSHOTS.c.cik==spec['cik'], SNAPSHOTS.c.first_received_at<=utc_text(cutoff),
            FILINGS.c.accession==receipt['accession']).limit(1)).scalar()
        if (not document or document['primary_document']!=receipt['primary'] or document['form']!='10-K'
                or document['report_date']!=cover['report_end'] or document['filed']>cutoff.date().isoformat()):
            raise ValueError('FILING_CATALOGUE_MISMATCH')
        base['evidence'].append(dict(kind='SEC_COMMON_STOCK_COVER',id=receipt['accession'],sha256=ref['sha256'],
            url=ref['url'],received_at=receipt['received_at'],context_id=cover['context_id'],filed=document['filed']))
        base.update(state='DOCUMENTED',reason='Emisor y acción ordinaria contrastados con el contexto del informe SEC y el catálogo Alpaca fijado. El vínculo no acredita identidad histórica.',
            cik=spec['cik'],instrument_id=fingerprint(['common-stock-pilot-v1',spec['cik'],cover['security_title']]),
            market_listing_id=spec['market_listing_id'],sec_listing_id=spec['sec_listing_id'],security_title=cover['security_title'],
            known_from=max(pilot['reviewed_at'],receipt['received_at']), market_identity_hash=spec['market_identity_hash'],
            provider_asset_id=rows['market']['provider_key'],price_unit='PER_SHARE')
    except (OSError,EOFError,ValueError,KeyError,TypeError):
        base.update(state='REVIEW_REQUIRED',reason='Falta evidencia, ha cambiado la identidad o no coincide la clase del documento. Requiere nueva revisión.')
    base.update(contract_evidence(sec_root.parent/'ibkr/contracts/raw',base,spec,pilot,cutoff,contract_review))
    return base
