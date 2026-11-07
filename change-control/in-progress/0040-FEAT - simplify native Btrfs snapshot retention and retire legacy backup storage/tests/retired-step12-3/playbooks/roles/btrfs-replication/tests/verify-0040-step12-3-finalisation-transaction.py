#!/usr/bin/env python3
"""Offline Step 12.3 lock-owned finalisation composition regression."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-finalisation-transaction.py'
spec = importlib.util.spec_from_file_location('finalisation_transaction', SOURCE)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class FakeFinal:
    calls = []
    def finalize_locked(self, p, c, **kw):
        self.calls.append(kw)
        assert kw['manager_lock_held'] and kw['writer_lock_held']
        assert kw['read_state']() == {'state': True}
        assert kw['read_journal']() == {'journal': True}
        assert kw['receipt_absent']('B')
        kw['commit_receipt']('B', {'snapshot':'B'})
        return {'status':'receiver-receipt-committed-promotion-pending'}

class FakeStorage:
    def read_state(self, where): return {'state':True}
    def read_journal(self, where): return {'journal':True}
    def receipt_absent(self, stamp, where): return True
    def commit_receipt(self, stamp, fields, *, directory, locks_held):
        assert locks_held and stamp == 'B'

class Test(unittest.TestCase):
    def args(self):
        return dict(finalisation=FakeFinal(), storage=FakeStorage(),
                    verify_sender_completion=lambda a,b: {},
                    inspect_received=lambda b: {}, receipt_fields={})
    def test_lock_failure_refuses(self):
        with patch.object(m, '_lock', side_effect=OSError('lock unavailable')):
            with self.assertRaisesRegex(OSError, 'lock unavailable'):
                m.finalize_transaction({}, {}, **self.args())
    def test_noncanonical_path_refused(self):
        a=self.args(); a['lock_paths']=(Path('/tmp/x'),Path('/tmp/y'))
        with self.assertRaisesRegex(m.TransactionRefused,'noncanonical'):
            m.finalize_transaction({}, {}, **a)
    def test_no_unverified_sender_verifier(self):
        a=self.args(); a['verify_sender_completion']=None
        with self.assertRaisesRegex(m.TransactionRefused,'trusted sender proof'):
            m.finalize_transaction({}, {}, **a)
    def test_only_lock_owning_finaliser_commits(self):
        a=self.args(); fake=FakeFinal()
        a['finalisation']=fake
        with patch.object(m,'_lock',side_effect=[1,2]) as lock:
            result=m.finalize_transaction({}, {}, **a)
        self.assertEqual(lock.call_count, 2)
        self.assertEqual(result['status'],'receiver-receipt-committed-promotion-pending')
        self.assertEqual(len(fake.calls),1)
    def test_absent_cli(self):
        self.assertFalse(hasattr(m,'main'))

if __name__ == '__main__': unittest.main(verbosity=2)
