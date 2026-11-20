"""B1 regression fixtures. No external data or writes to the personal database."""
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.database import Base, DataObservation, InstrumentAlias, InstrumentRecord
from app.data_catalog import CATALOG
from app.data_parsers import parse
from app.data_history import archive, read_source
from app.data_registry import ingest
from app.data_service import cache_key
from app.research_planning import role_evidence_gap
from app.database import DataDownload

NOW = datetime(2026, 10, 27, tzinfo=timezone.utc)
DATA = SimpleNamespace(initial=lambda _: SimpleNamespace(state='NOT_VERIFIED'))


def engine():
    result = create_engine('sqlite://')
    Base.metadata.create_all(result)
    return result


def sec(rows):
    raw = {'cik': 1, 'facts': {'us-gaap': {'Assets': {'units': {'USD': rows}}}}}
    return parse(CATALOG['A09'], json.dumps(raw).encode(), NOW)


def test_sec_same_period_distinct_filings_survive():
    rows = sec([{'end': '2025-12-31', 'val': 100, 'accn': 'TEST-1', 'filed': '2026-02-01', 'form': '10-K'},
                {'end': '2025-12-31', 'val': 110, 'accn': 'TEST-2', 'filed': '2026-03-01', 'form': '10-K/A'}])
    assert len({o.id for o in rows}) == 2
    with Session(engine()) as s, s.begin():
        archive(s, CATALOG['A09'], cache_key(CATALOG['A09']), rows)
        assert len(list(s.scalars(select(DataObservation)))) == 2


def test_history_window_is_sixty_dates_after_one_revision():
    source = CATALOG['A21']
    raw = [{'timestamp': (NOW-timedelta(days=i+1)).isoformat(), 'price': '1'} for i in range(60)]
    first = parse(source, json.dumps(raw).encode(), NOW)
    raw[0]['price'] = '1.1'
    second = parse(source, json.dumps(raw).encode(), NOW+timedelta(minutes=1))
    with Session(engine()) as s, s.begin():
        archive(s, source, cache_key(source), first)
        archive(s, source, cache_key(source), second)
        archive(s, source, cache_key(source), second)
        rows = read_source(s, DATA, source, limit=60, local_research=True)
        assert len({o.observed_at for o in rows}) == 60
        assert len(list(s.scalars(select(DataObservation)))) == 61
        assert str(rows[0].value) == '1.1'


def test_aliases_survive_second_provider_and_idempotent_redownload():
    base = sec([{'end': '2025-12-31', 'val': 1, 'accn': 'TEST', 'filed': '2026-02-01'}])[0]
    base = base.model_copy(update={'data_kind': 'instrument_metadata', 'value': None,
        'series_id': 'TEST', 'metadata': {'ticker': 'TEST', 'type': 'STOCK', 'exchange': 'XTEST'},
        'provider': 'TEST_A'})
    other = base.model_copy(update={'provider': 'TEST_B'})
    with Session(engine()) as s, s.begin():
        ingest(s, [base, other, base])
        assert len(list(s.scalars(select(InstrumentRecord)))) == 1
        assert {a.provider for a in s.scalars(select(InstrumentAlias))} == {'TEST_A', 'TEST_B'}
        ingest(s, [base.model_copy(update={'currency': 'EUR'})])
        assert len(list(s.scalars(select(InstrumentRecord)))) == 2


def test_as_of_preserves_first_receipt_and_excludes_future_revision():
    source=CATALOG['A21']
    def observations(value,when):
        return parse(source,json.dumps([{'timestamp':'2026-10-20T00:00:00Z','price':value}]).encode(),when)
    first=observations('1',NOW)
    second=observations('2',NOW+timedelta(hours=1))
    redownload=observations('1',NOW+timedelta(hours=2))
    with Session(engine()) as s,s.begin():
        for rows in (first,second,redownload):archive(s,source,cache_key(source),rows)
        assert read_source(s,DATA,source,as_of=NOW-timedelta(seconds=1),local_research=True)==[]
        assert read_source(s,DATA,source,as_of=NOW,local_research=True)[0].value==1
        assert read_source(s,DATA,source,as_of=NOW+timedelta(hours=1),local_research=True)[0].value==2
        assert read_source(s,DATA,source,local_research=True)[0].value==1
        assert len(list(s.scalars(select(DataObservation))))==2
        assert len(list(s.scalars(select(DataDownload))))==3
        assert s.get(DataObservation,first[0].id).received_at==NOW.isoformat()


def test_legacy_duplicate_ids_are_deduplicated_without_rewriting_storage():
    source=CATALOG['A21']
    obs=parse(source,b'[{"timestamp":"2026-10-20T00:00:00Z","price":"1"}]',NOW)[0]
    with Session(engine()) as s,s.begin():
        for i in range(2):
            legacy=obs.model_dump(mode='json');legacy.pop('observation_key');legacy.pop('identity_version')
            legacy.update(id=str(i)*64,received_at=(NOW+timedelta(minutes=i)).isoformat())
            s.add(DataObservation(id=legacy['id'],access_id=source.id,source_identity=cache_key(source),
                observed_at=legacy['observed_at'],received_at=legacy['received_at'],payload=legacy))
        assert len(read_source(s,DATA,source,local_research=True))==1
        assert len(list(s.scalars(select(DataObservation))))==2


def annual_bundle():
    facts={}
    for concept,value in [('Assets',100),('StockholdersEquity',60),('Revenues',150),('NetIncomeLoss',15)]:
        row={'end':'2025-12-31','val':value,'accn':'TEST-ANNUAL','filed':'2026-02-01','form':'10-K'}
        if concept in ('Revenues','NetIncomeLoss'):row['start']='2025-01-01'
        facts[concept]={'units':{'USD':[row]}}
    return parse(CATALOG['A09'],json.dumps({'cik':1,'facts':{'us-gaap':facts}}).encode(),NOW)


def test_fundamental_contract_rejects_mixed_issuer_period_and_missing_concepts():
    evidence=[{'scope':'INSTRUMENT','rights_ok':True,'freshness':'FRESH','content':o.model_dump(mode='json')} for o in annual_bundle()]
    assert role_evidence_gap('fundamental_equity',evidence) is None
    assert role_evidence_gap('fundamental_equity',evidence[:1])
    assert role_evidence_gap('valuation',evidence)  # facts alone are not a model
    for field,value in [('cik','0000000002'),('start','2025-10-01'),('accn','OTHER')]:
        import copy
        broken=copy.deepcopy(evidence);broken[-1]['content']['metadata'][field]=value
        assert role_evidence_gap('fundamental_equity',broken)


def test_sec_publication_and_retrieval_order_are_distinct():
    source=CATALOG['A09']
    old=sec([{'end':'2025-12-31','val':100,'accn':'OLD','filed':'2026-02-01','form':'10-K'}])[0]
    revised=sec([{'end':'2025-12-31','val':110,'accn':'NEW','filed':'2026-03-01','form':'10-K/A'}])[0]
    with Session(engine()) as s,s.begin():
        archive(s,source,cache_key(source),[old,revised])
        archive(s,source,cache_key(source),[old.model_copy(update={'received_at':NOW+timedelta(hours=1)})])
        assert read_source(s,DATA,source)[0].value==110
        assert old.published_at.date().isoformat()=='2026-02-02'
        assert len(read_source(s,DATA,source,revisions=True))==2


def test_sec_date_only_publication_waits_for_eastern_day_end():
    source = CATALOG['A09']
    for filed in ('2026-02-01', '2026-07-01'):
        received = datetime.fromisoformat(filed).replace(tzinfo=timezone.utc) + timedelta(days=1)
        raw = {'cik': 1, 'facts': {'us-gaap': {'Assets': {'units': {'USD': [
            {'end': '2025-12-31', 'val': 100, 'accn': 'TEST-BOUND', 'filed': filed, 'form': '10-K'}]}}}}}
        rows = parse(source, json.dumps(raw).encode(), received)
        with Session(engine()) as s, s.begin():
            archive(s, source, cache_key(source), rows)
            assert read_source(s, DATA, source, as_of=received + timedelta(hours=4, minutes=59)) == []
            assert len(read_source(s, DATA, source, as_of=received + timedelta(hours=5))) == 1


def test_fundamental_identity_and_publication_survive_model_compaction():
    from app.research_planning import evidence_pack
    from app.local_llm import model_view
    observations = annual_bundle()
    evidence = [{'id': o.id, 'hash': o.payload_hash, 'content': o.model_dump(mode='json'),
                 'scope': 'INSTRUMENT', 'source': o.feed, 'provider': o.provider,
                 'observed_at': o.observed_at.isoformat(), 'rights': {},
                 'rights_ok': True, 'freshness': 'FRESH'} for o in observations]
    pack = model_view(evidence_pack(evidence))
    assert len(pack['sources']) == 4
    for row, obs in zip(pack['records'], observations):
        source = pack['sources'][row['source_id']]
        assert source['statement']['cik'] == '0000000001'
        assert source['statement']['concept'] == obs.metadata['concept']
        assert source['statement']['accn'] == 'TEST-ANNUAL'
        assert source['statement']['start'] == obs.metadata.get('start')
        assert source['statement']['publication_precision'] == 'day_upper_bound'
        assert row['published_at'] == obs.model_dump(mode='json')['published_at']


def test_verified_issuer_mapping_connects_sec_to_correct_instrument(migrated):
    from app.database import create_db_engine
    from app.research_evidence import collect
    db=create_db_engine(migrated.database_url)
    source=CATALOG['A09'];rows=annual_bundle()
    meta=rows[0].model_copy(update={'data_kind':'instrument_metadata','value':None,'provider':'TEST_PROVIDER',
        'series_id':'TEST','metadata':{'ticker':'TEST','type':'STOCK','exchange':'XTEST','cik':'1'}})
    with Session(db) as s,s.begin():
        ingest(s,[meta]);archive(s,source,cache_key(source),rows)
        item=s.scalar(select(InstrumentRecord)).payload
    data=SimpleNamespace(engine=db,initial=DATA.initial,clock=lambda:NOW)
    evidence=collect(data,{'id':'TEST-CASE','instrument':item})
    assert len([e for e in evidence if e['scope']=='INSTRUMENT'])==4
    assert role_evidence_gap('fundamental_equity',evidence) is None
    wrong=collect(data,{'id':'OTHER','instrument':{**item,'issuer_cik':'0000000002'}})
    assert not any(e['scope']=='INSTRUMENT' for e in wrong)
