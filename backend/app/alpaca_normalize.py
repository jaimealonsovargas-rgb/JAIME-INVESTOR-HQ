"""Typed observations; these parsers never infer issuer links or trading readiness."""
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
import re
from uuid import UUID
from zoneinfo import ZoneInfo

from app.alpaca_http import symbol_text, date_text, page_token


def decimal_text(value, *, minimum=None, maximum=Decimal('1e30')):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError('ALPACA_NUMBER_INVALID')
    source = str(value)
    if len(source) > 128:
        raise ValueError('ALPACA_NUMBER_INVALID')
    try:
        number = Decimal(source)
    except InvalidOperation:
        raise ValueError('ALPACA_NUMBER_INVALID') from None
    if (not number.is_finite() or abs(number) > maximum or number.as_tuple().exponent < -18
            or number.as_tuple().exponent > 30 or (minimum is not None and number < minimum)):
        raise ValueError('ALPACA_NUMBER_INVALID')
    return format(number, 'f')


def positive(value):
    text = decimal_text(value, minimum=Decimal(0))
    if Decimal(text) == 0:
        raise ValueError('ALPACA_PRICE_INVALID')
    return text


def instant(value):
    if not isinstance(value, str) or not 10 <= len(value) <= 40:
        raise ValueError('ALPACA_TIMESTAMP_INVALID')
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('ALPACA_TIMESTAMP_INVALID') from None
    if stamp.utcoffset() is None:
        raise ValueError('ALPACA_TIMESTAMP_ZONE_REQUIRED')
    return stamp.astimezone(timezone.utc)


def utc(value):
    return instant(value).isoformat()


def _object(body):
    if not isinstance(body, dict):
        raise ValueError('ALPACA_OBJECT_REQUIRED')
    return body


def _integer(value):
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError('ALPACA_INTEGER_INVALID')
    return value


def _bar(body):
    _object(body)
    prices = {name: positive(body[key]) for name, key in (('open', 'o'), ('high', 'h'), ('low', 'l'), ('close', 'c'))}
    lo, hi, opening, close = (Decimal(prices[k]) for k in ('low', 'high', 'open', 'close'))
    if not lo <= opening <= hi or not lo <= close <= hi:
        raise ValueError('ALPACA_OHLC_INVALID')
    volume = decimal_text(body['v'], minimum=Decimal(0))
    count = _integer(body['n']) if body.get('n') is not None else None
    vwap = positive(body['vw']) if body.get('vw') is not None else None
    # VWAP of an adjusted historical bar need not lie within rounded OHLC bounds.
    return {'timestamp': utc(body['t']), **prices, 'volume': volume, 'trade_count': count, 'vwap': vwap}


def normalize_bars(body, symbol, start, end, adjustment):
    _object(body)
    symbol_text(symbol)
    if adjustment not in ('raw', 'split', 'all') or body.get('symbol') != symbol:
        raise ValueError('ALPACA_BAR_IDENTITY_INVALID')
    a, b = instant(start), instant(end)
    if a > b or b > datetime.now(timezone.utc) + timedelta(seconds=5):
        raise ValueError('ALPACA_WINDOW_INVALID')
    raw = body.get('bars')
    if raw is None:
        raw = []  # Alpaca may return bars:null for an empty window.
    if not isinstance(raw, list) or len(raw) > 1000:
        raise ValueError('ALPACA_BARS_INVALID')
    rows = {}
    previous = None
    for item in raw:
        row = {**_bar(item), 'symbol': symbol, 'feed': 'iex', 'currency': 'USD', 'adjustment': adjustment}
        stamp = instant(row['timestamp'])
        if not a <= stamp <= b or (previous is not None and stamp < previous):
            raise ValueError('ALPACA_BAR_RANGE_INVALID')
        previous = stamp
        if row['timestamp'] in rows and rows[row['timestamp']] != row:
            raise ValueError('ALPACA_BAR_CONFLICT')
        rows[row['timestamp']] = row
    return list(rows.values()), page_token(body.get('next_page_token'))


def normalize_snapshot(body, symbol, now):
    _object(body)
    symbol_text(symbol)
    if 'symbol' in body and body['symbol'] != symbol:
        raise ValueError('ALPACA_SNAPSHOT_IDENTITY_INVALID')
    if not {'latestTrade', 'latestQuote', 'dailyBar', 'prevDailyBar', 'minuteBar'} & set(body):
        raise ValueError('ALPACA_SNAPSHOT_INVALID')
    flags, trade, quote = [], None, None
    if body.get('latestTrade') is not None:
        t = _object(body['latestTrade'])
        stamp = instant(t['t'])
        if stamp > now + timedelta(seconds=5):
            raise ValueError('ALPACA_FUTURE_TRADE')
        exchange = t.get('x')
        if exchange is not None and (not isinstance(exchange, str) or not re.fullmatch(r'[A-Z0-9]{1,5}', exchange)):
            raise ValueError('ALPACA_EXCHANGE_INVALID')
        trade = {'price': positive(t['p']), 'timestamp': stamp.isoformat(), 'exchange': exchange,
                 'size': decimal_text(t['s'], minimum=Decimal(0)) if t.get('s') is not None else None}
        if now - stamp > timedelta(minutes=15):
            flags.append('TRADE_OLDER_THAN_15_MIN')
    if body.get('latestQuote') is not None:
        q = _object(body['latestQuote'])
        stamp = instant(q['t'])
        if stamp > now + timedelta(seconds=5):
            raise ValueError('ALPACA_FUTURE_QUOTE')
        bid, ask = (decimal_text(q[k], minimum=Decimal(0)) for k in ('bp', 'ap'))
        if Decimal(bid) == 0 or Decimal(ask) == 0:
            flags.append('ONE_SIDED_QUOTE')
        elif Decimal(bid) > Decimal(ask):
            flags.append('CROSSED_QUOTE')
        else:
            quote = {'bid': bid, 'ask': ask, 'timestamp': stamp.isoformat(),
                     'bid_size': decimal_text(q['bs'], minimum=Decimal(0)),
                     'ask_size': decimal_text(q['as'], minimum=Decimal(0))}
        if now - stamp > timedelta(minutes=15):
            flags.append('QUOTE_OLDER_THAN_15_MIN')
    result = {'symbol': symbol, 'feed': 'iex', 'currency': 'USD', 'trade': trade, 'quote': quote,
              'daily_bar': None, 'previous_daily_bar': None, 'flags': flags}
    for field, key in (('daily_bar', 'dailyBar'), ('previous_daily_bar', 'prevDailyBar')):
        if body.get(key) is not None:
            bar = _bar(body[key])
            if instant(bar['timestamp']) > now + timedelta(seconds=5):
                raise ValueError('ALPACA_FUTURE_BAR')
            result[field] = bar
    if trade is None:
        flags.append('NO_TRADE')
    return result


def normalize_clock(body, now):
    _object(body)
    stamp, opening, close = (instant(body[k]) for k in ('timestamp', 'next_open', 'next_close'))
    if type(body.get('is_open')) is not bool or abs((now-stamp).total_seconds()) > 300:
        raise ValueError('ALPACA_CLOCK_INVALID')
    if opening <= stamp or close <= stamp:
        raise ValueError('ALPACA_CLOCK_INVALID')
    return {'timestamp': stamp.isoformat(), 'is_open': body['is_open'],
            'next_open': opening.isoformat(), 'next_close': close.isoformat()}


def normalize_calendar(body, start, end):
    start, end = date_text(start), date_text(end)
    if start > end or not isinstance(body, list) or len(body) > 3661:
        raise ValueError('ALPACA_CALENDAR_INVALID')
    eastern = ZoneInfo('America/New_York')
    result, seen = [], set()
    for item in body:
        _object(item)
        day = date_text(item['date'])
        if day in seen or not start <= day <= end:
            raise ValueError('ALPACA_SESSION_INVALID')
        seen.add(day)
        clocks = []
        for key in ('open', 'close'):
            value = item[key]
            if not isinstance(value, str) or not re.fullmatch(r'\d{2}:\d{2}', value):
                raise ValueError('ALPACA_SESSION_TIME_INVALID')
            local = datetime.combine(date.fromisoformat(day), time.fromisoformat(value), eastern)
            clocks.append(local.astimezone(timezone.utc))
        opening, close = clocks
        if opening >= close:
            raise ValueError('ALPACA_SESSION_TIME_INVALID')
        result.append({'date': day, 'open': opening.isoformat(), 'close': close.isoformat(),
                       'timezone': 'America/New_York'})
    return sorted(result, key=lambda row: row['date'])


def normalize_account(body):
    _object(body)
    status, currency = body.get('status'), body.get('currency')
    if not isinstance(status, str) or not re.fullmatch(r'[A-Z_]{1,40}', status):
        raise ValueError('ALPACA_ACCOUNT_INVALID')
    if not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency):
        raise ValueError('ALPACA_ACCOUNT_CURRENCY_INVALID')
    result = {'status': status, 'currency': currency}
    for key in ('equity', 'cash', 'buying_power', 'portfolio_value'):
        result[key] = decimal_text(body[key])
    for key in ('trading_blocked', 'account_blocked'):
        if type(body.get(key)) is not bool:
            raise ValueError('ALPACA_ACCOUNT_INVALID')
        result[key] = body[key]
    return result


def normalize_positions(body):
    if not isinstance(body, list) or len(body) > 10000:
        raise ValueError('ALPACA_POSITIONS_INVALID')
    result, seen = [], set()
    for item in body:
        _object(item)
        ident = str(UUID(item['asset_id']))
        if ident in seen:
            raise ValueError('ALPACA_POSITION_CONFLICT')
        seen.add(ident)
        asset_class, exchange = item.get('asset_class'), item.get('exchange')
        if asset_class not in ('us_equity', 'us_option', 'crypto') or not isinstance(exchange, str) or not re.fullmatch(r'[A-Z_]{1,40}', exchange):
            raise ValueError('ALPACA_POSITION_INVALID')
        symbol = item.get('symbol')
        if not isinstance(symbol, str) or not re.fullmatch(r'[A-Z0-9./\-]{1,40}', symbol):
            raise ValueError('ALPACA_POSITION_SYMBOL_INVALID')
        if item.get('side') not in ('long', 'short'):
            raise ValueError('ALPACA_POSITION_INVALID')
        result.append({'asset_id': ident, 'symbol': symbol, 'asset_class': asset_class, 'exchange': exchange,
                       'side': item['side'], 'qty': decimal_text(item['qty']),
                       'current_price': positive(item['current_price']) if item.get('current_price') is not None else None,
                       'market_value': decimal_text(item['market_value']), 'unrealized_pl': decimal_text(item['unrealized_pl'])})
    return result


_ACTION_GROUPS = frozenset(('reverse_splits', 'forward_splits', 'unit_splits', 'cash_dividends', 'stock_dividends',
    'spin_offs', 'cash_mergers', 'stock_mergers', 'stock_and_cash_mergers', 'redemptions', 'name_changes',
    'worthless_removals', 'rights_distributions', 'partial_calls', 'reorganizations', 'capital_gains_distributions'))


def normalize_corporate_actions(body, symbol, start, end):
    """Retain evidence by PROCESS date; this does not certify ex-date completeness."""
    _object(body)
    symbol_text(symbol)
    start, end = date_text(start), date_text(end)
    groups = _object(body.get('corporate_actions'))
    if start > end or set(groups) - _ACTION_GROUPS:
        raise ValueError('ALPACA_ACTION_SHAPE_INVALID')
    result, seen = [], set()
    for kind, rows in groups.items():
        if not isinstance(rows, list) or len(rows) > 1000:
            raise ValueError('ALPACA_ACTIONS_INVALID')
        for item in rows:
            _object(item)
            ident = str(UUID(item['id']))
            processed = date_text(item['process_date'])
            symbols = [item[k] for k in ('symbol', 'old_symbol', 'new_symbol', 'initiating_symbol', 'target_symbol')
                       if item.get(k) is not None]
            if symbol not in symbols or not start <= processed <= end or ident in seen:
                raise ValueError('ALPACA_ACTION_IDENTITY_INVALID')
            if len(result) >= 1000:
                raise ValueError('ALPACA_ACTIONS_INVALID')
            seen.add(ident)
            payload = {}
            # Public corporate event scalars only; no links/instructions interpreted.
            for key, value in item.items():
                if not isinstance(key, str) or not re.fullmatch(r'[a-z_]{1,80}', key):
                    raise ValueError('ALPACA_ACTION_FIELD_INVALID')
                if value is None or isinstance(value, bool):
                    payload[key] = value
                elif isinstance(value, str):
                    if len(value) > 1000 or any(ord(ch) < 32 for ch in value):
                        raise ValueError('ALPACA_ACTION_TEXT_INVALID')
                    payload[key] = value
                elif isinstance(value, (int, float, Decimal)):
                    payload[key] = decimal_text(value)
                else:
                    raise ValueError('ALPACA_ACTION_FIELD_INVALID')
            result.append({'id': ident, 'kind': kind, 'process_date': processed, 'symbol': symbol, 'payload': payload})
    return result, page_token(body.get('next_page_token'))
