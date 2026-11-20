"""Bounded, credentialed reads from Alpaca PAPER and IEX; no order transport."""
import re
import time
from datetime import date, datetime
from urllib.parse import urlsplit

import httpx

from app.data_http import FetchError, public_dns, retry_seconds

MAX_BYTES = 24 * 1024 * 1024
PAPER = 'https://paper-api.alpaca.markets'
DATA = 'https://data.alpaca.markets'
SIMPLE = {'assets': '/v2/assets', 'clock': '/v2/clock', 'calendar': '/v2/calendar',
          'account': '/v2/account', 'positions': '/v2/positions'}


def symbol_text(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Z][A-Z0-9.\-]{0,19}', value):
        raise ValueError('ALPACA_SYMBOL_INVALID')
    return value


def date_text(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('ALPACA_DATE_INVALID')
    date.fromisoformat(value)
    return value


def timestamp_text(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError('ALPACA_TIMESTAMP_INVALID')
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.utcoffset() is None:
        raise ValueError('ALPACA_TIMESTAMP_ZONE_REQUIRED')
    return value


def page_token(value):
    if value is not None and (not isinstance(value, str) or not 1 <= len(value) <= 2048
                              or not value.isascii() or any(ord(ch) < 33 or ord(ch) > 126 for ch in value)):
        raise ValueError('ALPACA_PAGE_TOKEN_INVALID')
    return value


def request_spec(kind, params=None):
    """Reject every unrecognised input; parameters cannot override feed or host."""
    p = {} if params is None else params
    if not isinstance(p, dict):
        raise ValueError('ALPACA_PARAMS_INVALID')
    if kind in ('assets', 'clock', 'account', 'positions'):
        if p:
            raise ValueError('ALPACA_PARAMS_INVALID')
        return PAPER + SIMPLE[kind], ({'status': 'active', 'asset_class': 'us_equity'} if kind == 'assets' else {})
    if kind == 'calendar':
        if set(p) != {'start', 'end'}:
            raise ValueError('ALPACA_PARAMS_INVALID')
        start, end = date_text(p['start']), date_text(p['end'])
        if start > end or (date.fromisoformat(end) - date.fromisoformat(start)).days > 3660:
            raise ValueError('ALPACA_WINDOW_INVALID')
        return PAPER + SIMPLE[kind], {'start': start, 'end': end}
    if kind == 'snapshot':
        if set(p) != {'symbol'}:
            raise ValueError('ALPACA_PARAMS_INVALID')
        return DATA + '/v2/stocks/' + symbol_text(p['symbol']) + '/snapshot', {'feed': 'iex', 'currency': 'USD'}
    if kind in ('bars', 'corporate_actions'):
        allowed = {'symbol', 'start', 'end', 'page_token', 'limit'} | ({'adjustment'} if kind == 'bars' else set())
        if set(p) - allowed or not {'symbol', 'start', 'end'} <= set(p):
            raise ValueError('ALPACA_PARAMS_INVALID')
        symbol = symbol_text(p['symbol'])
        limit = p.get('limit', 1000)
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError('ALPACA_LIMIT_INVALID')
        token = page_token(p.get('page_token'))
        if kind == 'bars':
            start, end = timestamp_text(p['start']), timestamp_text(p['end'])
            a, b = (datetime.fromisoformat(s.replace('Z', '+00:00')) for s in (start, end))
            if a > b or (b-a).days > 3660:
                raise ValueError('ALPACA_WINDOW_INVALID')
            adjustment = p.get('adjustment', 'raw')
            if adjustment not in ('raw', 'split', 'all'):
                raise ValueError('ALPACA_ADJUSTMENT_INVALID')
            url = DATA + '/v2/stocks/' + symbol + '/bars'
            query = {'start': start, 'end': end, 'timeframe': '1Day', 'limit': limit, 'sort': 'asc',
                     'feed': 'iex', 'adjustment': adjustment, 'asof': '-', 'currency': 'USD'}
        else:
            start, end = date_text(p['start']), date_text(p['end'])
            if start > end or (date.fromisoformat(end) - date.fromisoformat(start)).days > 3660:
                raise ValueError('ALPACA_WINDOW_INVALID')
            url = DATA + '/v1/corporate-actions'
            query = {'symbols': symbol, 'start': start, 'end': end, 'limit': limit, 'sort': 'asc',
                     'region': 'us', 'data_quality': 'complete'}
        if token is not None:
            query['page_token'] = token
        return url, query
    raise ValueError('ALPACA_ENDPOINT_DENIED')


def endpoint_url(kind, params=None):
    return request_spec(kind, params)[0]


class AlpacaHttp:
    def __init__(self, settings, transport=None, resolver=public_dns):
        self.settings, self.transport, self.resolver = settings, transport, resolver
        self.real = transport is None

    def fetch(self, kind, params=None):
        try:
            url, query = request_spec(kind, params)
        except (ValueError, TypeError, KeyError):
            raise FetchError('CONFIG_REQUIRED') from None
        key, secret = (self.settings.secret(name) for name in ('alpaca_api_key', 'alpaca_secret_key'))
        if not key or not secret:
            raise FetchError('NO_CREDENTIALS')
        if any(len(value) > 512 or not value.isascii() or any(ord(ch) < 33 or ord(ch) > 126 for ch in value)
               for value in (key, secret)):
            raise FetchError('CONFIG_REQUIRED')
        headers = {'APCA-API-KEY-ID': key, 'APCA-API-SECRET-KEY': secret,
                   'Accept': 'application/json', 'User-Agent': 'JAIME-Investor-HQ/read-only'}
        started = time.monotonic()
        try:
            self.resolver(urlsplit(url).hostname)
            with httpx.Client(transport=self.transport, timeout=httpx.Timeout(20, connect=5),
                              trust_env=False, follow_redirects=False) as client:
                with client.stream('GET', url, params=query, headers=headers) as response:
                    if response.status_code != 200:
                        raise FetchError({401: 'AUTH_FAILED', 403: 'RIGHTS_RESTRICTED', 404: 'NOT_FOUND',
                                          429: 'RATE_LIMITED'}.get(response.status_code, 'ERROR'),
                                         response.status_code, retry_seconds(response.headers.get('Retry-After', '60')))
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise FetchError('INVALID_PAYLOAD', 200)
                        if time.monotonic() - started > 45:
                            raise FetchError('TIMEOUT', 200)
                        chunks.append(chunk)
                    return b''.join(chunks)
        except FetchError:
            raise
        except httpx.TimeoutException:
            raise FetchError('TIMEOUT') from None
        except (httpx.HTTPError, OSError):
            raise FetchError('OFFLINE') from None
