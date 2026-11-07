#!/usr/bin/env python3
"""Receiver scoped-mode CLI and internal boundary regression (no live receive)."""
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace
P = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-receiver-entry.py'
spec = importlib.util.spec_from_file_location('receiver_scoped_entry_test', P)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
class Cases(unittest.TestCase):
    def invoke(self, scoped):
        captured={}
        def integrated(*a, **kw):
            captured.update(kw)
            return {'status':'receiver-provisional-only','receipt_committed':False,
                    'transfer_finalized':False,'authorizes_transition':False,
                    'authorizes_prune':False,'authorizes_release':False}
        core=SimpleNamespace(receive_prepared_candidate_integrated=integrated)
        observer=SimpleNamespace(inspect_scope=lambda u: {'unit':u}, inspect_scope_lifecycle=lambda u: {'unit':u})
        deps={k:object() for k in ('state','absence','endpoint','journal','attestation')}
        deps.update({'core':core, 'manager_lock':m.MANAGER,'writer_lock':m.WRITER,
                     'state_dir':m.STATE,'runner':object(),'inspect_received':lambda b:None})
        if scoped:deps['scope-observer']=observer
        result=m.receive_from_migrated_core_internal(A,B,input_stream=io.BytesIO(),dependencies=deps,scoped=scoped)
        self.assertEqual(result['status'],'receiver-provisional-only')
        return captured
    def test_scoped_trusted_observer_and_real_runner(self):
        args=self.invoke(True)
        self.assertIsNone(args['runner'])
        self.assertTrue(args['scoped'])
        self.assertTrue(callable(args['scope_query']))
        self.assertTrue(args['scope_lifecycle'])
    def test_default_unchanged(self):
        args=self.invoke(False)
        self.assertNotIn('scoped',args)
        self.assertNotIn('scope_query',args)
        self.assertIsNotNone(args['runner'])
    def test_mismatched_dependency_refused(self):
        with self.assertRaisesRegex(RuntimeError,'invalid internal migrated core dependencies'):
            m.receive_from_migrated_core_internal(A,B,input_stream=io.BytesIO(),dependencies={},scoped=True)
    def test_opt_in_cli_present(self):
        text=P.read_text()
        self.assertIn("mode.add_argument('--receive-scoped'",text)
        self.assertIn('scoped=(args.receive_scoped or args.receive_staged_scoped)',text)
        self.assertIn('mode.add_argument(\'--receive\'',text)
    def test_installer_includes_observer(self):
        tasks=(P.parents[1]/'tasks'/'agreed-parent-runtime.yaml').read_text()
        self.assertIn('    - scope-observer',tasks)
if __name__=='__main__': unittest.main(verbosity=2)
