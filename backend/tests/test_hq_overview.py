"""TEST_ONLY: no red, cartera ni datos reales en fixtures."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from dataclasses import replace

from sqlalchemy.orm import Session

from app.data_catalog import CATALOG
from app.data_contracts import DataResult
from app.data_parsers import parse
from app.database import DataRecord
from app.data_service import cache_key


def test_overview_master_is_backed_by_ledger_and_future_phases_remain_absent(client):
    response = client.get('/api/hq/overview')
    assert response.status_code == 200
    result = response.json()
    assert result['trading_mode'] == 'PAPER_ONLY' and result['orders_enabled'] is False
    assert len(result['sections']) == 9
    assert all(s['items'] == [] for s in result['sections'])
    assert all(s['status'] == 'NOT_IMPLEMENTED' and s['value'] is None for s in result['sections'] if s['section_id'] not in ('systems', 'portfolio', 'positions'))
    portfolio = next(s for s in result['sections'] if s['section_id']=='portfolio')
    assert portfolio['value']['nav_eur']=='10000.00' and 'Ledger MASTER' in portfolio['source']
    assert client.post('/api/orders', json={'mode': 'LIVE'}).status_code == 403


def test_overview_requires_verified_display_rights_and_labels_stale(client, monkeypatch):
    data = client.app.state.data
    now = datetime(2026, 10, 15, tzinfo=timezone.utc)
    monkeypatch.setattr(data, 'clock', lambda: now)
    raw = b'KEY,TIME_PERIOD,OBS_VALUE,UNIT_MEASURE,UNIT_MULT\nTEST_ONLY,2026-09,1.234567890123456789,index,0\n'
    rows = parse(CATALOG['A01'], raw, now-timedelta(days=3))
    assert rows[0].value == Decimal('1.234567890123456789')
    result = DataResult(access_id='A01', state='AVAILABLE_VERIFIED', reason='TEST_ONLY', real_connection=False, usable=False, observations=rows)
    with Session(data.engine) as session, session.begin():
        record = DataRecord(key=cache_key(CATALOG['A01']), payload=result.model_dump(mode='json'), expires_at=now.isoformat(), updated_at=now.isoformat())
        session.add(record)
    assert all(not s['items'] for s in client.get('/api/hq/overview').json()['sections'])
    with Session(data.engine) as session, session.begin():
        record = session.get(DataRecord, cache_key(CATALOG['A01']))
        record.payload = result.model_copy(update={'real_connection': True}).model_dump(mode='json')
    markets = next(s for s in client.get('/api/hq/overview').json()['sections'] if s['section_id'] == 'markets')
    assert markets['status'] == 'STALE'
    assert markets['items'][0]['value'] == '1.234567890123456789'
    assert markets['items'][0]['execution_eligible'] is False
    fresh=rows[0].model_copy(update={'series_id':'TEST_ONLY_FRESH','received_at':now})
    with Session(data.engine) as session, session.begin():
        record=session.get(DataRecord,cache_key(CATALOG['A01']))
        record.payload=result.model_copy(update={'real_connection':True,'observations':(fresh,*rows)}).model_dump(mode='json')
    mixed=next(s for s in client.get('/api/hq/overview').json()['sections'] if s['section_id']=='markets')
    assert len(mixed['items'])==2 and mixed['status']=='STALE'
    source = CATALOG['A01']
    monkeypatch.setitem(CATALOG, 'A01', replace(source, rights=source.rights.model_copy(update={'display_allowed': False})))
    assert all(not s['items'] for s in client.get('/api/hq/overview').json()['sections'])
