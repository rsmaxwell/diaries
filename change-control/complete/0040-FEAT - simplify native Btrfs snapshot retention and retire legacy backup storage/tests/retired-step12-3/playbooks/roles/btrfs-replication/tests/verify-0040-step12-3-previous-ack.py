#!/usr/bin/env python3
"""Offline regression for explicit receiver-first previous-parent acknowledgement."""
import importlib.util
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import Mock
import json

BASE = Path(__file__).resolve().parents[1] / 'files'
p = BASE / 'btrfs-agreed-parent-sender-previous-ack.py'
spec = importlib.util.spec_from_file_location('ack', p)
ack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ack)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}
PROMOTED = {'schema': 1, 'established': B, 'pending': None, 'previous': A}
CLEARED = dict(PROMOTED, previous=None)

class Context:
    def __init__(self, *, already_clear=False, receipt_ok=True):
        self.data = dict(PROMOTED)
        self.commands = Mock()
        self.commands.previous_readback_command.return_value = ['readback']
        self.commands.acknowledge_previous_command.return_value = ['acknowledge']
        self.observer = Mock()
        self.observer.lock.side_effect = lambda stack, path: None
        self.state = Mock()
        self.state.load.side_effect = lambda *args, **kw: dict(self.data)
        self.state.save.side_effect = lambda path, value, **kw: setattr(self, 'data', value)
        self.state.acknowledge_previous.side_effect = lambda current: dict(current, previous=None)
        self.evidence = Mock()
        self.evidence.verify_source.side_effect = lambda x: dict(x, verified=True)
        self.receipt = Mock(return_value=receipt_ok)
        self.promotion = Mock()
        self.promotion.receiver_readback.return_value = dict(PROMOTED)
        self.already_clear = already_clear
        self.calls = []
    def remote(self, cmd, **kw):
        self.calls.append(cmd[0])
        if cmd[0] == 'readback' and not (self.already_clear or 'acknowledge' in self.calls):
            return Mock(returncode=1, stdout=b'', stderr=b'receiver not clear')
        return Mock(returncode=0, stdout=json.dumps(CLEARED).encode(), stderr=b'')
    def run(self):
        return ack.run(observer=self.observer, state=self.state, evidence=self.evidence,
                       receipt=self.receipt, promotion=self.promotion,
                       commands=self.commands, run_ssh=self.remote)

class Tests(TestCase):
    def test_receiver_first_then_sender(self):
        c = Context(); out=c.run()
        self.assertEqual(out['source_state'], CLEARED)
        self.assertEqual(c.calls, ['readback', 'acknowledge', 'readback'])
        self.state_check(c)
    def test_recover_receiver_already_clear(self):
        c = Context(already_clear=True); out=c.run()
        self.assertEqual(out['receiver_state'], CLEARED)
        self.assertEqual(c.calls, ['readback', 'readback'])
        c.promotion.receiver_readback.assert_not_called()
    def test_missing_receipt_refuses(self):
        c = Context(receipt_ok=False)
        with self.assertRaises(ack.PreviousAckRefused): c.run()
        c.state.save.assert_not_called()
    def test_bad_receiver_response_refuses_without_source_write(self):
        c = Context(); c.promotion.receiver_readback.return_value = {'error': True}
        with self.assertRaises(ack.PreviousAckRefused): c.run()
        c.state.save.assert_not_called()
    def state_check(self, c):
        c.state.save.assert_called_once()

if __name__ == '__main__': main(verbosity=2)
