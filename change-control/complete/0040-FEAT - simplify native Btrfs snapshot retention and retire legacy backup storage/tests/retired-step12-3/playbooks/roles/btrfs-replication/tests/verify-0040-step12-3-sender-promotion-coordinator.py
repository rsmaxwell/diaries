#!/usr/bin/env python3
"""Offline fault-injection gate for sender-after-receipt promotion ordering."""
import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-sender-promotion-coordinator.py'
spec = importlib.util.spec_from_file_location('promotion_coordinator_0040', p)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}
PREPARED = {'schema': 1, 'established': A, 'pending': B, 'previous': None}
PROMOTED = {'schema': 1, 'established': B, 'pending': None, 'previous': A}

class Gate(unittest.TestCase):
    def harness(self, fail=None):
        events = []
        def step(name, result):
            def call(*args):
                events.append(name)
                if name == fail: raise OSError('injected uncertainty')
                return result
            return call
        kwargs = dict(verify_source_prepared=step('source-verified', True),
                      verify_receiver_receipt=step('receipt-verified', True),
                      promote_receiver=step('receiver-promote', None),
                      read_receiver_promoted=step('receiver-read', dict(PROMOTED)),
                      promote_source=step('source-promote', None),
                      read_source_state=step('source-read', dict(PROMOTED)))
        return kwargs, events

    def test_order_and_pinned_previous(self):
        kw, events = self.harness()
        result = m.coordinate_after_receipt(A, B, **kw)
        self.assertEqual(events, ['source-verified','receipt-verified','receiver-promote',
                                  'receiver-read','source-promote','source-read'])
        self.assertFalse(result['authorizes_prune'])
        self.assertFalse(result['authorizes_release'])
        self.assertEqual(result['source_state']['previous'], A)

    def test_every_uncertain_stage_refuses(self):
        for stage in ('source-verified','receipt-verified','receiver-promote',
                      'receiver-read','source-promote','source-read'):
            with self.subTest(stage=stage):
                kw, events = self.harness(fail=stage)
                with self.assertRaises(OSError): m.coordinate_after_receipt(A, B, **kw)
                if stage in ('source-verified','receipt-verified','receiver-promote','receiver-read'):
                    self.assertNotIn('source-promote', events)

    def test_false_receipt_refuses(self):
        kw, events = self.harness()
        kw['verify_receiver_receipt'] = lambda a,b: False
        with self.assertRaises(m.PromotionRefused): m.coordinate_after_receipt(A, B, **kw)
        self.assertNotIn('receiver-promote', events)

    def test_receiver_readback_must_be_promoted(self):
        kw, events = self.harness()
        kw['read_receiver_promoted'] = lambda a,b: dict(PREPARED)
        with self.assertRaises(m.PromotionRefused): m.coordinate_after_receipt(A, B, **kw)
        self.assertNotIn('source-promote', events)

    def test_source_readback_must_be_promoted(self):
        kw, events = self.harness()
        kw['read_source_state'] = lambda a,b: dict(PREPARED)
        with self.assertRaises(m.PromotionRefused): m.coordinate_after_receipt(A, B, **kw)
        self.assertIn('source-promote', events)

    def test_no_source_advance_on_receiver_mismatch(self):
        kw, events = self.harness()
        kw['read_receiver_promoted'] = lambda a,b: dict(PROMOTED, previous=None)
        with self.assertRaises(m.PromotionRefused): m.coordinate_after_receipt(A, B, **kw)
        self.assertNotIn('source-promote', events)

    def test_reject_missing_adapter(self):
        kw, _ = self.harness(); kw['read_receiver_promoted'] = None
        with self.assertRaises(m.PromotionRefused): m.coordinate_after_receipt(A, B, **kw)

if __name__ == '__main__':
    unittest.main(verbosity=2)
