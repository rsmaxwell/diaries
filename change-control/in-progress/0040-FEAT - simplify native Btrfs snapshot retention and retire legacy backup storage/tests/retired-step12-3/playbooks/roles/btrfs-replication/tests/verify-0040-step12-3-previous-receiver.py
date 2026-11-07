#!/usr/bin/env python3
"""Offline receiver previous acknowledgement contract tests."""
import importlib.util
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import Mock, patch
BASE = Path(__file__).resolve().parents[1] / 'files'
spec=importlib.util.spec_from_file_location('receiver_prev', BASE/'btrfs-agreed-parent-previous-ack.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
PROMOTED={'schema':1,'established':B,'pending':None,'previous':A}
CLEARED=dict(PROMOTED,previous=None)
class Tests(TestCase):
    def setup(self, start=PROMOTED, committed=True):
        data={'value':dict(start)}
        state=Mock()
        state.load.side_effect=lambda *a,**kw:dict(data['value'])
        state.save.side_effect=lambda path,v,**kw:data.update(value=v)
        state.acknowledge_previous.side_effect=lambda v:dict(v,previous=None)
        receiver=type('Receiver', (), {'_lock': staticmethod(lambda stack,path:None)})()
        entry=Mock();entry._receipt_locked.return_value={'receipt_committed':committed}
        return data,{'receiver':receiver,'state':state,'receipt':entry}
    def test_receiver_first_acknowledges(self):
        data,d=self.setup()
        with patch.object(m, '_load', return_value=Mock()):
            self.assertEqual(m.acknowledge(A,B,dependencies=d),CLEARED)
        self.assertEqual(data['value'],CLEARED)
        d['state'].save.assert_called_once()
    def test_retry_does_not_rewrite(self):
        data,d=self.setup(start=CLEARED)
        with patch.object(m,'_load',return_value=Mock()):
            self.assertEqual(m.acknowledge(A,B,dependencies=d),CLEARED)
        d['state'].save.assert_not_called()
    def test_missing_receipt_refuses(self):
        data,d=self.setup(committed=False)
        with patch.object(m,'_load',return_value=Mock()):
            with self.assertRaises(RuntimeError):m.acknowledge(A,B,dependencies=d)
        d['state'].save.assert_not_called()
    def test_state_mismatch_refuses(self):
        data,d=self.setup(start=dict(PROMOTED,pending=A))
        with patch.object(m,'_load',return_value=Mock()):
            with self.assertRaises(RuntimeError):m.acknowledge(A,B,dependencies=d)
        d['state'].save.assert_not_called()
if __name__=='__main__':main(verbosity=2)
