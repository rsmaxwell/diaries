#!/usr/bin/env python3
"""Offline regression for opt-in journal-bound staging. No Btrfs mutations."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent.parent / 'files' / 'btrfs-agreed-parent-receive-core.py'
spec = importlib.util.spec_from_file_location('core', SOURCE)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
P={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
C={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
NONCE='a'*64

class Journal:
    def __init__(self): self.bound=[]
    def reserve(self, directory, parent, candidate, **kw):
        path=Path(directory)/'.pending.json'
        path.write_text(json.dumps({'nonce':NONCE,'scope_unit':'btrfs-agreed-receive-'+C['timestamp']+'-'+NONCE[:16]+'.scope','scope_binding':'reserved-not-termination-evidence'}))
        return path
    def bind_staging(self, path, candidate, nonce, identity, **kw):
        self.bound.append((path, candidate, nonce, identity, kw))

class Storage:
    def __init__(self):self.calls=[]
    def reserve(self, stamp, nonce, **kw):
        self.calls.append((stamp,nonce,kw))
        return {'directory_dev':123, 'directory_ino':456}

class Cases(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.a=self.root/'manager.lock'; self.b=self.root/'writer.lock'
        self.a.touch(); self.b.touch(); self.journal=Journal(); self.storage=Storage();self.seen=[]
    def run_txn(self, **kwargs):
        def receive(p,c,**kw):
            self.seen.append(kw)
            return True
        return core.receive_prepared_candidate_reserved(P,C,manager_lock=self.a,writer_lock=self.b,
            state_dir=self.root, verify_prepared=lambda *_:True, receive_stream=receive,
            journal_module=self.journal, **kwargs)
    def test_staged_reserves_and_binds_before_stream(self):
        result=self.run_txn(staged=True, scoped=True, staging_storage=self.storage)
        self.assertEqual(self.storage.calls,[(C['timestamp'],NONCE,{'locks_held':True})])
        self.assertEqual(len(self.journal.bound),1)
        self.assertEqual(self.journal.bound[0][2], NONCE)
        self.assertEqual(self.journal.bound[0][4],{'manager_lock_held':True,'writer_lock_held':True})
        self.assertEqual(self.seen[0]['staging_nonce'],NONCE)
        self.assertFalse(result['receipt_committed'])
    def test_staging_fails_closed_without_scoped(self):
        with self.assertRaisesRegex(RuntimeError,'Staged receive requires scoped'):
            self.run_txn(staged=True, staging_storage=self.storage)
        self.assertEqual(self.storage.calls,[])
        self.assertEqual(self.seen,[])
    def test_default_does_not_reserve_staging(self):
        result=self.run_txn()
        self.assertEqual(self.storage.calls,[])
        self.assertEqual(self.journal.bound,[])
        self.assertNotIn('staging_nonce',self.seen[0])
        self.assertFalse(result['staged'])
    def test_staged_runner_requires_real_scope_and_locks(self):
        with self.assertRaisesRegex(RuntimeError,'Staged receive requires real'):
            core.receive_prepared_binary_stream(P,C,input_stream=__import__('io').BytesIO(),
                runner=lambda *a,**kw:None,staging_nonce=NONCE)
    def test_bad_nonce_refused(self):
        with self.assertRaisesRegex(RuntimeError,'Invalid staged transaction nonce'):
            core.receive_prepared_binary_stream(P,C,input_stream=__import__('io').BytesIO(),
                staging_nonce='../bad')

if __name__=='__main__':unittest.main(verbosity=2)
