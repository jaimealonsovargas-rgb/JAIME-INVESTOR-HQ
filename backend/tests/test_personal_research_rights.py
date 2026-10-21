"""TEST_ONLY data in temporary DB; not real observations or API verification."""
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.data_catalog import CATALOG
from app.data_history import archive, read_source
from app.data_parsers import parse
from app.data_rights import readable
from app.data_service import cache_key
from app.market_history import market_status
from app.portfolio_valuation import permitted
from test_data_history_refresh import setup

NOW = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)


def test_personal_ai_is_not_redistribution_or_master_valuation():
    rights = CATALOG['A21'].rights
    assert not readable(rights) and readable(rights, local_research=True)
    assert not rights.redistribution_allowed
    assert not readable(rights.model_copy(update={'local_research_allowed': False}), local_research=True)
    assert not readable(rights.model_copy(update={'scope': 'restricted'}), local_research=True)
    assert not readable(CATALOG['A18'].rights, local_research=True)


def test_daily_history_does_not_fabricate_candles_or_include_today(migrated):
    data = setup(migrated); source = CATALOG['A21']
    raw = json.dumps([{'timestamp': '2026-10-19T00:00:00Z', 'price': '1.23456789'},
                      {'timestamp': '2026-10-20T00:00:00Z', 'price': '9.99'}]).encode()
    observations = parse(source, raw, NOW)
    assert len(observations) == 1
    obs = observations[0]
    assert obs.period_precision == 'day' and str(obs.value) == '1.23456789'
    assert 'HISTORICAL_DAILY_SNAPSHOT' in obs.quality_flags
    assert 'HISTORICAL_EOD' not in obs.quality_flags
    assert not permitted(obs)  # Display/research cannot grant P3 valuation permission.
    assert market_status(obs, NOW) == 'FRESH'
    with Session(data.engine) as s, s.begin():
        archive(s, source, cache_key(source), observations)
    with Session(data.engine) as s:
        assert read_source(s, data, source) == []
        assert len(read_source(s, data, source, local_research=True)) == 1


def test_spot_tolerance_matches_published_free_update_cadence():
    source = CATALOG['A15']
    raw = json.dumps({'last_updated': '2026-10-20T11:52:00Z',
        'quotes': {'USD': {'price': '1'}}, 'id': 'TEST_ONLY', 'name': 'TEST_ONLY', 'symbol': 'TEST_ONLY'}).encode()
    obs = parse(source, raw, NOW)[0]
    assert source.ttl == 900 and not obs.stale(NOW)
    assert obs.stale(NOW.replace(hour=13))


def test_context_cannot_displace_instrument_history():
    from app.research_evidence import bounded_evidence
    context = [{'id': f'TEST_CONTEXT_{i}', 'scope': 'MACRO_CONTEXT', 'observed_at': f'2026-10-{i+1:02d}'} for i in range(20)]
    direct = [{'id': f'TEST_DIRECT_{i}', 'scope': 'INSTRUMENT', 'observed_at': f'2026-09-{i+1:02d}'} for i in range(30)]
    selected = bounded_evidence(context + direct)
    assert [e for e in selected if e['scope'] == 'INSTRUMENT'] == direct
    assert len(selected) == 38
    assert selected[-8]['observed_at'] == '2026-10-20'
    spots = [{'id': f'TEST_SPOT_{i}', 'scope': 'INSTRUMENT', 'freshness': 'STALE',
              'observed_at': f'2026-10-20T01:{i:02d}:00Z', 'content': {'feed': 'SPOT'}} for i in range(60)]
    history = [{**e, 'freshness': 'FRESH', 'content': {'feed': 'DAILY'}} for e in direct]
    selected = bounded_evidence(context + spots + history)
    assert len([e for e in selected if e.get('content', {}).get('feed') == 'DAILY']) == 30
    assert len([e for e in selected if e.get('content', {}).get('feed') == 'SPOT']) == 2
