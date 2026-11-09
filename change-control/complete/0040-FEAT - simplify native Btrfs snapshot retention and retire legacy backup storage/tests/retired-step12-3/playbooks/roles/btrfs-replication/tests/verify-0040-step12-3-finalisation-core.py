#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

src = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-finalisation-core.py'
spec = importlib.util.spec_from_file_location('finalisation', src)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}

NONCE='a'*64

class Tests(unittest.TestCase):
    def setUp(self):
        self.calls=[]
        self.state={'schema':1,'established':A,'pending':B,'previous':None}
        self.journal={'schema':1,'status':'receiving','parent':A,'candidate':B,'nonce':NONCE}
        self.proof={'authenticated_session':True,'source_send_exit':0,'ssh_exit':0,'receiver_receive_exit':0,'parent':A,'candidate':B}
        self.receipt={'schema':1,'snapshot':B['timestamp'],'source_uuid':B['uuid'],
                      'received_uuid':B['uuid'],'parent_snapshot':A['timestamp'],
                      'parent_source_uuid':A['uuid'],'transport':'btrfs-incremental',
                      'read_only_verified':True,'source_send_exit':0,'receiver_receive_exit':0}
        self.kw=dict(read_state=lambda:self.state,read_journal=lambda:self.journal,
                     verify_source_completion=lambda a,b,nonce:self.proof if nonce == NONCE else None,
                     inspect_received=lambda s:{'uuid':'receiver-b','flags':'readonly','received_uuid':B['uuid']},
                     receipt_absent=lambda s:True,
                     commit_receipt=lambda s,r:self.calls.append((s,r)),
                     receipt_fields=self.receipt,manager_lock_held=True,writer_lock_held=True)
    def go(self, **changes):
        return m.finalize_locked(A,B,**(self.kw|changes))
    def test_success_is_receipt_only(self):
        result=self.go()
        self.assertEqual(len(self.calls),1)
        self.assertTrue(result['journal_retained'])
        for name in ('state_changed','authorizes_transition','authorizes_prune','authorizes_release'):
            self.assertIs(result[name],False)
    def test_missing_lock_blocks_commit(self):
        with self.assertRaises(m.FinalisationRefused): self.go(writer_lock_held=False)
        self.assertFalse(self.calls)
    def test_wrong_state_blocks_commit(self):
        self.state['pending']=None
        with self.assertRaises(m.FinalisationRefused): self.go()
        self.assertFalse(self.calls)
    def test_nonce_mismatch_blocks_commit(self):
        self.journal['nonce']='b'*64
        with self.assertRaises(m.FinalisationRefused): self.go()
        self.assertFalse(self.calls)
    def test_missing_nonce_blocks_commit(self):
        del self.journal['nonce']
        with self.assertRaises(m.FinalisationRefused): self.go()
        self.assertFalse(self.calls)
    def test_wrong_journal_blocks_commit(self):
        self.journal['candidate']=A
        with self.assertRaises(m.FinalisationRefused): self.go()
        self.assertFalse(self.calls)
    def test_unproven_source_exit_blocks_commit(self):
        self.proof['ssh_exit']=255
        with self.assertRaises(m.FinalisationRefused): self.go()
        self.assertFalse(self.calls)
    def test_unverified_received_uuid_blocks_commit(self):
        with self.assertRaises(m.FinalisationRefused): self.go(inspect_received=lambda s:{'uuid':'b','flags':'readonly','received_uuid':A['uuid']})
        self.assertFalse(self.calls)
    def test_existing_receipt_blocks_commit(self):
        with self.assertRaises(m.FinalisationRefused): self.go(receipt_absent=lambda s:False)
        self.assertFalse(self.calls)
    def test_uncertain_commit_requires_reconciliation(self):
        def fail(s,r): raise OSError('disk failure')
        with self.assertRaisesRegex(m.FinalisationRefused,'manual reconciliation'):
            self.go(commit_receipt=fail)
    def test_no_cli_and_no_filesystem_mutation(self):
        source=src.read_text()
        self.assertNotIn('def main(',source)
        self.assertNotIn('os.unlink(',source)
        self.assertNotIn('subprocess.',source)

if __name__=='__main__': unittest.main(verbosity=2)
