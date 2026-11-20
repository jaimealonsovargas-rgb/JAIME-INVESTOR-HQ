"""Private bounded IBKR daily-history worker. JSON stdin/stdout only; no disk writes."""
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from importlib.metadata import version
import json
import logging
from pathlib import Path
import socket
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.ibkr_history_transport import (HistoryTransportError, MAX_INPUT_BYTES, MAX_OUTPUT_BYTES,
    MAX_BARS, LIMITATIONS, encode_request, decimal_string, require_rights, validate_response)
from app.data_identity import fingerprint
from app.ibkr_probe_policy import validate_probe_config, matches_paper_account
from app.ibkr_data_policy import safe_error, INFO_CODES, FATAL_CODES

ALLOWED_MESSAGES = frozenset({71, 49, 59, 20, 25})
MAX_WIRE_BYTES = 512 * 1024
HISTORY_ID = 301


def make_client(wrapper, request):
    from ibapi.client import EClient
    from ibapi.common import PROTOBUF_MSG_ID
    from ibapi.contract import Contract
    request, _ = encode_request(request)

    class HistoryClient(EClient):
        def __init__(self):
            super().__init__(wrapper)
            self.sent = []
            self.verified = False
            self.scope = threading.local()

        @contextmanager
        def _command(self, ident):
            if ident not in ALLOWED_MESSAGES or (ident != 71 and not self.verified):
                raise PermissionError('IBKR_COMMAND_BLOCKED')
            if ident in self.sent:
                raise PermissionError('IBKR_REQUEST_BUDGET_EXCEEDED')
            if getattr(self.scope, 'ident', None) is not None:
                raise PermissionError('NESTED_COMMAND_BLOCKED')
            self.scope.ident = ident
            try:
                yield
            finally:
                self.scope.ident = None

        def _check(self, ident):
            if ident not in ALLOWED_MESSAGES or ident != getattr(self.scope, 'ident', None):
                raise PermissionError('IBKR_MESSAGE_BLOCKED')
            if ident in self.sent:
                raise PermissionError('IBKR_REQUEST_BUDGET_EXCEEDED')
            self.sent.append(ident)

        def sendMsg(self, ident, message):
            self._check(ident)
            return super().sendMsg(ident, message)

        def sendMsgProtoBuf(self, ident, message):
            self._check(ident - PROTOBUF_MSG_ID)
            return super().sendMsgProtoBuf(ident, message)

        def startApi(self):
            with self._command(71):
                super().startApi()

        def clock_request(self):
            with self._command(49):
                self.reqCurrentTime()

        def delayed_request(self):
            with self._command(59):
                self.reqMarketDataType(3)

        def history_request(self):
            contract = Contract()
            for key, value in request['contract'].items():
                setattr(contract, key, value)
            end = date.fromisoformat(request['end']) + timedelta(days=1)
            days = (end - date.fromisoformat(request['start'])).days
            with self._command(20):
                self.reqHistoricalData(HISTORY_ID, contract, end.strftime('%Y%m%d 00:00:00 UTC'),
                                       f'{days} D', '1 day', 'TRADES', 1, 1, False, [])

        def cancel_history(self):
            with self._command(25):
                self.cancelHistoricalData(HISTORY_ID)

    return HistoryClient()


def bounded_connection(base, fatal, state):
    class BoundedConnection(base):
        def _recvAllMsg(self):
            chunk = self.socket.recv(4096)
            state['wire_bytes'] += len(chunk)
            if state['wire_bytes'] > MAX_WIRE_BYTES:
                state['reason'] = 'INVALID_RESPONSE'
                fatal.set()
                self.disconnect()
                return b''
            return chunk
    return BoundedConnection


def run_history(config, request):
    require_rights()  # Independent worker gate; never rely on the parent's gate.
    request, _ = encode_request(request)
    validate_probe_config(config)
    if version('ibapi') != '1052.1' or version('protobuf') != '7.36.2':
        raise HistoryTransportError('SESSION_UNAVAILABLE')
    from ibapi.wrapper import EWrapper
    import ibapi.client as sdk_client
    logging.disable(logging.CRITICAL)
    handshake, account, clock, done, fatal = [threading.Event() for _ in range(5)]
    state = dict(wire_bytes=0, reason=None, account=False, completed=False,
                 feed='HISTORICAL_UNCONFIRMED', bars=[], callbacks=0, previous='', notices=0)
    start, end = [date.fromisoformat(request[key]) for key in ('start', 'end')]

    class Observer(EWrapper):
        def nextValidId(self, orderId):
            handshake.set()

        def managedAccounts(self, accountsList):
            state['account'] = matches_paper_account(accountsList, config['paper_account_sha256'])
            if not state['account']:
                state['reason'] = 'SESSION_UNAVAILABLE'
                fatal.set()
            account.set()

        def currentTime(self, epoch):
            if abs(epoch - time.time()) > 120:
                state['reason'] = 'SESSION_UNAVAILABLE'
                fatal.set()
            clock.set()

        def connectionClosed(self):
            if not state['completed']:
                state['reason'] = state['reason'] or 'SESSION_UNAVAILABLE'
                fatal.set()

        def error(self, reqId, errorTime, errorCode, errorString, advancedOrderRejectJson=''):
            state['notices'] += 1
            if state['notices'] > 64:
                state['reason'] = 'INVALID_RESPONSE'
                fatal.set()
                return
            if errorCode in FATAL_CODES:
                state['reason'] = 'SESSION_UNAVAILABLE'
                fatal.set()
            elif reqId == HISTORY_ID and errorCode == 2188:
                state['feed'] = 'DELAYED_HISTORY_ADVISORY_2188'
            elif reqId == HISTORY_ID and errorCode not in INFO_CODES:
                reason = safe_error(errorCode, errorString)
                state['reason'] = reason if reason in {'PACING_LIMIT', 'DATA_ENTITLEMENT_REQUIRED', 'NO_DATA'} else 'INVALID_RESPONSE'
                done.set()

        def historicalData(self, reqId, bar):
            if reqId != HISTORY_ID or fatal.is_set():
                return
            try:
                state['callbacks'] += 1
                if state['completed'] or state['callbacks'] > MAX_BARS:
                    raise ValueError()
                label = bar.date
                if not isinstance(label, str) or len(label) != 8 or not label.isascii() or not label.isdigit():
                    raise ValueError()
                session = datetime.strptime(label, '%Y%m%d').date()
                # Daily duration can denote trading sessions. Validate the bounded
                # overfetch, then expose only the exact requested calendar interval.
                if not end - timedelta(days=96) <= session <= end or label <= state['previous']:
                    raise ValueError()
                state['previous'] = label
                values = {key: decimal_string(getattr(bar, key), volume=key == 'volume')
                          for key in ('open', 'high', 'low', 'close', 'volume')}
                opened, high, low, closed = [Decimal(values[key]) for key in ('open', 'high', 'low', 'close')]
                if not low <= min(opened, closed) <= max(opened, closed) <= high:
                    raise ValueError()
                if start <= session <= end:
                    state['bars'].append(dict(session=session.isoformat(), **values))
            except (ValueError, TypeError, AttributeError, OverflowError):
                state['reason'] = 'INVALID_RESPONSE'
                fatal.set()
                done.set()

        def historicalDataEnd(self, reqId, first, last):
            if reqId == HISTORY_ID:
                if state['completed']:
                    state['reason'] = 'INVALID_RESPONSE'
                    fatal.set()
                state['completed'] = True
                done.set()

    client = make_client(Observer(), request)
    original_connection = sdk_client.Connection
    sdk_client.Connection = bounded_connection(original_connection, fatal, state)
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(3)
    deadline = time.monotonic() + 55

    def wait(event, seconds):
        until = min(deadline, time.monotonic() + seconds)
        while not event.is_set() and not fatal.is_set() and time.monotonic() < until:
            event.wait(min(.1, max(0, until - time.monotonic())))
        return event.is_set() and not fatal.is_set()

    def loop():
        try:
            client.connect(config['host'], config['port'], clientId=config['client_id'])
            client.run()
        except Exception:
            state['reason'] = 'SESSION_UNAVAILABLE'
            fatal.set()

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    try:
        if not wait(handshake, 8) or not wait(account, 4):
            raise HistoryTransportError(state['reason'] or 'SESSION_UNAVAILABLE')
        client.verified = True
        client.clock_request()
        if not wait(clock, 4):
            raise HistoryTransportError(state['reason'] or 'SESSION_UNAVAILABLE')
        client.delayed_request()
        client.history_request()
        if not wait(done, 35):
            if not fatal.is_set():
                client.cancel_history()
            raise HistoryTransportError(state['reason'] or 'PROVIDER_TIMEOUT')
        if state['reason']:
            raise HistoryTransportError(state['reason'])
        response = dict(provider='IBKR_TWS', request_hash=fingerprint(request), completed=state['completed'],
                        received_at=datetime.now(timezone.utc).isoformat(), feed=state['feed'],
                        bars=state['bars'], metadata=dict(LIMITATIONS))
        return validate_response(response, request)
    finally:
        client.disconnect()
        thread.join(timeout=2)
        sdk_client.Connection = original_connection
        socket.setdefaulttimeout(old_timeout)


def main():
    logging.disable(logging.CRITICAL)
    try:
        require_rights()  # Also before reading private config or importing the SDK.
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise HistoryTransportError('INVALID_RESPONSE')
        request = json.loads(raw)
        config = json.loads((ROOT / '.tools/ibkr/pilot.json').read_text(encoding='utf-8'))
        response = run_history(config, request)
    except HistoryTransportError as exc:
        response = dict(error=exc.reason)
    except Exception:
        response = dict(error='INVALID_RESPONSE')
    encoded = json.dumps(response, ensure_ascii=True, allow_nan=False).encode()
    if len(encoded) > MAX_OUTPUT_BYTES:
        encoded = b'{"error":"INVALID_RESPONSE"}'
    sys.stdout.buffer.write(encoded)


if __name__ == '__main__':
    main()
