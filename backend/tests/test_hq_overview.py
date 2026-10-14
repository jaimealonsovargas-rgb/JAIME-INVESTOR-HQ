"""TEST_ONLY: no red, cartera ni datos reales en fixtures."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from dataclasses import replace

from sqlalchemy.orm import Session

from app.data_catalog import CATALOG
from app.data_contracts import DataResult
from app.data_parsers import parse
from app.database import DataRecord


def test_overview_absence_is_not_zero_or_initial_funds(client):
    response = client.get('/api/hq/overview')
    assert response.status_code == 200
    result = response.json()
    assert result['trading_mode'] == 'PAPER_ONLY' and result['orders_enabled'] is False
    assert len(result['sections']) == 7
    assert all(s['value'] is None and s['items'] == [] for s in result['sections'])
    assert all(s['status'] == 'NOT_IMPLEMENTED' for s in result['sections'])
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
        record = DataRecord(key='cache:TEST_ONLY', payload=result.model_dump(mode='json'), expires_at=now.isoformat(), updated_at=now.isoformat())
        session.add(record)
    assert all(not s['items'] for s in client.get('/api/hq/overview').json()['sections'])
    with Session(data.engine) as session, session.begin():
        record = session.get(DataRecord, 'cache:TEST_ONLY')
        record.payload = result.model_copy(update={'real_connection': True}).model_dump(mode='json')
    markets = next(s for s in client.get('/api/hq/overview').json()['sections'] if s['section_id'] == 'markets')
    assert markets['status'] == 'STALE'
    assert markets['items'][0]['value'] == '1.234567890123456789'
    assert markets['items'][0]['execution_eligible'] is False
    source = CATALOG['A01']
    monkeypatch.setitem(CATALOG, 'A01', replace(source, rights=source.rights.model_copy(update={'display_allowed': False})))
    assert all(not s['items'] for s in client.get('/api/hq/overview').json()['sections'])
