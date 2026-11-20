"""Pinned Zagreb historical website export, ordinary shares traded in EUR since 2023."""
from datetime import date, timedelta, timezone
from decimal import Decimal
import json
import re
from urllib.parse import urlsplit

ISIN = 'HRHT00RA0005'
MIC = 'XZAG'
SYMBOL = 'HT'
NAME = 'Hrvatski Telekom (HT d.d.)'
IDENTITY = f'https://zse.hr/en/papir/310?isin={ISIN}'
BASE_URL = f'https://zse.hr/json/securityHistory/{ISIN}'
POLICY = 'https://zse.hr/UserDocsImages/docs/marketdata/vendors/2019-05%20-%20ZSE%20Data%20vending%20policy%20of%20the%20Zagreb%20Stock%20Exchange.pdf'
MAX_AGE_DAYS = 5


def window(now):
    # Midnight UTC is after midnight in Zagreb in both summer and winter.
    end = now.astimezone(timezone.utc).date() - timedelta(days=1)
    return end - timedelta(days=13), end


def request_url(now):
    start, end = window(now)
    return f'{BASE_URL}/{start}/{end}/en'


def historical_closes(raw, received):
    body = json.loads(raw, parse_float=Decimal)
    if not isinstance(body, dict) or body.get('ErrMsg') != '' or body.get('DualView') is not False:
        raise ValueError('ZSE_HISTORY_FORMAT')
    start = date.fromisoformat(body['DateFromRaw'])
    end = date.fromisoformat(body['DateToRaw'])
    _, requested_end = window(received)
    # Allow a request crossing UTC midnight, always strictly before today's session.
    if (end not in (requested_end, requested_end - timedelta(days=1)) or
        start != end - timedelta(days=13) or start.year < 2023):
        raise ValueError('ZSE_HISTORY_WINDOW')
    target = urlsplit(body['url'])
    suffix = f'/security-history/{MIC}/{ISIN}/{start}/{end}/json'
    if (target.scheme != 'https' or target.netloc != 'rest.zse.hr' or
        not target.path.endswith(suffix) or target.query != 'trading_model_id=CT' or target.fragment):
        raise ValueError('ZSE_HISTORY_IDENTITY')
    rows = body['rows']
    if not isinstance(rows, list) or len(rows) > 14:
        raise ValueError('ZSE_HISTORY_SIZE')
    seen = set()
    closes = []
    for row in rows:
        day = date.fromisoformat(row['date_yyyy_MM_dd'])
        if (day in seen or not start <= day <= end or row['security_class_id'] != 'EQTY'
                or row['trading_model_id'] != 'CT'):
            raise ValueError('ZSE_HISTORY_SESSION')
        seen.add(day)
        trades = str(row['num_trades'])
        if not re.fullmatch(r'(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)', trades):
            raise ValueError('ZSE_HISTORY_TRADES')
        if int(trades.replace(',', '')) == 0:
            continue
        price = row['last_price_n']
        if type(price) not in (int, Decimal) or not Decimal(price).is_finite() or price <= 0:
            raise ValueError('ZSE_HISTORY_PRICE')
        closes.append((day.isoformat(), price, f'{BASE_URL}/{start}/{end}/en?trading_model_id=CT'))
    return sorted(closes, reverse=True)
