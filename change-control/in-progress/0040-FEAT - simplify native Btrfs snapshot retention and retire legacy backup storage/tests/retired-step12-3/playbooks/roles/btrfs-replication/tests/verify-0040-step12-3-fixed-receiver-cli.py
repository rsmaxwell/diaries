#!/usr/bin/env python3
"""Source-level CLI integration, no live Btrfs and no production state."""
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from contextlib import redirect_stdout
import sys

FILE=Path(__file__).resolve().parents[1]/'files'/'btrfs-agreed-parent-receiver-entry.py'
spec=importlib.util.spec_from_file_location('fixed_receiver_cli',FILE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
class T(unittest.TestCase):
    def setUp(self):
        self.loaded=[];self.calls=[]
    def loader(self,name):
        self.loaded.append(name)
        if name=='receive-core':
            return SimpleNamespace(inspect=lambda s:{},receive_prepared_candidate_integrated=self.core)
        return SimpleNamespace()
    def core(self,a,b,**kw):
        self.calls.append((a,b,kw))
        return dict(status='receiver-provisional-only',receipt_committed=False,
                    transfer_finalized=False,authorizes_transition=False,
                    authorizes_prune=False,authorizes_release=False)
    def test_nonroot_refused_before_import(self):
        with patch.object(m.os,'geteuid',return_value=1000):
            with self.assertRaisesRegex(RuntimeError,'root'):m.receive_fixed(A,B,input_stream=io.BytesIO(),loader=self.loader)
        self.assertFalse(self.loaded)
    def test_missing_stream_refused(self):
        with patch.object(m.os,'geteuid',return_value=0):
            with self.assertRaisesRegex(RuntimeError,'stream'):m.receive_fixed(A,B,input_stream=None,loader=self.loader)
        self.assertFalse(self.loaded)
    def test_fixed_deps_and_one_lock_owner(self):
        with patch.object(m.os,'geteuid',return_value=0):
            result=m.receive_fixed(A,B,input_stream=io.BytesIO(b'data'),loader=self.loader)
        self.assertEqual(len(self.calls),1)
        self.assertEqual(self.calls[0][2]['manager_lock'],m.MANAGER)
        self.assertEqual(self.calls[0][2]['writer_lock'],m.WRITER)
        self.assertTrue(callable(self.calls[0][2]['runner']))
        self.assertEqual(set(self.loaded),{'receive-core','state','transfer-absence','endpoint','provisional-journal','transfer-attestation'})
        self.assertFalse(result['receipt_committed'])
    def test_unsafe_result_refused(self):
        def bad(*args,**kwargs):return dict(status='receiver-provisional-only',receipt_committed=True)
        self.core=bad
        with patch.object(m.os,'geteuid',return_value=0):
            with self.assertRaisesRegex(RuntimeError,'unsafe'):m.receive_fixed(A,B,input_stream=io.BytesIO(),loader=self.loader)
    def test_no_prune_cli(self):
        source=FILE.read_text()
        self.assertIn("add_argument('--promote'",source)
        self.assertIn("add_argument('--promoted-readback'",source)
        self.assertNotIn("add_argument('--prune'",source)
    def test_argument_mode_is_exclusive(self):
        # Malformed invocations must exit before reading stdin or touching state.
        with patch.object(sys,'argv',['receiver','--receive','--review-only']):
            with self.assertRaises(SystemExit) as caught:m.main()
        self.assertEqual(caught.exception.code,2)
if __name__=='__main__':unittest.main(verbosity=2)
