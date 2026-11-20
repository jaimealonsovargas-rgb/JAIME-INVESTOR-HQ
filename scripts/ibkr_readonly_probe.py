"""Bounded optional SDK probe. No database, prices, orders, balances or positions.

Parent runs in JAIME's environment for StorageGovernor; worker in the isolated SDK
environment. Account IDs stay in memory and are compared to a private local hash.
"""
import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.ibkr_probe_policy import PILOT, validate_probe_config, matches_paper_account, classify_contracts

# Fixed wire-level allowlist: start API, current time, current contract details.
# Managed-account identification arrives with the initial session; no request needed.
ALLOWED_MESSAGES = frozenset({71, 49, 9})


def make_client(wrapper):
    from ibapi.client import EClient
    from ibapi.common import PROTOBUF_MSG_ID

    class ReadOnlyClient(EClient):
        def __init__(self):
            super().__init__(wrapper)
            self.sent = []

        def sendMsg(self, msgId, msg):
            if msgId not in ALLOWED_MESSAGES:
                raise PermissionError('IBKR_MESSAGE_NOT_ALLOWED')
            self.sent.append(msgId)
            return super().sendMsg(msgId, msg)

        def sendMsgProtoBuf(self, msgId, msg):
            if msgId - PROTOBUF_MSG_ID not in ALLOWED_MESSAGES:
                raise PermissionError('IBKR_MESSAGE_NOT_ALLOWED')
            self.sent.append(msgId - PROTOBUF_MSG_ID)
            return super().sendMsgProtoBuf(msgId, msg)

    return ReadOnlyClient()


def run_probe(config, include_contracts=False):
    validate_probe_config(config)
    from importlib.metadata import version
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    if version('ibapi') != '1052.1' or version('protobuf') != '7.36.2':
        raise ValueError('SDK_VERSION_NOT_REVIEWED')
    logging.disable(logging.CRITICAL)  # SDK logs may include raw account identifiers.
    report = dict(version='ibkr-readonly-probe-v1', state='NOT_CONNECTED',
        checked_at=datetime.now(timezone.utc).isoformat(), python=sys.version.split()[0],
        sdk=version('ibapi'), protobuf=version('protobuf'), connected=False,
        paper_account_matched=False, read_only_basis='TWS_UI_CONFIRMED_BY_USER',
        orders_enabled=False, market_data_requested=False, contracts=[], errors=[])
    handshake, account, clock = threading.Event(), threading.Event(), threading.Event()
    finished = {}
    results = {}
    fatal = threading.Event()

    class Observer(EWrapper):
        def nextValidId(self, orderId):
            handshake.set()  # Do not store or use the order ID.

        def managedAccounts(self, accountsList):
            report['paper_account_matched'] = matches_paper_account(
                accountsList, config['paper_account_sha256'])
            if not report['paper_account_matched']:
                fatal.set()
            account.set()

        def currentTime(self, epoch):
            report['server_time_utc'] = datetime.fromtimestamp(epoch, timezone.utc).isoformat()
            clock.set()

        def error(self, reqId, errorTime, errorCode, errorString, advancedOrderRejectJson=''):
            # Keep codes only: provider text can contain private data.
            if len(report['errors']) < 50:
                report['errors'].append(dict(request_id=reqId, code=errorCode))
            if reqId in finished:
                results[reqId]['error_codes'].append(errorCode)
                finished[reqId].set()
            elif errorCode in (502, 504, 1100, 1300, 326):
                fatal.set()

        def contractDetails(self, reqId, details):
            if reqId not in results:
                return
            values = results[reqId]['candidates']
            if len(values) >= 10:
                results[reqId]['error_codes'].append(-1)
                finished[reqId].set()
                return
            c = details.contract
            values.append({k: getattr(c, k) for k in
                ('conId','symbol','secType','currency','exchange','primaryExchange',
                 'localSymbol','tradingClass')})
            values[-1]['longName'] = details.longName[:200]

        def contractDetailsEnd(self, reqId):
            if reqId in results:
                results[reqId]['completed'] = True
                finished[reqId].set()

    client = make_client(Observer())
    deadline = time.monotonic() + 40

    def wait(event):
        end = min(deadline, time.monotonic() + 8)
        while not event.is_set() and not fatal.is_set() and time.monotonic() < end:
            event.wait(min(.1, max(0, end - time.monotonic())))
        return event.is_set() and not fatal.is_set()

    def loop():
        try:
            client.connect('127.0.0.1', 7497, clientId=27)
            client.run()
        except Exception as exc:
            report['transport_error_type'] = type(exc).__name__
            fatal.set()

    socket.setdefaulttimeout(3)
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    try:
        if not wait(handshake) or not wait(account):
            report['state'] = ('ACCOUNT_REJECTED' if account.is_set()
                               and not report['paper_account_matched'] else 'SESSION_NOT_VERIFIED')
            return report
        if not report['paper_account_matched']:
            report['state'] = 'ACCOUNT_REJECTED'
            return report
        report['connected'] = True
        report['server_version'] = client.serverVersion()
        client.reqCurrentTime()
        if not wait(clock):
            report['state'] = 'CLOCK_NOT_VERIFIED'
            return report
        report['state'] = 'CONNECTED_READ_ONLY_PROBE'
        if include_contracts:
            for request_id, symbol in enumerate(PILOT, 101):
                if fatal.is_set() or not report['paper_account_matched']:
                    report['state'] = 'SESSION_LOST'
                    break
                result = dict(symbol=symbol, candidates=[], completed=False, error_codes=[])
                results[request_id] = result
                finished[request_id] = threading.Event()
                contract = Contract()
                contract.symbol, contract.secType, contract.exchange = symbol, 'STK', 'SMART'
                contract.currency = 'USD'  # Search constraint, not inferred currency evidence.
                client.reqContractDetails(request_id, contract)
                wait(finished[request_id])
                result['state'] = classify_contracts(symbol, result['candidates'],
                                                     result['completed'], result['error_codes'])
                report['contracts'].append(result)
                if not result['completed'] or result['error_codes']:
                    report['state'] = 'CONTRACTS_PARTIAL'
                    break
            if any(c['state'] != 'CURRENT_CONTRACT_CANDIDATE' for c in report['contracts']):
                report['state'] = 'CONTRACTS_PARTIAL'
        return report
    finally:
        client.disconnect()
        thread.join(timeout=2)
        report['sent_message_ids'] = list(client.sent)
        report['disconnected_after_probe'] = not client.isConnected()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--contracts', action='store_true')
    parser.add_argument('--output')
    args = parser.parse_args()
    config = json.loads((ROOT/'.tools/ibkr/pilot.json').read_text(encoding='utf-8'))
    validate_probe_config(config)
    if args.worker:
        try:
            report = run_probe(config, args.contracts)
        except Exception as exc:
            report = dict(state='PROBE_FAILED', error_type=type(exc).__name__, orders_enabled=False)
        print(json.dumps(report, ensure_ascii=True))
        return
    if not args.output:
        parser.error('--output requiere un archivo nuevo dentro de output/')
    target = Path(args.output).resolve()
    if not target.is_relative_to((ROOT/'output').resolve()) or target.exists():
        parser.error('Destino debe ser nuevo y privado dentro de output/')
    from app.storage_budget import StorageGovernor, MIB
    from app.config import Settings
    from sqlalchemy.engine import make_url
    data_root = Path(make_url(Settings().database_url).database).resolve().parent
    with StorageGovernor(data_root, ROOT/'output').admission(reserve=MIB, destination='output'):
        command = [str(ROOT/'.tools/ibkr/venv/Scripts/python.exe'), '-B', str(Path(__file__)), '--worker']
        if args.contracts:
            command.append('--contracts')
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=50)
            if result.returncode != 0 or len(result.stdout) > MIB:
                report = dict(state='WORKER_FAILED', returncode=result.returncode, orders_enabled=False)
            else:
                report = json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            report = dict(state='PROBE_TIMEOUT', orders_enabled=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()
