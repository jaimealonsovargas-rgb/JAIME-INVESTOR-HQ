"""SDK-specific D1 tests: no socket/network and no application database."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import json
import sys
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import ibkr_data_probe as probe
from ibapi.wrapper import EWrapper
from ibapi.client import EClient


class Sink:
    def __init__(self): self.messages=[]
    def sendMsg(self,message): self.messages.append(message)
    def isConnected(self): return True


class WireTests(unittest.TestCase):
    def setUp(self):
        self.client=probe.make_client(EWrapper())
        self.client.conn=Sink()
        self.client.connState=EClient.CONNECTED
        self.client.serverVersion_=226

    def test_no_commands_before_exact_account_match(self):
        for method in (self.client.clock_request,self.client.delayed_request,self.client.quote_request):
            with self.assertRaises(PermissionError): method()
        self.assertEqual(self.client.conn.messages,[])

    def test_both_wires_block_orders_and_unsolicited_allowed_ids(self):
        self.client.verified=True
        for ident in range(-1,401):
            with self.assertRaises(PermissionError): self.client.sendMsg(ident,'')
            with self.assertRaises(PermissionError): self.client.sendMsgProtoBuf(ident+200,b'')
        self.assertEqual(self.client.conn.messages,[])

    def test_legacy_and_protobuf_only_approved_once(self):
        for server in (100,226):
            with self.subTest(server=server):
                client=probe.make_client(EWrapper()); client.conn=Sink()
                client.connState=EClient.CONNECTED; client.serverVersion_=server; client.verified=True
                for ident in probe.ALLOWED_MESSAGES:
                    with client._command(ident):
                        if server==100: client.sendMsg(ident,'')
                        else: client.sendMsgProtoBuf(ident+200,b'')
                    with self.assertRaises(PermissionError):
                        with client._command(ident): client.sendMsg(ident,'')
                self.assertEqual(len(client.conn.messages),7)

    def test_public_requests_pin_arguments_and_never_regulatory_snapshot(self):
        self.client.verified=True
        with patch.object(EClient,'reqMktData') as request:
            self.client.quote_request()
            args=request.call_args.args
            self.assertEqual(args[0],202)
            self.assertEqual(args[1].conId,265598)
            self.assertEqual(args[2:],('',True,False,[]))
        with patch.object(EClient,'reqHistoricalData') as request:
            self.client.history_request(probe.end_time(datetime.now(timezone.utc)))
            self.assertEqual(request.call_args.args[3:],('5 D','1 day','TRADES',1,1,False,[]))
        with patch.object(EClient,'reqMarketDataType') as request:
            self.client.delayed_request(); request.assert_called_once_with(3)

    def test_real_sdk_serializes_reviewed_requests(self):
        self.client.verified=True
        self.client.clock_request(); self.client.delayed_request()
        self.client.history_request(probe.end_time(datetime.now(timezone.utc)))
        self.client.cancel_history(); self.client.quote_request(); self.client.cancel_quote()
        self.assertEqual(self.client.sent,[49,59,20,25,1,2])
        self.assertEqual(len(self.client.conn.messages),6)

    def test_receive_budget_disconnects(self):
        report=dict(wire_bytes_received=probe.MAX_WIRE_BYTES,wire_limit_exceeded=False)
        fatal=threading.Event()
        class Base:
            socket=SimpleNamespace(recv=lambda size:b'x')
            def disconnect(self): self.closed=True
        connection=probe.bounded_connection(Base,fatal,report)()
        self.assertEqual(connection._recvAllMsg(),b'')
        self.assertTrue(fatal.is_set() and connection.closed and report['wire_limit_exceeded'])


class FlowTests(unittest.TestCase):
    def simulated(self, mode):
        cfg=dict(host='127.0.0.1',port=7497,client_id=27,read_only_confirmed_in_tws=True,
                 paper_account_sha256=sha256(b'DU_TEST').hexdigest())
        # Account syntax deliberately uses only characters accepted by the existing policy.
        cfg['paper_account_sha256']=sha256(b'DU123456').hexdigest()
        holders=[]
        class FakeClient:
            def __init__(self,wrapper): self.w=wrapper; self.sent=[]; self.closed=False; holders.append(self)
            def connect(self,*args,**kwargs):
                self.w.nextValidId(1)
                self.w.managedAccounts('U123456' if mode=='live' else 'DU123456')
            def run(self): pass
            def disconnect(self): self.closed=True
            def isConnected(self): return not self.closed
            def serverVersion(self): return 226
            def clock_request(self): self.sent.append(49); self.w.currentTime(int(time.time())+(600 if mode=='clock' else 0))
            def delayed_request(self): self.sent.append(59)
            def history_request(self,end):
                self.sent.append(20)
                if mode=='denied': self.w.error(201,0,162,'No market data permissions SECRET_ACCOUNT'); return
                self.w.error(201,0,2188,'up-to-the-second data requires subscription SECRET_ACCOUNT')
                day=(end-timedelta(days=7)).strftime('%Y%m%d')
                self.w.historicalData(201,SimpleNamespace(date=day,open=10,high=12,low=9,close=11,volume=100))
                self.w.historicalDataEnd(201,'','')
            def cancel_history(self): self.sent.append(25)
            def quote_request(self):
                self.sent.append(1)
                if mode=='denied': self.w.error(202,0,354,'SECRET_ACCOUNT no subscription'); return
                self.w.marketDataType(202,3); self.w.tickPrice(202,68,11,None)
                self.w.tickSnapshotEnd(202)
            def cancel_quote(self): self.sent.append(2)
        with patch.object(probe,'make_client',FakeClient): result=probe.run_probe(cfg)
        self.assertTrue(holders[0].closed)
        return result

    def test_success_metadata_only(self):
        result=self.simulated('ok')
        self.assertEqual(result['history']['state'],'ACCESS_OBSERVED')
        self.assertEqual(result['quote']['state'],'ACCESS_OBSERVED')
        self.assertEqual(result['history']['bar_count'],1)
        self.assertEqual(result['history']['feed_type'],'DELAYED_HISTORY_ADVISORY_2188')
        self.assertEqual(result['history']['errors'],[])
        self.assertFalse(result['raw_market_values_persisted'])
        self.assertNotIn('open',result['history'])
        self.assertIsNone(result['quote']['market_timestamp'])
        self.assertEqual(result['rights']['backtest'],'BLOCKED')

    def test_permission_denial_without_sensitive_text(self):
        result=self.simulated('denied')
        self.assertEqual(result['history']['state'],'DATA_ENTITLEMENT_REQUIRED')
        self.assertEqual(result['quote']['state'],'DATA_ENTITLEMENT_REQUIRED')
        self.assertNotIn('SECRET_ACCOUNT',json.dumps(result))

    def test_live_and_clock_skew_never_request_market_data(self):
        for mode in ('live','clock'):
            result=self.simulated(mode)
            self.assertFalse(result['history']['requested'])
            self.assertFalse(result['quote']['requested'])
            self.assertNotIn(20,result['sent_message_ids'])


if __name__=='__main__': unittest.main()
