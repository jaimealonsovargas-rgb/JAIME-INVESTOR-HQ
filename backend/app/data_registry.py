"""Ingesta solo de respuestas reales autorizadas; sin seeds ni elegibilidad broker."""
import re
from uuid import uuid5,NAMESPACE_URL,uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import zse
from app.contracts import Instrument, ProviderCapability
from app.database import InstrumentRecord, InstrumentAlias

def ingest(session:Session, observations):
    added=0
    for o in observations:
        if not o.rights.storage_allowed or not o.rights.display_allowed:continue
        asset=currency=symbol=isin=figi=cusip=None
        venue=o.venue
        if o.data_kind in ('macro_series','yield_curve'):
            asset='MACRO_SERIES';symbol=o.series_id;venue=o.provider;currency=o.currency
        elif o.data_kind=='fx_reference':
            asset='FX';symbol=o.series_id;venue=o.provider;currency=o.currency
        elif o.data_kind=='market_quote' and o.asset_class=='CRYPTO':
            asset='CRYPTO';symbol=o.series_id;currency=o.currency
        elif (o.access_id, o.provider, o.data_kind, o.asset_class, o.venue, o.series_id,
              o.metadata.get('isin'), o.currency, o.unit) == (
              'A22', 'ZSE', 'market_quote', 'EQUITY', zse.MIC, zse.SYMBOL, zse.ISIN, 'EUR', 'EUR/share'):
            asset, symbol, isin, currency = 'EQUITY', zse.SYMBOL, zse.ISIN, 'EUR'
        elif o.data_kind=='instrument_metadata':
            m=o.metadata;symbol=m.get('ticker') or m.get('symbol');currency=o.currency
            kind=m.get('type') or m.get('instrument_type') or m.get('securityType')
            asset={'STOCK':'EQUITY','Stock':'EQUITY','Common Stock':'EQUITY','ETF':'ETF'}.get(kind)
            if m.get('isEtf')=='True':asset='ETF'
            elif m.get('isEtf')=='False' and o.provider=='FMP':asset='EQUITY'
            venue=m.get('mic_code') or m.get('exchange') or m.get('exchCode') or venue
            # No adivinar currency ausente en OpenFIGI ni convertir mapping en ticker inequívoco.
            isin=m.get('isin');figi=m.get('figi');cusip=m.get('cusip')
        if not asset or not symbol or (currency is None and asset not in ('MACRO_SERIES','INDEX')):continue
        identity='|'.join((symbol,venue,currency or '',asset));id=uuid5(NAMESPACE_URL,identity)
        existing=session.get(InstrumentRecord,str(id))
        country=o.country if o.country and re.fullmatch('[A-Z]{2}',o.country) and o.country!='EU' else None
        item=Instrument(id=id,symbol=symbol,venue=venue,currency=currency,country=country,asset_class=asset,isin=isin,figi=figi,cusip=cusip,source=o.source_ref,verified_at=o.received_at,provider_capabilities=(ProviderCapability(provider=o.provider,feed=o.feed,research=True,valuation=False,internal_paper=False,broker_paper=False,license=o.rights.license,source=o.rights.source,checked_at=o.received_at,reason='Dato de consulta verificado; no demuestra elegibilidad ni ejecución paper.'),))
        cik=o.metadata.get('cik','')
        if o.data_kind=='instrument_metadata' and re.fullmatch(r'\d{1,10}',cik) and int(cik)>0:
            item=item.model_copy(update={'issuer_cik':cik.zfill(10),'issuer_source':o.source_ref})
        if existing is None:
            session.add(InstrumentRecord(id=str(item.id),symbol=item.symbol,venue=item.venue,currency=item.currency or '',asset_class=item.asset_class,payload=item.model_dump(mode='json')))
            added+=1
        else:
            current=Instrument.model_validate(existing.payload)
            capabilities={(c.provider,c.feed):c for c in current.provider_capabilities}
            capabilities.update({(c.provider,c.feed):c for c in item.provider_capabilities})
            update={'provider_capabilities':tuple(capabilities.values())}
            if item.issuer_cik and not current.issuer_cik:
                update.update(issuer_cik=item.issuer_cik,issuer_source=item.issuer_source)
            existing.payload=current.model_copy(update=update).model_dump(mode='json')
        session.flush()
        alias=session.scalar(select(InstrumentAlias).where(InstrumentAlias.provider==o.provider,
            InstrumentAlias.symbol==o.series_id,InstrumentAlias.venue==venue,InstrumentAlias.currency==(currency or '')))
        if alias is None:
            session.add(InstrumentAlias(id=str(uuid4()),instrument_id=str(item.id),provider=o.provider,symbol=o.series_id,venue=venue,currency=currency or '',source=o.source_ref,verified_at=o.received_at.isoformat(),expires_at=None))
        elif alias.instrument_id==str(item.id):
            alias.verified_at=o.received_at.isoformat()
            alias.source=o.source_ref
    return added
