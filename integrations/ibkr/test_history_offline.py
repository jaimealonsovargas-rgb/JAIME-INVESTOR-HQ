"""D2 SDK protocol/flow tests. All SDK clients use fake sinks; never a socket."""
from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import ibkr_history_worker as worker
from app import ibkr_history_transport as transport
from app.data_identity import fingerprint
from ibapi.client import EClient
from ibapi.wrapper import EWrapper


def request():
    return dict(provider='IBKR_TWS', listing_id='listing-aapl', identity_hash='a' * 64,
                contract=dict(conId=265598, symbol='AAPL', secType='STK', exchange='SMART',
                              primaryExchange='NASDAQ', currency='USD'),
                start='2026-10-01', end='2026-10-31', frequency='1 day',
                adjustment='SPLIT_ADJUSTED_NOT_DIVIDENDS', what_to_show='TRADES', use_rth=True,
                purpose='OFFLINE_TEST', metadata=dict(source='fixture'))


def response(req=None):
    return dict(provider='IBKR_TWS', request_hash=fingerprint(req or request()), completed=True,
                received_at='2026-11-01T10:00:00+00:00', feed='HISTORICAL_UNCONFIRMED',
                bars=[dict(session='2026-10-01', open='10', high='12', low='9', close='11', volume='100')],
                metadata=dict(transport.LIMITATIONS))


class Sink:
    def __init__(self): self.messages = []
    def sendMsg(self, message): self.messages.append(message)
    def isConnected(self): return True


class RequestTests(unittest.TestCase):
    def test_exact_fingerprint_preserves_additional_metadata(self):
        value, raw = transport.encode_request(request())
        self.assertEqual(value, request())
        self.assertEqual(fingerprint(json.loads(raw)), fingerprint(request()))
        self.assertEqual(transport.validate_response(response(), value), response())
        changed = deepcopy(value)
        changed['metadata']['source'] = 'changed'
        with self.assertRaises(transport.HistoryTransportError):
            transport.validate_response(response(), changed)

    def test_request_bounds_and_fixed_semantics(self):
        changes = [dict(end='2026-11-01'), dict(frequency='1 min'), dict(use_rth=1),
                   dict(adjustment='TOTAL_RETURN'), dict(what_to_show='MIDPOINT'),
                   dict(provider='OTHER'), dict(identity_hash='invalid'), dict(start='20261001'),
                   dict(metadata='x' * transport.MAX_INPUT_BYTES)]
        for change in changes:
            with self.subTest(change=list(change)):
                with self.assertRaises(transport.HistoryTransportError):
                    transport.encode_request(dict(request(), **change))
        for key, val in [('conId', True), ('conId', -1), ('secType', 'OPT'), ('currency', '')]:
            req = request()
            req['contract'][key] = val
            with self.assertRaises(transport.HistoryTransportError):
                transport.encode_request(req)

    def test_invalid_decimal_is_bounded(self):
        for value in ('NaN', 'Infinity', '-1', '1e1000000', '1e-1000000', '0', True):
            with self.assertRaises(transport.HistoryTransportError):
                transport.decimal_string(value)
        self.assertEqual(transport.decimal_string('0', volume=True), '0')

    def test_parent_response_validation(self):
        cases = []
        for key, value in [('completed', False), ('feed', 'LIVE'), ('request_hash', 'b' * 64),
                           ('received_at', '2026-11-01T10:00:00'), ('metadata', {})]:
            cases.append(dict(response(), **{key: value}))
        for key, value in [('session', '2026-11-01'), ('open', 'NaN'), ('high', '1'), ('volume', '-1')]:
            item = response()
            item['bars'][0][key] = value
            cases.append(item)
        item = response()
        item['bars'] *= 65
        cases.append(item)
        for item in cases:
            with self.assertRaises(transport.HistoryTransportError):
                transport.validate_response(item, request())

    def test_empty_and_safe_error_envelope(self):
        with self.assertRaisesRegex(transport.HistoryTransportError, 'NO_DATA'):
            transport.validate_response(dict(response(), bars=[]), request())
        for reason in transport.REASONS:
            with self.assertRaisesRegex(transport.HistoryTransportError, reason):
                transport.validate_response(dict(error=reason), request())
        with self.assertRaisesRegex(transport.HistoryTransportError, 'INVALID_RESPONSE'):
            transport.validate_response(dict(error='SECRET_ACCOUNT'), request())

    def test_closed_parent_gate_precedes_child(self):
        with patch.object(transport, 'bounded_child') as child:
            with self.assertRaisesRegex(transport.HistoryTransportError, 'RIGHTS_RESTRICTED'):
                transport.IbkrHistoryTransport().fetch(request())
            child.assert_not_called()

    def test_closed_worker_gate_precedes_client_and_config(self):
        with patch.object(worker, 'make_client') as client:
            with self.assertRaisesRegex(transport.HistoryTransportError, 'RIGHTS_RESTRICTED'):
                worker.run_history({}, request())
            client.assert_not_called()

    def test_parent_handshake_offline(self):
        with patch.object(transport, 'require_ibkr_archive_rights', return_value=None), \
             patch.object(transport, 'bounded_child', return_value=response()) as child:
            self.assertEqual(transport.IbkrHistoryTransport().fetch(request()), response())
            self.assertEqual(json.loads(child.call_args.args[0]), request())


class WireTests(unittest.TestCase):
    def client(self, server=226):
        client = worker.make_client(EWrapper(), request())
        client.conn = Sink()
        client.connState = EClient.CONNECTED
        client.serverVersion_ = server
        client.clientId = 27
        return client

    def test_preverification_commands_blocked(self):
        client = self.client()
        for method in (client.clock_request, client.delayed_request, client.history_request, client.cancel_history):
            with self.assertRaises(PermissionError): method()
        self.assertEqual(client.conn.messages, [])

    def test_legacy_and_proto_reject_all_unsolicited_commands(self):
        client = self.client()
        client.verified = True
        for ident in range(-1, 401):
            with self.assertRaises(PermissionError): client.sendMsg(ident, '')
            with self.assertRaises(PermissionError): client.sendMsgProtoBuf(ident + 200, b'')
        self.assertEqual(client.conn.messages, [])

    def test_actual_sdk_serializes_only_five_commands_once(self):
        for server in (100, 226):
            client = self.client(server)
            client.startApi()
            client.verified = True
            client.clock_request()
            client.delayed_request()
            client.history_request()
            client.cancel_history()
            self.assertEqual(client.sent, [71, 49, 59, 20, 25])
            self.assertEqual(len(client.conn.messages), 5)
            for method in (client.startApi, client.clock_request, client.delayed_request, client.history_request, client.cancel_history):
                with self.assertRaises(PermissionError): method()

    def test_contextual_id_and_nested_scope_rejected(self):
        client = self.client()
        client.verified = True
        with client._command(20):
            with self.assertRaises(PermissionError): client.sendMsg(1, '')
            with self.assertRaises(PermissionError): client.sendMsgProtoBuf(201, b'')
            with self.assertRaises(PermissionError):
                with client._command(49): pass
        self.assertEqual(client.conn.messages, [])

    def test_fixed_contract_and_daily_nonstreaming_arguments(self):
        client = self.client()
        client.verified = True
        with patch.object(EClient, 'reqHistoricalData') as call:
            client.history_request()
            args = call.call_args.args
            self.assertEqual(args[0], worker.HISTORY_ID)
            self.assertEqual(args[1].conId, 265598)
            self.assertEqual(args[2:], ('20261101 00:00:00 UTC', '31 D', '1 day', 'TRADES', 1, 1, False, []))
        with patch.object(EClient, 'reqMarketDataType') as call:
            client.delayed_request()
            call.assert_called_once_with(3)

    def test_wire_budget_disconnects(self):
        state = dict(wire_bytes=worker.MAX_WIRE_BYTES, reason=None)
        fatal = threading.Event()
        class Base:
            socket = SimpleNamespace(recv=lambda size: b'x')
            def disconnect(self): self.closed = True
        connection = worker.bounded_connection(Base, fatal, state)()
        self.assertEqual(connection._recvAllMsg(), b'')
        self.assertTrue(connection.closed and fatal.is_set())
        self.assertEqual(state['reason'], 'INVALID_RESPONSE')


class FlowTests(unittest.TestCase):
    def simulated(self, mode):
        config = dict(host='127.0.0.1', port=7497, client_id=27, read_only_confirmed_in_tws=True,
                      paper_account_sha256=sha256(b'DU123456').hexdigest())
        holders = []
        class FakeClient:
            def __init__(self, wrapper, req): self.w = wrapper; self.sent = []; self.closed = False; holders.append(self)
            def connect(self, *args, **kwargs):
                self.w.nextValidId(1)
                self.w.managedAccounts('U123456' if mode == 'live' else 'DU123456')
            def run(self): pass
            def disconnect(self): self.closed = True
            def clock_request(self): self.sent.append(49); self.w.currentTime(int(time.time()) + (600 if mode == 'clock' else 0))
            def delayed_request(self): self.sent.append(59)
            def history_request(self):
                self.sent.append(20)
                codes = dict(pacing=(162, 'Historical pacing violation SECRET_ACCOUNT'),
                             denied=(162, 'No market data permissions SECRET_ACCOUNT'),
                             empty=(162, 'query returned no data SECRET_ACCOUNT'),
                             session=(1100, 'SECRET_ACCOUNT'))
                if mode in codes:
                    code, text = codes[mode]
                    self.w.error(worker.HISTORY_ID, 0, code, text)
                    return
                if mode != 'unconfirmed': self.w.error(worker.HISTORY_ID, 0, 2188, 'SECRET_ACCOUNT')
                dates = ['20260929', '20261001', '20261002']
                if mode == 'duplicates': dates = ['20261001', '20261001']
                if mode == 'too_many': dates = ['20261001'] * 65
                if mode == 'outside': dates = ['20200101']
                if mode == 'no_bars': dates = []
                for day in dates:
                    self.w.historicalData(worker.HISTORY_ID, SimpleNamespace(date=day, open=10,
                        high=1 if mode == 'bad_ohlc' else 12, low=9, close=11, volume=100))
                self.w.historicalDataEnd(worker.HISTORY_ID, '', '')
            def cancel_history(self): self.sent.append(25)
        # The only gate override is inside this explicitly fake-client scope.
        with patch.object(transport, 'require_ibkr_archive_rights', return_value=None), \
             patch.object(worker, 'make_client', FakeClient):
            try:
                result = worker.run_history(config, request())
            finally:
                self.assertTrue(holders[0].closed)
        return result, holders[0]

    def test_advisory_succeeds_and_overfetch_is_filtered(self):
        result, client = self.simulated('ok')
        self.assertEqual(result['request_hash'], fingerprint(request()))
        self.assertEqual(result['feed'], 'DELAYED_HISTORY_ADVISORY_2188')
        self.assertEqual([bar['session'] for bar in result['bars']], ['2026-10-01', '2026-10-02'])
        self.assertEqual(client.sent, [49, 59, 20])
        self.assertFalse(result['metadata']['full_coverage_guaranteed'])
        self.assertNotIn('SECRET_ACCOUNT', json.dumps(result))

    def test_absent_advisory_never_claims_delayed_or_live(self):
        result, _ = self.simulated('unconfirmed')
        self.assertEqual(result['feed'], 'HISTORICAL_UNCONFIRMED')

    def test_safe_failure_classification(self):
        for mode, reason in [('pacing', 'PACING_LIMIT'), ('denied', 'DATA_ENTITLEMENT_REQUIRED'),
                             ('empty', 'NO_DATA'), ('session', 'SESSION_UNAVAILABLE'),
                             ('duplicates', 'INVALID_RESPONSE'), ('too_many', 'INVALID_RESPONSE'),
                             ('outside', 'INVALID_RESPONSE'), ('bad_ohlc', 'INVALID_RESPONSE'), ('no_bars', 'NO_DATA')]:
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(transport.HistoryTransportError, reason): self.simulated(mode)

    def test_exact_account_and_clock_reject_before_data(self):
        for mode in ('live', 'clock'):
            with self.assertRaisesRegex(transport.HistoryTransportError, 'SESSION_UNAVAILABLE'):
                self.simulated(mode)


class ChildBoundaryTests(unittest.TestCase):
    def fake_process(self, data=b'', stderr=b''):
        class Process:
            def __init__(self):
                self.stdin = io.BytesIO(); self.stdout = io.BytesIO(data); self.stderr = io.BytesIO(stderr)
                self.returncode = 0; self.killed = False
            def wait(self, timeout): return self.returncode
            def kill(self): self.killed = True; self.returncode = -1
        return Process()

    def test_parent_stdout_and_stderr_share_budget(self):
        for out, err in [(b'x' * (transport.MAX_OUTPUT_BYTES + 1), b''),
                         (b'{}', b'x' * transport.MAX_OUTPUT_BYTES)]:
            process = self.fake_process(out, err)
            with patch.object(transport.subprocess, 'Popen', return_value=process):
                with self.assertRaisesRegex(transport.HistoryTransportError, 'INVALID_RESPONSE'):
                    transport.bounded_child(b'{}')
            self.assertTrue(process.killed)

    def test_parent_process_deadline_kills(self):
        process = self.fake_process()
        calls = []
        def wait(timeout):
            calls.append(timeout)
            if len(calls) == 1: raise subprocess.TimeoutExpired('worker', timeout)
            return -1
        process.wait = wait
        with patch.object(transport.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(transport.HistoryTransportError, 'PROVIDER_TIMEOUT'):
                transport.bounded_child(b'{}')
        self.assertEqual(calls, [70, 3])
        self.assertTrue(process.killed)

    def test_parent_invalid_json_safe(self):
        process = self.fake_process(b'SECRET_ACCOUNT')
        with patch.object(transport.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(transport.HistoryTransportError, 'INVALID_RESPONSE'):
                transport.bounded_child(b'{}')


if __name__ == '__main__':
    unittest.main()
