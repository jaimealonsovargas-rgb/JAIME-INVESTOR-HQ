"""D1: one history request and one non-regulatory snapshot, metadata only.

Parent: existing backend environment, StorageGovernor, 70 s process deadline.
Worker: isolated reviewed SDK, exact Paper hash, bounded wire and command budget.
No SQLite imports in the worker, no persistent quotes/bars or broker operations.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib.metadata import version
import json
import logging
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app.ibkr_probe_policy import validate_probe_config, matches_paper_account
from app.ibkr_data_policy import (CONTRACT, ALLOWED_MESSAGES, MAX_WIRE_BYTES, MAX_REPORT_BYTES,
    MAX_BARS, HISTORY_ID, QUOTE_ID, FATAL_CODES, INFO_CODES, end_time, safe_error, price,
    bar_metadata, classify_history, classify_quote)


def make_client(wrapper):
    from ibapi.client import EClient
    from ibapi.common import PROTOBUF_MSG_ID
    from ibapi.contract import Contract

    class DataProbeClient(EClient):
        def __init__(self):
            super().__init__(wrapper)
            self.sent = []
            self.verified = False
            self.scope = threading.local()

        @contextmanager
        def _command(self, ident):
            if ident not in ALLOWED_MESSAGES or (ident != 71 and not self.verified):
                raise PermissionError('IBKR_COMMAND_BLOCKED')
            if getattr(self.scope, 'ident', None) is not None:
                raise PermissionError('NESTED_COMMAND_BLOCKED')
            self.scope.ident = ident
            try:
                yield
            finally:
                self.scope.ident = None

        def _check(self, ident):
            if ident not in ALLOWED_MESSAGES or ident != getattr(self.scope,'ident',None):
                raise PermissionError('IBKR_MESSAGE_BLOCKED')
            if ident in self.sent:
                raise PermissionError('IBKR_REQUEST_BUDGET_EXCEEDED')
            self.sent.append(ident)

        def sendMsg(self, ident, message):
            self._check(ident)
            return super().sendMsg(ident, message)

        def sendMsgProtoBuf(self, ident, message):
            self._check(ident-PROTOBUF_MSG_ID)
            return super().sendMsgProtoBuf(ident, message)

        def startApi(self):
            with self._command(71): super().startApi()

        def clock_request(self):
            with self._command(49): self.reqCurrentTime()

        def delayed_request(self):
            with self._command(59): self.reqMarketDataType(3)

        @staticmethod
        def contract():
            value = Contract()
            for key, item in CONTRACT.items(): setattr(value,key,item)
            return value

        def history_request(self, end):
            if end != end_time(datetime.now(timezone.utc)):
                raise ValueError('CURRENT_COMPLETED_WINDOW_REQUIRED')
            with self._command(20):
                self.reqHistoricalData(HISTORY_ID, self.contract(), end.strftime('%Y%m%d %H:%M:%S UTC'),
                                       '5 D', '1 day', 'TRADES', 1, 1, False, [])

        def quote_request(self):
            with self._command(1):
                self.reqMktData(QUOTE_ID, self.contract(), '', True, False, [])

        def cancel_history(self):
            with self._command(25): self.cancelHistoricalData(HISTORY_ID)

        def cancel_quote(self):
            with self._command(2): self.cancelMktData(QUOTE_ID)

    return DataProbeClient()


def bounded_connection(base, fatal, report):
    class BoundedConnection(base):
        def _recvAllMsg(self):
            # The SDK reassembles partial frames. Never collect an unbounded burst.
            chunk = self.socket.recv(4096)
            report['wire_bytes_received'] += len(chunk)
            if report['wire_bytes_received'] > MAX_WIRE_BYTES:
                report['wire_limit_exceeded'] = True
                fatal.set()
                self.disconnect()
                return b''
            return chunk
    return BoundedConnection


def run_probe(config):
    validate_probe_config(config)
    if version('ibapi') != '1052.1' or version('protobuf') != '7.36.2':
        raise ValueError('SDK_VERSION_NOT_REVIEWED')
    from ibapi.wrapper import EWrapper
    import ibapi.client as sdk_client
    logging.disable(logging.CRITICAL)
    now = datetime.now(timezone.utc)
    end = end_time(now)
    report = dict(version='ibkr-data-probe-v1', checked_at=now.isoformat(), state='NOT_CONNECTED',
        sdk=version('ibapi'), connected=False, paper_account_matched=False, orders_enabled=False,
        read_only_basis='EXISTING_TWS_UI_CONFIRMATION_AND_WIRE_GUARD', contract=CONTRACT,
        raw_market_values_persisted=False, database_writes=0, execution_ready=False,
        rights=dict(scope='PRIVATE_ACCESS_DIAGNOSIS', archive='NOT_ENABLED_RIGHTS_PENDING',
                    redistribution=False, backtest='BLOCKED'),
        cost_controls=dict(regulatory_snapshot=False, subscriptions_purchased=False, requested_feed=3),
        wire_bytes_received=0, wire_limit_exceeded=False, errors=[],
        history=dict(requested=False, request_id=HISTORY_ID, end_utc=end.isoformat(), duration='5 D',
            bar_size='1 day', what_to_show='TRADES', use_rth=True, keep_up_to_date=False,
            currency='USD', adjustments='SPLITS_NOT_DIVIDENDS_DOCUMENTED',
            date_semantics='SESSION_LABEL_NOT_PUBLICATION_TIMESTAMP', calendar_validation='PENDING_D3',
            duration_semantics='PROVIDER_DAILY_SESSIONS_14_CALENDAR_DAY_SAFETY_BOUND',
            feed_type='NOT_REPORTED_BY_HISTORICAL_CALLBACK', completed=False,
            session_dates=[], quality_errors=[], errors=[], advisories=[]),
        quote=dict(requested=False, request_id=QUOTE_ID, snapshot=True, regulatory_snapshot=False,
            requested_feed=3, observed_feed=None, valid_tick_types=[], market_timestamp=None,
            received_at=None, completed=False, errors=[]))
    handshake, account, clock, history_done, quote_done, fatal = [threading.Event() for _ in range(6)]
    hist, quote = report['history'], report['quote']
    callbacks = 0

    class Observer(EWrapper):
        def nextValidId(self, orderId): handshake.set()

        def managedAccounts(self, accountsList):
            report['paper_account_matched'] = matches_paper_account(accountsList, config['paper_account_sha256'])
            if not report['paper_account_matched']: fatal.set()
            account.set()

        def currentTime(self, epoch):
            report['server_time_utc'] = datetime.fromtimestamp(epoch,timezone.utc).isoformat()
            if abs(epoch-time.time()) > 120:
                report['clock_skew_rejected'] = True
                fatal.set()
            clock.set()

        def error(self, reqId, errorTime, errorCode, errorString, advancedOrderRejectJson=''):
            item = dict(request_id=reqId, code=errorCode, reason=safe_error(errorCode,errorString))
            if len(report['errors']) < 32: report['errors'].append(item)
            else: fatal.set()
            if errorCode in FATAL_CODES: fatal.set()
            if reqId == HISTORY_ID and errorCode == 2188:
                hist['advisories'].append(item)
                hist['feed_type'] = 'DELAYED_HISTORY_ADVISORY_2188'
                return  # A documented advisory may precede a valid historical response.
            if reqId == HISTORY_ID and errorCode not in INFO_CODES:
                hist['errors'].append(item); history_done.set()
            if reqId == QUOTE_ID and errorCode not in INFO_CODES:
                quote['errors'].append(item)
                # 10167/10090 can accompany delayed/partial data: wait for end or deadline.
                if errorCode not in {10167,10090}: quote_done.set()

        def historicalData(self, reqId, bar):
            if reqId != HISTORY_ID or fatal.is_set(): return
            try:
                if len(hist['session_dates']) >= MAX_BARS: raise ValueError('BAR_LIMIT')
                label = bar_metadata(bar,end,hist['session_dates'][-1] if hist['session_dates'] else None)
                hist['session_dates'].append(label)
                hist['received_at'] = datetime.now(timezone.utc).isoformat()
            except ValueError as exc:
                hist['quality_errors'].append(str(exc) if str(exc) in {
                    'INVALID_SESSION_LABEL','BAR_OUTSIDE_REQUEST_WINDOW','UNORDERED_OR_DUPLICATE_BAR',
                    'INVALID_NUMBER','OHLC_INCONSISTENT','BAR_LIMIT'} else 'INVALID_BAR')
                fatal.set(); history_done.set()

        def historicalDataEnd(self, reqId, start, finish):
            if reqId == HISTORY_ID:
                hist['completed'] = True; history_done.set()

        def marketDataType(self, reqId, marketDataType):
            if reqId == QUOTE_ID: quote['observed_feed'] = marketDataType if marketDataType in {1,2,3,4} else None

        def tickPrice(self, reqId, tickType, value, attrib):
            nonlocal callbacks
            if reqId != QUOTE_ID: return
            callbacks += 1
            if callbacks > 64: fatal.set(); return
            if tickType not in {1,2,4,66,67,68}: return
            try: price(value)
            except ValueError: return  # -1 is unavailable, never a price.
            if tickType not in quote['valid_tick_types']: quote['valid_tick_types'].append(tickType)
            quote['received_at'] = datetime.now(timezone.utc).isoformat()

        def tickString(self, reqId, tickType, value):
            if reqId == QUOTE_ID and tickType in {45,88}:
                try:
                    epoch = int(value)
                    if not 0 < epoch <= time.time()+120: return
                    quote['market_timestamp'] = datetime.fromtimestamp(epoch,timezone.utc).isoformat()
                except (ValueError,OverflowError,OSError): pass

        def tickSnapshotEnd(self, reqId):
            if reqId == QUOTE_ID: quote['completed'] = True; quote_done.set()

    client = make_client(Observer())
    original_connection = sdk_client.Connection
    sdk_client.Connection = bounded_connection(original_connection, fatal, report)
    deadline = time.monotonic()+55

    def wait(event, seconds):
        until = min(deadline,time.monotonic()+seconds)
        while not event.is_set() and not fatal.is_set() and time.monotonic() < until:
            event.wait(min(.1,max(0,until-time.monotonic())))
        return event.is_set() and not fatal.is_set()

    def loop():
        try:
            client.connect('127.0.0.1',7497,clientId=27)
            client.run()
        except Exception:
            report['transport_failed'] = True; fatal.set()

    socket.setdefaulttimeout(3)
    worker = threading.Thread(target=loop,daemon=True)
    worker.start()
    try:
        if not wait(handshake,8) or not wait(account,4):
            report['state'] = 'ACCOUNT_REJECTED' if account.is_set() and not report['paper_account_matched'] else 'SESSION_NOT_VERIFIED'
        else:
            client.verified = True
            report['connected'] = True
            report['server_version'] = client.serverVersion()
            client.clock_request()
            if not wait(clock,4): report['state'] = 'CLOCK_NOT_VERIFIED'
            else:
                client.delayed_request()
                hist['requested'] = True
                client.history_request(end)
                wait(history_done,18)
                if not hist['completed'] and not fatal.is_set(): client.cancel_history()
                if not fatal.is_set():
                    quote['requested'] = True
                    client.quote_request()
                    wait(quote_done,15)
                    client.cancel_quote()
                report['state'] = 'ACCESS_DIAGNOSIS_COMPLETE' if not fatal.is_set() else 'PROBE_INTERRUPTED'
    finally:
        client.disconnect()
        worker.join(timeout=2)
        sdk_client.Connection = original_connection
        report['sent_message_ids'] = list(client.sent)
        report['disconnected_after_probe'] = not client.isConnected()
        hist['state'] = classify_history(hist['completed'],hist['session_dates'],hist['quality_errors'],hist['errors']) if hist['requested'] else 'NOT_REQUESTED'
        hist['bar_count'] = len(hist['session_dates'])
        quote['state'] = classify_quote(quote['observed_feed'],quote['valid_tick_types'],quote['completed'],quote['errors']) if quote['requested'] else 'NOT_REQUESTED'
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--output')
    args = parser.parse_args()
    config = json.loads((ROOT/'.tools/ibkr/pilot.json').read_text(encoding='utf-8'))
    validate_probe_config(config)
    if args.worker:
        try: report = run_probe(config)
        except Exception: report = dict(state='WORKER_FAILED',orders_enabled=False,raw_market_values_persisted=False)
        print(json.dumps(report,ensure_ascii=True))
        return
    if not args.output: parser.error('Archivo nuevo --output obligatorio.')
    target = Path(args.output).resolve()
    if not target.is_relative_to((ROOT/'output').resolve()) or target.exists():
        parser.error('El destino debe ser nuevo, dentro de output/.')
    from app.config import Settings
    from app.storage_budget import StorageGovernor, StorageBlocked, MIB
    from sqlalchemy.engine import make_url
    data_root = Path(make_url(Settings().database_url).database).parent
    try:
        with StorageGovernor(data_root,ROOT/'output').admission(reserve=MIB,destination='output'):
            try:
                child = subprocess.run([str(ROOT/'.tools/ibkr/venv/Scripts/python.exe'),'-B',
                                        str(Path(__file__)), '--worker'],capture_output=True,timeout=70)
                if child.returncode or len(child.stdout)>MAX_REPORT_BYTES:
                    report = dict(state='WORKER_FAILED',orders_enabled=False)
                else:
                    report = json.loads(child.stdout)
                    if not isinstance(report,dict) or 'state' not in report:
                        report = dict(state='WORKER_PROTOCOL_ERROR',orders_enabled=False)
            except subprocess.TimeoutExpired: report = dict(state='PROBE_TIMEOUT',orders_enabled=False)
            except (ValueError,OSError): report = dict(state='WORKER_FAILED',orders_enabled=False)
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('x',encoding='utf-8') as stream: json.dump(report,stream,indent=2,ensure_ascii=False)
    except StorageBlocked as exc:
        print(json.dumps(dict(state='STORAGE_'+exc.reason,market_requests=0,orders_enabled=False)))
        raise SystemExit(2) from None
    print(json.dumps(dict(state=report['state'],history=report.get('history',{}).get('state'),
                         quote=report.get('quote',{}).get('state'),orders_enabled=False)))
    if report['state'] != 'ACCESS_DIAGNOSIS_COMPLETE': raise SystemExit(2)


if __name__ == '__main__': main()
