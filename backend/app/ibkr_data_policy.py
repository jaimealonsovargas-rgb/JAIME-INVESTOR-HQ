"""D1 bounded access diagnosis, not dataset admission or a market data licence."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import re

CONTRACT = dict(conId=265598, symbol='AAPL', secType='STK', exchange='SMART',
                primaryExchange='NASDAQ', currency='USD', localSymbol='AAPL', tradingClass='NMS')
ALLOWED_MESSAGES = frozenset({71, 49, 59, 20, 25, 1, 2})
MAX_WIRE_BYTES = 128 * 1024
MAX_REPORT_BYTES = 32 * 1024
MAX_BARS = 8
HISTORY_ID, QUOTE_ID = 201, 202
FATAL_CODES = frozenset({502, 504, 1100, 1300, 326})
INFO_CODES = frozenset({2104, 2106, 2107, 2108, 2158})


def end_time(now):
    if now.utcoffset() is None:
        raise ValueError('AWARE_TIME_REQUIRED')
    return now.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def safe_error(code, message):
    """Map provider prose to fixed reasons; never retain account/contract/error text."""
    value = message.lower()
    if code in INFO_CODES:
        return 'SERVICE_NOTICE'
    if code == 2188:
        return 'UP_TO_SECOND_SUBSCRIPTION_ADVISORY'
    if code in FATAL_CODES:
        return 'SESSION_ERROR'
    if code in {354, 10089, 10090, 10167, 10168, 10186} or (code == 162 and any(
            token in value for token in ('permission', 'subscription', 'not subscribed'))):
        return 'DATA_ENTITLEMENT_REQUIRED'
    if code == 162 and 'pacing' in value:
        return 'PACING_LIMIT'
    if code == 162 and 'cancel' in value:
        return 'REQUEST_CANCELLED'
    if code == 162 and ('no data' in value or 'query returned no' in value):
        return 'NO_DATA'
    return 'PROVIDER_ERROR'  # 162 alone is not proof of missing subscription.


def price(value, *, allow_zero=False):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or (not allow_zero and number == 0) or number > Decimal('1e15'):
            raise ValueError('INVALID_NUMBER')
        return number
    except (InvalidOperation, TypeError):
        raise ValueError('INVALID_NUMBER') from None


def bar_metadata(bar, end, previous=None):
    """Inspect OHLCV in RAM; return only the session label, never price values."""
    label = bar.date
    if not re.fullmatch(r'\d{8}', label):
        raise ValueError('INVALID_SESSION_LABEL')
    day = datetime.strptime(label, '%Y%m%d').date()
    # Daily duration may cover trading sessions across non-trading days. This is
    # a bounded diagnosis (14 calendar-day safety envelope), NOT calendar admission.
    if not end.date()-timedelta(days=14) <= day < end.date():
        raise ValueError('BAR_OUTSIDE_REQUEST_WINDOW')
    if previous and label <= previous:
        raise ValueError('UNORDERED_OR_DUPLICATE_BAR')
    opened, high, low, closed = [price(getattr(bar, key)) for key in ('open','high','low','close')]
    price(bar.volume, allow_zero=True)
    if not low <= min(opened, closed) <= max(opened, closed) <= high:
        raise ValueError('OHLC_INCONSISTENT')
    return label


def classify_history(completed, dates, quality_errors, errors):
    if quality_errors:
        return 'QUALITY_REJECTED'
    if errors:
        return 'DATA_ENTITLEMENT_REQUIRED' if any(e['reason']=='DATA_ENTITLEMENT_REQUIRED' for e in errors) else 'PROVIDER_ERROR'
    if not completed:
        return 'INCOMPLETE_OR_TIMEOUT'
    return 'ACCESS_OBSERVED' if dates else 'EMPTY_RESPONSE'


def classify_quote(feed, ticks, completed, errors=()):
    # Requested feed type is not evidence of returned feed. Never infer live from absence of callback.
    if not ticks and any(e['reason']=='DATA_ENTITLEMENT_REQUIRED' for e in errors):
        return 'DATA_ENTITLEMENT_REQUIRED'
    if feed not in {1,2,3,4}:
        return 'FEED_UNCONFIRMED'
    expected = {1,2,4} if feed in {1,2} else {66,67,68}
    if not expected.intersection(ticks):
        return 'NO_VALID_TOP_OF_BOOK'
    return 'ACCESS_OBSERVED' if completed else 'PARTIAL_OBSERVATION'
