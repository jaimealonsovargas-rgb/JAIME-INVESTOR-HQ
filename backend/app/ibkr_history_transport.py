"""Bounded, isolated daily history transport. Never opens the SDK in the backend."""
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import subprocess
import threading

from app.data_identity import fingerprint
from app.history_rights import require_ibkr_archive_rights

ROOT = Path(__file__).resolve().parents[2]
MAX_INPUT_BYTES = 16 * 1024
MAX_OUTPUT_BYTES = 512 * 1024
MAX_BARS = 64
REASONS = frozenset({'RIGHTS_RESTRICTED', 'SESSION_UNAVAILABLE', 'PROVIDER_TIMEOUT',
                     'PACING_LIMIT', 'DATA_ENTITLEMENT_REQUIRED', 'NO_DATA', 'INVALID_RESPONSE'})
LIMITATIONS = dict(calendar_validation='PENDING_D3', full_coverage_guaranteed=False,
                   date_semantics='SESSION_LABEL_NOT_PUBLICATION_TIMESTAMP',
                   adjustment='SPLIT_ADJUSTED_NOT_DIVIDENDS',
                   duration_semantics='BOUNDED_PROVIDER_DAILY_SESSIONS_FILTERED_TO_REQUEST')


class HistoryTransportError(ValueError):
    def __init__(self, reason):
        self.reason = reason if reason in REASONS else 'INVALID_RESPONSE'
        super().__init__(self.reason)


def require_rights():
    try:
        require_ibkr_archive_rights()
    except Exception:
        raise HistoryTransportError('RIGHTS_RESTRICTED') from None


def encode_request(request):
    try:
        raw = json.dumps(request, ensure_ascii=True, allow_nan=False, separators=(',', ':')).encode()
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError()
        value = json.loads(raw)
        if not isinstance(value, dict) or value.get('provider') != 'IBKR_TWS':
            raise ValueError()
        if (not isinstance(value.get('listing_id'), str) or not 0 < len(value['listing_id']) <= 200
                or not re.fullmatch('[0-9a-f]{64}', value.get('identity_hash', ''))):
            raise ValueError()
        contract = value['contract']
        keys = {'conId', 'symbol', 'secType', 'exchange', 'primaryExchange', 'currency'}
        if not isinstance(contract, dict) or set(contract) != keys:
            raise ValueError()
        if type(contract['conId']) is not int or not 0 < contract['conId'] < 2**31:
            raise ValueError()
        if contract['secType'] != 'STK':
            raise ValueError()
        for key in keys - {'conId'}:
            if not isinstance(contract[key], str) or not re.fullmatch(r'[A-Za-z0-9 ._/\-]{1,64}', contract[key]):
                raise ValueError()
        if not re.fullmatch('[A-Z]{3}', contract['currency']):
            raise ValueError()
        start, end = [date.fromisoformat(value[key]) for key in ('start', 'end')]
        if (str(start) != value['start'] or str(end) != value['end'] or not 0 <= (end-start).days < 31
                or end >= datetime.now(timezone.utc).date()):
            raise ValueError()
        if (value.get('frequency') != '1 day' or value.get('what_to_show') != 'TRADES'
                or value.get('adjustment') != 'SPLIT_ADJUSTED_NOT_DIVIDENDS' or value.get('use_rth') is not True):
            raise ValueError()
        return value, raw
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
        raise HistoryTransportError('INVALID_RESPONSE') from None


def decimal_string(value, *, volume=False):
    try:
        if isinstance(value, bool) or len(str(value)) > 64:
            raise ValueError()
        number = Decimal(str(value))
        if (not number.is_finite() or number < 0 or (not volume and number == 0)
                or number > Decimal('1e15') or number.as_tuple().exponent < -18):
            raise ValueError()
        if number == 0:
            return '0'
        result = format(number, 'f')
        return result.rstrip('0').rstrip('.') if '.' in result else result
    except (ValueError, TypeError, InvalidOperation):
        raise HistoryTransportError('INVALID_RESPONSE') from None


def validate_response(response, request):
    try:
        if not isinstance(response, dict):
            raise ValueError()
        if response.get('error') in REASONS:
            raise HistoryTransportError(response['error'])
        if (response.get('provider') != 'IBKR_TWS' or response.get('completed') is not True
                or response.get('request_hash') != fingerprint(request)
                or response.get('feed') not in {'DELAYED_HISTORY_ADVISORY_2188', 'HISTORICAL_UNCONFIRMED'}
                or response.get('metadata') != LIMITATIONS):
            raise ValueError()
        received = datetime.fromisoformat(response['received_at'])
        if received.utcoffset() != timezone.utc.utcoffset(received):
            raise ValueError()
        bars = response['bars']
        if not isinstance(bars, list) or len(bars) > MAX_BARS:
            raise ValueError()
        previous = ''
        for bar in bars:
            if not isinstance(bar, dict) or set(bar) != {'session', 'open', 'high', 'low', 'close', 'volume'}:
                raise ValueError()
            session = bar['session']
            if str(date.fromisoformat(session)) != session or not request['start'] <= session <= request['end'] or session <= previous:
                raise ValueError()
            previous = session
            for key in ('open', 'high', 'low', 'close', 'volume'):
                if not isinstance(bar[key], str) or decimal_string(bar[key], volume=key == 'volume') != bar[key]:
                    raise ValueError()
            opened, high, low, closed = [Decimal(bar[key]) for key in ('open', 'high', 'low', 'close')]
            if not low <= min(opened, closed) <= max(opened, closed) <= high:
                raise ValueError()
        if not bars:
            raise HistoryTransportError('NO_DATA')
        return response
    except HistoryTransportError:
        raise
    except (KeyError, TypeError, ValueError, InvalidOperation):
        raise HistoryTransportError('INVALID_RESPONSE') from None


def bounded_child(raw):
    """Drain both pipes with a shared hard budget; no unbounded communicate()."""
    try:
        process = subprocess.Popen([str(ROOT / '.tools/ibkr/venv/Scripts/python.exe'), '-B',
                                    str(ROOT / 'scripts/ibkr_history_worker.py')],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   cwd=str(ROOT))
    except OSError:
        raise HistoryTransportError('SESSION_UNAVAILABLE') from None
    output = bytearray()
    total = 0
    exceeded = threading.Event()
    lock = threading.Lock()

    def drain(stream, keep):
        nonlocal total
        try:
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    return
                with lock:
                    total += len(chunk)
                    if total > MAX_OUTPUT_BYTES:
                        exceeded.set()
                        process.kill()
                        return
                    if keep:
                        output.extend(chunk)
        except (OSError, ValueError):
            exceeded.set()

    def write():
        try:
            process.stdin.write(raw)
            process.stdin.close()
        except (OSError, ValueError):
            pass

    threads = [threading.Thread(target=drain, args=(process.stdout, True), daemon=True),
               threading.Thread(target=drain, args=(process.stderr, False), daemon=True),
               threading.Thread(target=write, daemon=True)]
    for thread in threads:
        thread.start()
    try:
        process.wait(timeout=70)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)
        raise HistoryTransportError('PROVIDER_TIMEOUT') from None
    finally:
        for thread in threads:
            thread.join(timeout=1)
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
    if exceeded.is_set() or any(thread.is_alive() for thread in threads) or process.returncode:
        raise HistoryTransportError('INVALID_RESPONSE')
    try:
        return json.loads(output)
    except (ValueError, UnicodeError, RecursionError):
        raise HistoryTransportError('INVALID_RESPONSE') from None


class IbkrHistoryTransport:
    provider = 'IBKR_TWS'

    def fetch(self, request):
        require_rights()  # Mandatory before spawning any process.
        value, raw = encode_request(request)
        return validate_response(bounded_child(raw), value)
