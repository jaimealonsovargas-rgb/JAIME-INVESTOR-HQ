"""Historical audit probe. Fixtures only, SQLite in memory, no network or personal DB.
Run from repository: .venv/Scripts/python.exe docs/actual/evidencias/probe_data_integrity.py
Output documents behavior; defects should disappear after B1. No writes to repository.
"""
import sys
sys.dont_write_bytecode = True
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'backend'))
from app.data_catalog import CATALOG
from app.data_parsers import parse
from app.research_planning import role_evidence_gap
from app.data_history import archive, read_source
from app.data_service import cache_key
from types import SimpleNamespace
from app.data_registry import ingest
from app.database import Base, DataObservation, InstrumentAlias
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Synthetic SEC observation collision: same period, two legitimate filings.
fixture = {'cik': 320193, 'facts': {'us-gaap': {'Assets': {'label': 'TEST_ONLY', 'units': {'USD': [
    {'end':'2025-09-30','val':100,'filed':'2025-10-30','form':'10-K','accn':'TEST-1'},
    {'end':'2025-09-30','val':110,'filed':'2026-01-30','form':'10-Q','accn':'TEST-2'}
]}}}}}
observations = parse(CATALOG['A09'], json.dumps(fixture).encode(), datetime(2026,10,27,tzinfo=timezone.utc))
fundamental_gap = role_evidence_gap('fundamental_equity', [{'scope':'INSTRUMENT','rights_ok':True,'available':True,'freshness':'FRESH','content':observations[0].model_dump(mode='json')}])
engine = create_engine('sqlite://')
Base.metadata.create_all(engine)
with Session(engine) as session, session.begin():
    archive(session, CATALOG['A09'], 'TEST_ONLY', observations)
with Session(engine) as session:
    archived_sec = list(session.scalars(select(DataObservation)))
    sec_retained = len(archived_sec)
now = datetime(2026,10,27,tzinfo=timezone.utc)
prototype = observations[0].model_copy(update={'data_kind':'instrument_metadata','value':None,'period':'2026-10-27','observed_at':now,'series_id':'TEST','venue':'TEST_EXCHANGE','metadata':{'ticker':'TEST','type':'STOCK','exchange':'TEST_EXCHANGE'}})
first = prototype.model_copy(update={'provider':'TEST_PROVIDER_A'})
second = prototype.model_copy(update={'provider':'TEST_PROVIDER_B'})
with Session(engine) as session, session.begin():
    ingest(session,[first]); ingest(session,[second])
with Session(engine) as session:
    alias_providers = [a.provider for a in session.scalars(select(InstrumentAlias))]
history_fixture = [{'timestamp':(now-timedelta(days=i+1)).isoformat(),'price':'1'} for i in range(60)]
series_v1 = parse(CATALOG['A21'],json.dumps(history_fixture).encode(),now)
history_fixture[0]['price']='1.1'
series_v2 = parse(CATALOG['A21'],json.dumps(history_fixture).encode(),now+timedelta(minutes=1))
with Session(engine) as session, session.begin():
    archive(session,CATALOG['A21'],cache_key(CATALOG['A21']),series_v1)
    archive(session,CATALOG['A21'],cache_key(CATALOG['A21']),series_v2)
with Session(engine) as session:
    read_rows = read_source(session,SimpleNamespace(initial=lambda s:SimpleNamespace(state='NOT_VERIFIED')),CATALOG['A21'],limit=60,local_research=True)
history_probe = {'input_unique_days':60,'only_one_price_revised':True,'returned_rows':len(read_rows),'returned_unique_days':len(set(o.observed_at for o in read_rows))}
engine.dispose()
result = {
 'kind': 'SYNTHETIC_FIXTURES_NO_NETWORK_NO_PERSONAL_DB',
 'sec': {'input_revisions':len(observations),'unique_ids':len(set(o.id for o in observations)), 'archived_rows':sec_retained, 'fundamental_gate':fundamental_gap},
 'aliases': {'input_providers':2,'retained_providers':alias_providers},
 'history':history_probe
}
print(json.dumps(result,ensure_ascii=False,indent=2))
