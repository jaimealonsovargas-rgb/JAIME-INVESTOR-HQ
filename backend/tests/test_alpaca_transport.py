"""Contract tests use synthetic responses; never imply a verified broker connection."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import httpx
import pytest

from app.alpaca_http import AlpacaHttp, endpoint_url, request_spec
from app.alpaca_normalize import (decimal_text, normalize_account, normalize_bars, normalize_calendar,
    normalize_clock, normalize_corporate_actions, normalize_positions, normalize_snapshot)
from app.data_config import DataSettings
from app.data_http import FetchError

NOW = datetime(2024, 11, 29, 17, 0, tzinfo=timezone.utc)
START, END = '2024-11-25T00:00:00Z', '2024-11-29T23:59:59Z'
ASSET = 'bbac154e-c301-41f5-8d89-3f9518fa7e29'


def settings(**kwargs):
    return DataSettings(_env_file=None, alpaca_api_key='SYNTHETIC_KEY', alpaca_secret_key='SYNTHETIC_SECRET', **kwargs)


def bar(**kwargs):
    return {'t': '2024-11-29T05:00:00Z', 'o': '10', 'h': '12', 'l': '9', 'c': '11', 'v': 1234, 'n': 150, 'vw': '10.7', **kwargs}


def test_decimals_are_bounded_canonical_strings():
    assert decimal_text('1.25E+3') == '1250'
    assert decimal_text('1e-18') == '0.000000000000000001'
    for invalid in ('1e-999999', '0e999999', '1e31', '1' * 129, 'NaN', 'Infinity'):
        with pytest.raises(ValueError):
            decimal_text(invalid)


def test_allowlisted_paper_reads_and_fixed_iex_without_symbol_mapping():
    seen = []
    def respond(request):
        seen.append(request)
        assert request.method == 'GET'
        assert request.headers['APCA-API-KEY-ID'] == 'SYNTHETIC_KEY'
        assert request.headers['APCA-API-SECRET-KEY'] == 'SYNTHETIC_SECRET'
        return httpx.Response(200, json={})
    client = AlpacaHttp(settings(), httpx.MockTransport(respond), resolver=lambda _: None)
    for kind in ('assets', 'clock', 'account', 'positions'):
        assert client.fetch(kind) == b'{}'
        assert seen[-1].url.host == 'paper-api.alpaca.markets'
    client.fetch('snapshot', {'symbol': 'BRK.B'})
    assert seen[-1].url.params['feed'] == 'iex'
    assert seen[-1].url.params['currency'] == 'USD'
    client.fetch('bars', {'symbol': 'TEST', 'start': START, 'end': END, 'adjustment': 'split', 'page_token': 'a+1='})
    params = seen[-1].url.params
    assert params['feed'] == 'iex' and params['asof'] == '-' and params['currency'] == 'USD'
    assert params['page_token'] == 'a+1=' and params['adjustment'] == 'split'
    assert not client.real


@pytest.mark.parametrize('kind,params', [
    ('orders', {}), ('https://api.alpaca.markets/v2/account', {}), ('account', {'url': 'https://evil.test'}),
    ('snapshot', {'symbol': '../orders'}), ('snapshot', {'symbol': 'AAPL?feed=sip'}),
    ('snapshot', {'symbol': 'AAPL', 'feed': 'sip'}), ('positions', []),
    ('bars', {'symbol': 'TEST', 'start': START, 'end': END, 'limit': 1001}),
    ('bars', {'symbol': 'TEST', 'start': START, 'end': END, 'page_token': 'bad\nheader'}),
    ('bars', {'symbol': 'TEST', 'start': START, 'end': END, 'adjustment': 'magic'}),
    ('bars', {'symbol': 'TEST', 'start': '2024-01-01', 'end': END}),
    ('calendar', {'start': '2024-02-30', 'end': '2024-03-01'}),
])
def test_request_cannot_override_host_feed_or_path(kind, params):
    seen = []
    client = AlpacaHttp(settings(), httpx.MockTransport(lambda request: seen.append(request)), resolver=lambda _: None)
    with pytest.raises(FetchError) as error:
        client.fetch(kind, params)
    assert error.value.state == 'CONFIG_REQUIRED' and not seen


@pytest.mark.parametrize('status,state', [(301, 'ERROR'), (401, 'AUTH_FAILED'), (403, 'RIGHTS_RESTRICTED'), (404, 'NOT_FOUND'), (429, 'RATE_LIMITED')])
def test_failures_are_sanitized_and_redirect_never_followed(status, state):
    seen = []
    def respond(request):
        seen.append(request)
        return httpx.Response(status, headers={'Location': 'https://evil.test', 'Retry-After': '120'}, text='secret-account-details')
    client = AlpacaHttp(settings(), httpx.MockTransport(respond), resolver=lambda _: None)
    with pytest.raises(FetchError) as error:
        client.fetch('account')
    assert len(seen) == 1 and error.value.state == state and error.value.retry_after == 120
    assert 'secret-account-details' not in str(error.value)


def test_no_credentials_no_request_and_bounded_decompressed_response(monkeypatch):
    no_keys = DataSettings(_env_file=None, alpaca_api_key=None, alpaca_secret_key=None)
    with pytest.raises(FetchError) as error:
        AlpacaHttp(no_keys).fetch('assets')
    assert error.value.state == 'NO_CREDENTIALS'
    monkeypatch.setattr('app.alpaca_http.MAX_BYTES', 8)
    client = AlpacaHttp(settings(), httpx.MockTransport(lambda _: httpx.Response(200, content=b'x' * 9)), resolver=lambda _: None)
    with pytest.raises(FetchError) as error:
        client.fetch('clock')
    assert error.value.state == 'INVALID_PAYLOAD'


def test_bar_identity_ohlc_unit_and_duplicate_integrity():
    raw = {'symbol': 'TEST', 'bars': [bar(), bar()], 'next_page_token': 'page2'}
    rows, token = normalize_bars(raw, 'TEST', START, END, 'raw')
    assert len(rows) == 1 and token == 'page2'
    assert rows[0]['currency'] == 'USD' and rows[0]['feed'] == 'iex' and rows[0]['adjustment'] == 'raw'
    assert rows[0]['close'] == '11' and rows[0]['volume'] == '1234'
    raw['bars'][1]['c'] = '10'
    with pytest.raises(ValueError, match='CONFLICT'):
        normalize_bars(raw, 'TEST', START, END, 'raw')
    with pytest.raises(ValueError, match='IDENTITY'):
        normalize_bars({'symbol': 'OTHER', 'bars': []}, 'TEST', START, END, 'raw')


@pytest.mark.parametrize('changes', [{'c': 'NaN'}, {'h': 'Infinity'}, {'v': -1}, {'n': True}, {'o': 0}, {'l': 11}, {'t': '2024-11-30T05:00:00Z'}, {'t': '2024-11-29T05:00:00'}])
def test_reject_impossible_or_out_of_window_bars(changes):
    with pytest.raises(ValueError):
        normalize_bars({'symbol': 'TEST', 'bars': [bar(**changes)]}, 'TEST', START, END, 'raw')


def test_empty_bars_and_token_validation():
    assert normalize_bars({'symbol': 'TEST', 'bars': None, 'next_page_token': None}, 'TEST', START, END, 'all') == ([], None)
    with pytest.raises(ValueError):
        normalize_bars({'symbol': 'TEST', 'bars': [], 'next_page_token': 'x\n'}, 'TEST', START, END, 'all')


def test_snapshot_marks_stale_and_suppresses_crossed_or_one_sided_quote():
    raw = {'latestTrade': {'t': '2024-11-29T16:00:00Z', 'p': '10.123456789', 's': 5, 'x': 'V'},
           'latestQuote': {'t': '2024-11-29T16:59:00Z', 'bp': 12, 'ap': 11, 'bs': 4, 'as': 5},
           'dailyBar': bar(), 'prevDailyBar': None}
    value = normalize_snapshot(raw, 'TEST', NOW)
    assert value['trade']['price'] == '10.123456789'
    assert value['quote'] is None and 'CROSSED_QUOTE' in value['flags']
    assert 'TRADE_OLDER_THAN_15_MIN' in value['flags']
    raw['latestQuote']['bp'] = 0
    assert 'ONE_SIDED_QUOTE' in normalize_snapshot(raw, 'TEST', NOW)['flags']
    raw['latestQuote']['bp'] = 10
    assert normalize_snapshot(raw, 'TEST', NOW)['quote']['ask'] == '11'
    raw['latestTrade']['t'] = '2024-11-29T18:00:00Z'
    with pytest.raises(ValueError, match='FUTURE'):
        normalize_snapshot(raw, 'TEST', NOW)


def test_calendar_dst_early_close_and_empty_holiday():
    rows = normalize_calendar([{'date': '2024-03-08', 'open': '09:30', 'close': '16:00'},
                               {'date': '2024-03-11', 'open': '09:30', 'close': '16:00'},
                               {'date': '2024-11-29', 'open': '09:30', 'close': '13:00'}], '2024-03-01', '2024-11-30')
    assert rows[0]['open'] == '2024-03-08T14:30:00+00:00'
    assert rows[1]['open'] == '2024-03-11T13:30:00+00:00'
    assert rows[2]['close'] == '2024-11-29T18:00:00+00:00'
    assert normalize_calendar([], '2024-11-28', '2024-11-28') == []
    with pytest.raises(ValueError):
        normalize_calendar([{'date': '2024-11-29', 'open': '16:00', 'close': '13:00'}], '2024-11-29', '2024-11-29')


def test_clock_requires_recent_observation_and_real_boolean():
    clock = {'timestamp': NOW.isoformat(), 'is_open': True, 'next_open': '2024-12-02T14:30:00Z', 'next_close': '2024-11-29T18:00:00Z'}
    assert normalize_clock(clock, NOW)['is_open'] is True
    with pytest.raises(ValueError):
        normalize_clock({**clock, 'is_open': 'true'}, NOW)
    with pytest.raises(ValueError):
        normalize_clock({**clock, 'timestamp': '2024-11-29T16:00:00Z'}, NOW)


def test_paper_account_drops_identifiers_and_never_infers_usd():
    account = {'id': 'private-id', 'account_number': 'private-number', 'status': 'ACTIVE', 'currency': 'EUR',
               'equity': '10000.01', 'cash': '-12.5', 'buying_power': '20000', 'portfolio_value': '10000.01',
               'trading_blocked': False, 'account_blocked': False}
    result = normalize_account(account)
    assert result['currency'] == 'EUR' and result['cash'] == '-12.5'
    assert 'id' not in result and 'account_number' not in result
    with pytest.raises(ValueError):
        normalize_account({**account, 'equity': 'NaN'})
    position = {'asset_id': ASSET, 'symbol': 'TEST', 'asset_class': 'us_equity', 'exchange': 'NASDAQ',
                'qty': '-1.5', 'side': 'short', 'market_value': '-15', 'current_price': '10', 'unrealized_pl': '-2'}
    assert normalize_positions([position])[0]['qty'] == '-1.5'
    with pytest.raises(ValueError, match='CONFLICT'):
        normalize_positions([position, position])


def test_corporate_actions_window_is_process_date_not_ex_date():
    url, params = request_spec('corporate_actions', {'symbol': 'TEST', 'start': '2024-11-01', 'end': '2024-11-30'})
    assert url == 'https://data.alpaca.markets/v1/corporate-actions'
    assert params['data_quality'] == 'complete' and params['symbols'] == 'TEST'
    body = {'corporate_actions': {'cash_dividends': [{'id': ASSET, 'symbol': 'TEST', 'process_date': '2024-11-01',
             'ex_date': '2024-10-30', 'rate': '0.25'}]}, 'next_page_token': None}
    rows, token = normalize_corporate_actions(body, 'TEST', '2024-11-01', '2024-11-30')
    assert rows[0]['payload']['ex_date'] == '2024-10-30' and token is None
    body['corporate_actions']['cash_dividends'][0]['symbol'] = 'OTHER'
    with pytest.raises(ValueError):
        normalize_corporate_actions(body, 'TEST', '2024-11-01', '2024-11-30')
