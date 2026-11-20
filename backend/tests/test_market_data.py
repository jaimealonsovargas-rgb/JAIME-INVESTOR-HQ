"""B2.3 acceptance with synthetic replies only; no personal account or network."""
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from sqlalchemy import create_engine, select, update, func
from app.database import Base, DataQuota
from app.data_config import DataSettings
from app.data_service import DataService
from app.data_http import FetchError
from app.market_service import MarketService
from app.market_store import JOBS, RECEIPTS, BARS
from app.universe_store import UniverseStore, LISTINGS
from app.universe_contracts import parse_catalogue
from app.portfolio_store import initialize_master

NOW = datetime(2026, 10, 28, 15, tzinfo=timezone.utc)
ASSET_ID = '00000000-0000-0000-0000-000000000001'


def bar(day, close='12'):
    return dict(t=f'2024-01-{day:02}T05:00:00Z', o='10', h='13', l='9', c=close, v=100, n=10, vw='11')


class Replies:
    real = False

    def __init__(self, clock):
        self.clock, self.calls, self.fail, self.symbol = clock, [], {}, 'TEST'
        self.repeat_token = False

    def fetch(self, kind, params=None):
        self.calls.append((kind, dict(params or {})))
        if kind in self.fail:
            raise self.fail[kind]
        now = self.clock[0]
        values = {
            'assets': [dict(id=ASSET_ID, symbol=self.symbol, name='SYNTHETIC TEST ONLY', exchange='NYSE',
                status='active', tradable=True, **{'class': 'us_equity'})],
            'clock': dict(timestamp=now.isoformat(), is_open=True,
                next_open=(now+timedelta(days=1)).isoformat(), next_close=(now+timedelta(hours=5)).isoformat()),
            'calendar': [dict(date=f'2024-01-{day:02}', open='09:30', close='16:00') for day in range(2, 6)],
            'snapshot': dict(latestTrade=dict(t=now.isoformat(), p='12.25', s=1, x='V'),
                latestQuote=dict(t=now.isoformat(), bp='12.2', ap='12.3', bs=1, **{'as': 2})),
            'account': dict(id='DO_NOT_STORE_ACCOUNT_IDENTIFIER', status='ACTIVE', currency='USD',
                cash='400', equity='420', buying_power='800', portfolio_value='420', trading_blocked=False, account_blocked=False),
            'positions': [],
            'corporate_actions': dict(corporate_actions={}, next_page_token=None),
        }
        if kind == 'bars':
            values['bars'] = dict(symbol=self.symbol, bars=[bar(4), bar(5)] if params.get('page_token') else [bar(2), bar(3)],
                next_page_token='next-page' if not params.get('page_token') or self.repeat_token else None)
        return json.dumps(values[kind]).encode()


@pytest.fixture
def market(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path/'market.db'))
    Base.metadata.create_all(engine)
    initialize_master(engine)
    clock = [NOW]
    settings = DataSettings(_env_file=None, alpaca_api_key='TEST_KEY', alpaca_secret_key='TEST_SECRET')
    data = DataService(engine, settings, clock=lambda: clock[0])
    service = MarketService(data, Replies(clock), tmp_path/'raw')
    service.test_clock = clock
    yield service
    engine.dispose()


def drain(s, key):
    for _ in range(30):
        if s.store.job(key)['state'] not in ('QUEUED', 'RUNNING', 'WAITING'):
            return s.store.job(key)
        s.step()
        s.test_clock[0] += timedelta(seconds=10)
    raise AssertionError('Worker did not finish bounded import')


def catalogue(s, key='catalogue-test'):
    s.enqueue(key, dict(kind='catalogue'))
    assert drain(s, key)['state'] == 'SUCCEEDED'
    return UniverseStore(s.data.engine).search(provider='ALPACA')['items'][0]['id']


def history(s, ident, key='history-test', adjustment='raw'):
    return s.enqueue(key, dict(kind='history', listing_id=ident, start='2024-01-02', end='2024-01-05', adjustment=adjustment))


def protected(engine):
    with engine.connect() as c:
        return {name: [dict(r) for r in c.execute(select(table)).mappings()]
            for name, table in Base.metadata.tables.items() if not name.startswith(('market_', 'universe_', 'data_quotas'))}


def test_catalogue_prices_history_and_paper_never_write_master(market):
    before = protected(market.data.engine)
    ident = catalogue(market)
    market.enqueue('connection-test', dict(kind='connection'))
    assert drain(market, 'connection-test')['state'] == 'SUCCEEDED'
    summary = market.summary()
    assert summary['paper']['account']['cash'] == '400'
    assert summary['paper']['positions_complete'] is True
    assert 'DO_NOT_STORE' not in json.dumps(summary)
    assert not list(market.raw_root.rglob('*account*'))
    market.enqueue('snapshot-test', dict(kind='snapshot', listing_id=ident))
    drain(market, 'snapshot-test')
    detail = market.detail(ident)
    assert detail['quote']['price'] == '12.25' and detail['identity']['issuer_link'] == 'UNCONFIRMED'
    assert detail['identity']['currency'] == 'USD'
    history(market, ident)
    assert drain(market, 'history-test')['state'] == 'SUCCEEDED'
    detail = market.detail(ident)
    assert len(detail['history']['series']) == 4
    assert detail['history']['manifest']['missing_sessions'] == 0
    assert detail['backtest_ready'] is False and detail['execution_ready'] is False
    assert protected(market.data.engine) == before


def test_missing_keys_are_not_access_and_no_request_is_sent(market):
    market.data.settings = DataSettings(_env_file=None, alpaca_api_key=None, alpaca_secret_key=None)
    summary = market.summary()
    assert summary['source']['state'] == 'NO_CREDENTIALS'
    assert all(e['state'] == 'NO_CREDENTIALS' for e in summary['endpoints'])
    with pytest.raises(ValueError, match='NO_CREDENTIALS'):
        market.enqueue('no-creds', dict(kind='connection'))
    assert market.step() is False and market.http.calls == []


def test_sec_candidates_do_not_inherit_market_prices(market):
    ident = catalogue(market)
    store = UniverseStore(market.data.engine)
    store.claim('sec-fixture', 'SEC', NOW)
    rows = parse_catalogue('SEC', dict(fields=['cik','name','ticker','exchange'], data=[[1,'OTHER ISSUER','TEST','NYSE']]))
    store.apply_snapshot('sec-fixture', 'SEC', rows, 'https://www.sec.gov/files/company_tickers_exchange.json', 'a'*64, NOW)
    sec = store.search(provider='SEC')['items'][0]['id']
    detail = market.detail(sec)
    assert detail['identity']['candidates'][0]['id'] == ident
    assert detail['quote']['state'] == 'BLOCKED' and detail['quote']['price'] is None
    with pytest.raises(ValueError, match='ALPACA_IDENTITY_REQUIRED'):
        market.enqueue('wrong-link', dict(kind='snapshot', listing_id=sec))


def test_pagination_short_page_recovery_and_temporal_cutoff(market):
    ident = catalogue(market)
    history(market, ident)
    market.step()  # calendar
    market.test_clock[0] += timedelta(seconds=2)
    market.step()  # short first page still has a token
    partial_time = market.test_clock[0]
    assert market.history(ident, 'raw', partial_time)['manifest'] is None
    recovered = MarketService(market.data, market.http, market.raw_root)
    recovered.test_clock = market.test_clock
    recovered.test_clock[0] += timedelta(seconds=2)
    assert drain(recovered, 'history-test')['state'] == 'SUCCEEDED'
    assert recovered.history(ident, 'raw', partial_time)['manifest'] is None
    assert recovered.detail(ident)['history']['manifest']['bars'] == 4
    assert len([call for call in market.http.calls if call[0] == 'bars']) == 2


def test_repeated_page_token_cannot_publish_partial_series(market):
    ident = catalogue(market)
    market.http.repeat_token = True
    history(market, ident)
    assert drain(market, 'history-test')['state'] == 'FAILED'
    assert market.detail(ident)['history']['manifest'] is None
    with market.data.engine.connect() as c:
        assert c.execute(select(func.count()).select_from(BARS)).scalar_one() == 2


def test_raw_and_adjusted_series_are_separate_and_missing_calendar_unknown(market):
    ident = catalogue(market)
    history(market, ident)
    drain(market, 'history-test')
    market.http.fail['calendar'] = FetchError('RIGHTS_RESTRICTED', 403)
    market.http.fail['corporate_actions'] = FetchError('RIGHTS_RESTRICTED', 403)
    history(market, ident, 'adjusted-test', 'all')
    assert drain(market, 'adjusted-test')['state'] == 'PARTIAL'
    adjusted = market.detail(ident, 'all')['history']['manifest']
    assert adjusted['expected_sessions'] is None and adjusted['corporate_actions_state'] == 'NOT_VERIFIED'
    assert market.detail(ident, 'raw')['history']['manifest']['id'] == 'history-test'
    assert adjusted['id'] == 'adjusted-test'


def test_renamed_asset_does_not_receive_prices_from_old_symbol(market):
    ident = catalogue(market)
    market.enqueue('snapshot-test', dict(kind='snapshot', listing_id=ident))
    drain(market, 'snapshot-test')
    history(market, ident)
    drain(market, 'history-test')
    assert market.detail(ident)['quote']['price'] == '12.25'
    market.http.symbol = 'RENAMED'
    assert catalogue(market, 'renamed-catalogue') == ident
    detail = market.detail(ident)
    assert detail['identity']['symbol'] == 'RENAMED'
    assert detail['quote']['price'] is None and detail['history']['manifest'] is None


def test_cancel_and_expired_lease_fence_late_worker(market):
    market.enqueue('lease-test', dict(kind='connection'))
    first = market.store.claim(NOW)
    market.test_clock[0] += timedelta(minutes=3)
    second = market.store.claim(market.test_clock[0])
    assert first['token'] != second['token']
    assert market.store.accept(first, 'clock', {}, 'a'*64, 'https://paper-api.alpaca.markets/v2/clock', {}, NOW, market.test_clock[0]) is False
    market.store.control('lease-test', 'cancel', market.test_clock[0])
    assert market.store.accept(second, 'clock', {}, 'a'*64, 'https://paper-api.alpaca.markets/v2/clock', {}, NOW, market.test_clock[0]) is False
    with market.data.engine.connect() as c:
        assert c.execute(select(func.count()).select_from(RECEIPTS)).scalar_one() == 0


def test_idempotency_conflict_and_single_active_job(market):
    request = dict(kind='connection')
    first = market.enqueue('same-key', request)
    assert market.enqueue('same-key', request) == first
    with pytest.raises(ValueError, match='IDEMPOTENCY_CONFLICT'):
        market.enqueue('same-key', dict(kind='catalogue'))
    with pytest.raises(ValueError, match='IMPORT_ALREADY_ACTIVE'):
        market.enqueue('other-key', request)


def test_freshness_uses_exchange_time_and_clock_expires(market):
    ident = catalogue(market)
    market.enqueue('snapshot-test', dict(kind='snapshot', listing_id=ident))
    drain(market, 'snapshot-test')
    quote = market.detail(ident)['quote']
    assert quote['state'] == 'AVAILABLE' and quote['market_state'] == 'OPEN'
    market.test_clock[0] += timedelta(minutes=10)
    older = market.detail(ident)['quote']
    assert older['state'] == 'STALE' and older['market_state'] == 'UNKNOWN'
    assert older['as_of'] == quote['as_of'] and older['received_at'] == quote['received_at']
    assert older['bid'] is None


def test_account_refresh_does_not_claim_missing_positions_are_empty(market):
    market.enqueue('connection-first', dict(kind='connection'))
    drain(market, 'connection-first')
    market.http.fail['positions'] = FetchError('RIGHTS_RESTRICTED', 403)
    market.enqueue('connection-second', dict(kind='connection'))
    drain(market, 'connection-second')
    assert market.summary()['paper']['positions_complete'] is False


def test_http_routes_require_local_origin_and_known_scope(client):
    assert client.get('/api/universe/market/summary').status_code == 200
    headers = {'X-HQ-Universe':'1', 'Idempotency-Key':'http-request'}
    endpoint = '/api/universe/market/jobs'
    assert client.post(endpoint, json={'kind':'connection'}).status_code == 403
    assert client.post(endpoint, headers={**headers, 'Origin':'https://evil.example'}, json={'kind':'connection'}).status_code == 403
    assert client.post(endpoint, headers=headers, json={'kind':'connection','url':'https://api.alpaca.markets/v2/orders'}).status_code == 422
    assert client.post(endpoint, headers=headers, json={'kind':'history','listing_id':'a'*64,'start':'2024-02-31','end':'2024-03-01'}).status_code == 422
    assert client.post('/api/orders', json={}).status_code == 403


def test_storage_budget_is_reported_without_publishing_data(market, monkeypatch):
    import app.market_service as module
    def full(*args):
        raise ValueError('LOCAL_STORAGE_LIMIT')
    monkeypatch.setattr(module, 'archive_raw', full)
    market.enqueue('storage-test', dict(kind='catalogue'))
    result = drain(market, 'storage-test')
    assert result['state'] == 'FAILED' and result['reason'] == 'LOCAL_STORAGE_LIMIT'
    assert market.summary()['counts']['assets'] == 0
