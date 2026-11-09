#!/usr/bin/env python3
"""Source-only regression for receiver promotion adapter. No host operations."""
import importlib.util
from pathlib import Path
import unittest

f = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-receiver-promotion-adapter.py'
spec = importlib.util.spec_from_file_location('promotion_adapter', f)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A = {'timestamp': '20261030-010000Z', 'uuid': '11111111-1111-1111-1111-111111111111'}
B = {'timestamp': '20261031-010000Z', 'uuid': '22222222-2222-2222-2222-222222222222'}
STATE = {'schema': 1, 'established': B, 'pending': None, 'previous': A}
def ack():
    return {'schema': 1, 'status': 'receiver-promoted-previous-pinned',
            'parent': A, 'candidate': B, 'receipt_committed': True,
            'state': STATE, 'authorizes_prune': False, 'authorizes_release': False}

class Gate(unittest.TestCase):
    def test_success_requires_separate_read(self):
        calls = []
        def promote(a,b):
            calls.append('promote')
            return ack()
        def read(a,b):
            calls.append('read')
            return STATE.copy()
        self.assertEqual(m.promote_and_readback(A,B,promote_fixed=promote,read_locked_state=read), STATE)
        self.assertEqual(calls, ['promote', 'read'])
    def test_ack_cannot_substitute_for_readback(self):
        with self.assertRaises(m.PromotionAdapterRefused):
            m.promote_and_readback(A,B,promote_fixed=lambda a,b: ack(),
                read_locked_state=lambda a,b: {'schema':1,'established':A,'pending':B,'previous':None})
    def test_receipt_required(self):
        bad=ack(); bad['receipt_committed']=False
        with self.assertRaises(m.PromotionAdapterRefused):
            m.promote_and_readback(A,B,promote_fixed=lambda a,b:bad,read_locked_state=lambda a,b:STATE)
    def test_no_release(self):
        bad=ack(); bad['authorizes_release']=True
        with self.assertRaises(m.PromotionAdapterRefused):
            m.promote_and_readback(A,B,promote_fixed=lambda a,b:bad,read_locked_state=lambda a,b:STATE)
    def test_uncertainty_fails_closed(self):
        def uncertain(a,b): raise OSError('lost ack')
        with self.assertRaises(m.PromotionAdapterRefused):
            m.promote_and_readback(A,B,promote_fixed=uncertain,read_locked_state=lambda a,b:STATE)
    def test_invalid_identity_refused_before_calls(self):
        with self.assertRaises(m.PromotionAdapterRefused):
            m.promote_and_readback(B,A,promote_fixed=lambda a,b:self.fail('called'),
                                  read_locked_state=lambda a,b:self.fail('called'))
    def test_read_failure_refused(self):
        def fail(a,b): raise OSError('read failed')
        with self.assertRaises(m.PromotionAdapterRefused):
            m.promote_and_readback(A,B,promote_fixed=lambda a,b:ack(),read_locked_state=fail)

if __name__ == '__main__': unittest.main(verbosity=2)
