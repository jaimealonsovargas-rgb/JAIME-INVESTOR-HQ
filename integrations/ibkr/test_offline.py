"""Run with .tools/ibkr/venv/Scripts/python.exe; never opens a socket."""
from importlib.metadata import version
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from ibkr_readonly_probe import make_client
from ibapi.wrapper import EWrapper


class Sink:
    def __init__(self):
        self.messages = []

    def sendMsg(self, msg):
        self.messages.append(msg)


class WireGuardTest(unittest.TestCase):
    def setUp(self):
        self.client = make_client(EWrapper())
        self.client.conn = Sink()
        self.client.serverVersion_ = 100

    def test_reviewed_versions_import(self):
        self.assertEqual(version('ibapi'), '1052.1')
        self.assertEqual(version('protobuf'), '7.36.2')

    def test_only_clock_contract_and_start_messages(self):
        for ident in (9, 49, 71):
            self.client.sendMsg(ident, '')
            self.client.sendMsgProtoBuf(ident + 200, b'')
        self.assertEqual(len(self.client.conn.messages), 6)

    def test_orders_prices_unknown_and_future_ids_blocked(self):
        for ident in range(-1, 401):
            if ident in (9, 49, 71):
                continue
            with self.subTest(ident=ident):
                with self.assertRaises(PermissionError):
                    self.client.sendMsg(ident, '')
                with self.assertRaises(PermissionError):
                    self.client.sendMsgProtoBuf(ident + 200, b'')
        self.assertEqual(self.client.conn.messages, [])


if __name__ == '__main__':
    unittest.main()
