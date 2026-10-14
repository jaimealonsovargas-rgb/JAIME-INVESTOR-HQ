"""Ingesta solo de respuestas reales autorizadas; sin seeds ni elegibilidad broker."""
import re
from uuid import uuid5,NAMESPACE_URL,uuid4
from sqlalchemy.orm import Session
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
        elif o.data_kind=='instrument_metadata':
            m=o.metadata;symbol=m.get('ticker') or m.get('symbol');currency=o.currency
            kind=m.get('type') or m.get('instrument_type') or m.get('securityType')
            asset={'STOCK':'EQUITY','Stock':'EQUITY','Common Stock':'EQUITY','ETF':'ETF'}.get(kind)
            if m.get('isEtf')=='True':asset='ETF'
            venue=m.get('mic_code') or m.get('exchange') or m.get('exchCode') or venue
            # No adivinar currency ausente en OpenFIGI ni convertir mapping en ticker inequívoco.
            isin=m.get('isin');figi=m.get('figi');cusip=m.get('cusip')
        if not asset or not symbol or (currency is None and asset not in ('MACRO_SERIES','INDEX')):continue
        identity='|'.join((symbol,venue,currency or '',asset));id=uuid5(NAMESPACE_URL,identity)
        if session.get(InstrumentRecord,str(id)):continue
        country=o.country if o.country and re.fullmatch('[A-Z]{2}',o.country) and o.country!='EU' else None
        item=Instrument(id=id,symbol=symbol,venue=venue,currency=currency,country=country,asset_class=asset,isin=isin,figi=figi,cusip=cusip,source=o.source_ref,verified_at=o.received_at,provider_capabilities=(ProviderCapability(provider=o.provider,feed=o.feed,research=True,valuation=False,internal_paper=False,broker_paper=False,license=o.rights.license,source=o.rights.source,checked_at=o.received_at,reason='Dato de consulta verificado; no demuestra elegibilidad ni ejecución paper.'),))
        session.add(InstrumentRecord(id=str(item.id),symbol=item.symbol,venue=item.venue,currency=item.currency or '',asset_class=item.asset_class,payload=item.model_dump(mode='json')))
        session.flush()
        session.add(InstrumentAlias(id=str(uuid4()),instrument_id=str(item.id),provider=o.provider,symbol=o.series_id,venue=venue,currency=currency or '',source=o.source_ref,verified_at=o.received_at.isoformat(),expires_at=None))
        added+=1
    return added
