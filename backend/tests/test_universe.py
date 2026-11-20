"""Synthetic catalogue evidence only; external requests disabled by conftest."""
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4
import httpx
import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from app.database import Base, DataQuota, InstrumentRegistry
from app.contracts import Instrument
from app.data_config import DataSettings
from app.data_service import DataService
from app.data_http import FetchError
from app.universe_contracts import parse_catalogue
from app.universe_service import UniverseService, CatalogueHttp, SEC_DIRECTORY
from app.universe_store import ENTITIES, LISTINGS, VERSIONS, IMPORTS

NOW = datetime(2026, 10, 28, tzinfo=timezone.utc)


def payload(rows=None):
    return json.dumps({'fields': ['cik', 'name', 'ticker', 'exchange'], 'data': rows or [
        [1, 'TEST ONLY Holdings', 'TEST.A', 'Nasdaq'], [1, 'TEST ONLY Holdings', 'TEST.B', 'Nasdaq'],
        [2, 'TEST ONLY Company', 'OTHER', 'NYSE']]}).encode()


@pytest.fixture
def service(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'universe.db'))
    Base.metadata.create_all(engine)
    clock = [NOW]
    data = DataService(engine, DataSettings(_env_file=None, sec_contact='TEST_ONLY test@example.invalid'), clock=lambda: clock[0])
    http = SimpleNamespace(fetch_sec=lambda: payload())
    result = UniverseService(data, http)
    result.test_clock = clock
    return result


def test_directory_is_not_instruments_and_import_is_idempotent(service):
    first = service.sync('test-catalogue')
    assert first['state'] == 'SUCCEEDED' and first['entities'] == 2 and first['listings'] == 3
    assert service.sync('test-catalogue') == first
    assert service.store.summary()['counts']['versions'] == 3
    with Session(service.data.engine) as s:
        assert InstrumentRegistry(s).list() == []
        assert s.get(DataQuota, 'SEC').used == 1
    page = service.store.search('TEST', limit=1)
    assert page['total'] == 3 and len(page['items']) == 1 and page['items'][0]['currency'] is None
    detail = service.store.detail(page['items'][0]['id'])
    assert all(x['state'] == 'BLOCKED' for x in detail['readiness'])
    assert 'test@example' not in json.dumps(service.summary())


def test_conflicting_symbol_is_quarantined_without_merging_issuers(service):
    service.http.fetch_sec = lambda: payload([[1, 'TEST ONE', 'SAME', 'NYSE'], [2, 'TEST TWO', 'SAME', 'NYSE'], [3, 'TEST THREE', 'SAME', 'Nasdaq']])
    result = service.sync('test-conflict')
    assert result['conflicts'] == 1
    assert service.store.search(state='CONFLICT')['total'] == 2
    assert service.store.summary()['counts']['entities'] == 3


def test_local_temporal_history_rejects_future_revision_and_preserves_missing(service):
    service.sync('test-first')
    ident = service.store.search('TEST.A')['items'][0]['id']
    service.test_clock[0] += timedelta(minutes=1)
    service.http.fetch_sec = lambda: payload([[1, 'TEST RENAMED', 'TEST.A', 'Nasdaq']])
    service.sync('test-second')
    assert service.store.detail(ident)['name'] == 'TEST RENAMED'
    old = service.store.detail(ident, NOW)
    assert old['name'] == 'TEST ONLY Holdings' and len(old['versions']) == 1
    assert old['versions'][0]['known_until'] is None
    assert service.store.search(state='NOT_OBSERVED')['total'] == 2
    with pytest.raises(KeyError):
        service.store.detail(ident, NOW - timedelta(seconds=1))
    service.test_clock[0] += timedelta(minutes=1)
    service.sync('test-same-again')
    assert len(service.store.detail(ident)['versions']) == 2


def test_same_provider_asset_id_preserves_rename_history(service):
    ident = str(uuid4())
    body = [dict(id=ident, name='TEST ONLY', symbol='BEFORE', exchange='NYSE', status='active', tradable=True, **{'class': 'us_equity'})]
    store = service.store
    store.claim('asset-first', 'ALPACA', NOW)
    store.apply_snapshot('asset-first', 'ALPACA', parse_catalogue('ALPACA', body), 'https://paper-api.alpaca.markets/v2/assets', 'a' * 64, NOW)
    listing = store.search()['items'][0]['id']
    body[0]['symbol'] = 'AFTER'
    store.claim('asset-next', 'ALPACA', NOW + timedelta(days=1))
    store.apply_snapshot('asset-next', 'ALPACA', parse_catalogue('ALPACA', body), 'https://paper-api.alpaca.markets/v2/assets', 'b' * 64, NOW + timedelta(days=1))
    assert store.search()['total'] == 1
    assert store.detail(listing, NOW)['symbol'] == 'BEFORE'
    assert store.detail(listing)['symbol'] == 'AFTER'
    assert store.detail(listing)['currency'] is None


def test_partial_or_invalid_response_never_replaces_previous_catalogue(service):
    service.sync('test-good')
    service.test_clock[0] += timedelta(seconds=2)
    service.http.fetch_sec = lambda: payload([[1, 'VALID', 'VALID', 'NYSE'], ['bad-cik', 'INVALID', 'BAD', 'NYSE']])
    assert service.sync('test-bad')['state'] == 'INVALID_PAYLOAD'
    assert service.store.search()['total'] == 3
    assert service.store.summary()['counts']['versions'] == 3


def test_shared_quota_and_rate_limit_backoff(service):
    with Session(service.data.engine) as s, s.begin():
        s.add(DataQuota(key='SEC', window_start=NOW.isoformat(), used=1, failures=0))
    assert service.sync('quota-one')['state'] == 'SUCCEEDED'
    assert service.sync('quota-two')['state'] == 'RATE_LIMITED'
    service.test_clock[0] += timedelta(seconds=61)
    def limited():
        raise FetchError('RATE_LIMITED', 429, 120)
    service.http.fetch_sec = limited
    assert service.sync('quota-three')['state'] == 'RATE_LIMITED'
    service.test_clock[0] += timedelta(seconds=60)
    assert service.sync('quota-four')['state'] == 'RATE_LIMITED'
    assert service.store.search()['total'] == 3


def test_interrupted_import_lease_recovers_and_concurrent_import_is_coalesced(service):
    claimed, _ = service.store.claim('test-interrupted', 'SEC', NOW)
    assert claimed
    assert service.sync('test-concurrent')['id'] == 'test-interrupted'
    service.test_clock[0] += timedelta(minutes=4)
    assert service.sync('test-interrupted')['state'] == 'SUCCEEDED'
    with pytest.raises(ValueError, match='IDEMPOTENCY_CONFLICT'):
        service.store.claim('test-interrupted', 'ALPACA', service.test_clock[0])


def test_preparation_does_not_expose_or_invent_configuration(service):
    service.data.settings = DataSettings(_env_file=None, sec_contact=None, alpaca_api_key=None, alpaca_secret_key=None)
    assert service.sync('no-contact')['state'] == 'CONFIG_REQUIRED'
    assert service.preparation()[1]['state'] == 'NO_CREDENTIALS'
    service.data.settings = DataSettings(_env_file=None, sec_contact='bad\r\nmail@example.invalid')
    assert service.sync('bad-contact')['state'] == 'CONFIG_REQUIRED'


def test_http_only_fixed_sec_get_no_redirect_and_bounded_body():
    settings = DataSettings(_env_file=None, sec_contact='TEST_ONLY mail@example.invalid')
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(302, headers={'Location': 'https://invalid.example/secret'})
    http = CatalogueHttp(settings, httpx.MockTransport(handler), resolver=lambda _: None)
    with pytest.raises(FetchError):
        http.fetch_sec()
    assert len(requests) == 1 and str(requests[0].url) == SEC_DIRECTORY and requests[0].method == 'GET'
    http.transport = httpx.MockTransport(lambda _: httpx.Response(200, content=b'x' * (16 * 1024 * 1024 + 1)))
    with pytest.raises(FetchError) as error:
        http.fetch_sec()
    assert error.value.state == 'INVALID_PAYLOAD'


def test_search_scales_beyond_one_thousand_and_treats_wildcards_literally(service):
    rows = [[i + 1, f'TEST ONLY {i}', f'S{i:05d}', 'NYSE'] for i in range(1205)]
    rows.append([9000, 'TEST 100%_literal', 'PERCENT', 'NYSE'])
    service.http.fetch_sec = lambda: payload(rows)
    service.sync('test-large')
    page = service.store.search(offset=1200, limit=10)
    assert page['total'] == 1206 and len(page['items']) == 6
    assert service.store.search('%_')['total'] == 1
    assert service.store.search('S01204')['total'] == 1
    with Session(service.data.engine) as s, s.begin():
        item = Instrument(id=uuid4(), symbol='TEST%_', venue='TEST', currency='USD', asset_class='EQUITY')
        InstrumentRegistry(s).add(item)
        assert InstrumentRegistry(s).get(str(item.id)) == item
        assert InstrumentRegistry(s).list('%_') == [item]


def test_api_origin_bounds_and_no_execution(client):
    assert client.get('/api/universe/summary').status_code == 200
    assert client.get('/api/universe/listings?limit=101').status_code == 422
    assert client.get('/api/universe/listings/absent').status_code == 404
    assert client.post('/api/universe/sync', json={'provider': 'SEC'}).status_code == 403
    headers = {'X-HQ-Universe': '1', 'Idempotency-Key': 'test-api', 'Origin': 'https://evil.example'}
    assert client.post('/api/universe/sync', headers=headers, json={'provider': 'SEC'}).status_code == 403
    headers['Origin'] = 'http://127.0.0.1:5173'
    client.app.state.universe.data.settings = DataSettings(_env_file=None, sec_contact=None)
    assert client.post('/api/universe/sync', headers=headers, json={'provider': 'SEC'}).json()['state'] == 'CONFIG_REQUIRED'
    assert client.post('/api/orders').status_code == 403
