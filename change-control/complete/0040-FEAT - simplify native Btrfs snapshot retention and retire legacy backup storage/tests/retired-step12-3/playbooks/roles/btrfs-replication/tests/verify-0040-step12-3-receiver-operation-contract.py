#!/usr/bin/env python3
"""Offline contract tests; no SSH or Btrfs operations."""
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace

HERE = Path(__file__).resolve().parents[1] / 'files'
spec = importlib.util.spec_from_file_location('receiver_operation_contract', HERE / 'btrfs-agreed-parent-receiver-operation-contract.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
A = {'timestamp': '20261030-010000Z', 'uuid': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}
B = {'timestamp': '20261031-010000Z', 'uuid': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'}

class Gate(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def validate(identity):
            self.calls.append('validate')
            if type(identity) is not dict or set(identity) != {'timestamp', 'uuid'}:
                raise ValueError('identity')
        def promote(a,b):
            self.calls.append('promote')
            return {'status':'receiver-promoted'}
        def read(a,b):
            self.calls.append('readback')
            return {'established': b, 'previous': a, 'pending': None}
        self.deps={'state':SimpleNamespace(snapshot=validate),
                   'binding':SimpleNamespace(promote_verified_receiver=promote),
                   'readback':SimpleNamespace(read_promoted_state=read)}

    def req(self,operation='promote',parent=A,candidate=B):
        return {'operation':operation,'parent':parent,'candidate':candidate}

    def test_promote(self):
        result=mod.dispatch(self.req(), dependencies=self.deps)
        self.assertEqual(self.calls,['validate','validate','promote'])
        self.assertFalse(result['authorizes_release'])
        self.assertFalse(result['authorizes_prune'])

    def test_independent_readback(self):
        self.assertEqual(mod.dispatch(self.req('promoted-readback'),dependencies=self.deps)['result']['previous'],A)
        self.assertEqual(self.calls,['validate','validate','readback'])

    def test_unknown_operation_refuses_without_side_effect(self):
        with self.assertRaises(ValueError): mod.dispatch(self.req('release'), dependencies=self.deps)
        self.assertEqual(self.calls,[])

    def test_extra_args_refused(self):
        req=self.req(); req['path']='/';
        with self.assertRaises(ValueError): mod.dispatch(req, dependencies=self.deps)
        self.assertEqual(self.calls,[])

    def test_non_string_operation_refused(self):
        with self.assertRaises(ValueError): mod.dispatch(self.req(True),dependencies=self.deps)
        self.assertEqual(self.calls,[])

    def test_order_refused(self):
        with self.assertRaises(ValueError): mod.dispatch(self.req(parent=B,candidate=A),dependencies=self.deps)
        self.assertNotIn('promote',self.calls)

    def test_invalid_identity_refused(self):
        with self.assertRaises(ValueError): mod.dispatch(self.req(parent={}),dependencies=self.deps)
        self.assertNotIn('promote',self.calls)

    def test_missing_dependency_refused(self):
        with self.assertRaises(ValueError): mod.dispatch(self.req(),dependencies={'state':self.deps['state']})
        self.assertEqual(self.calls,[])

    def test_no_cli_in_module(self):
        import inspect
        source=inspect.getsource(mod)
        self.assertNotIn('argparse',source)
        self.assertNotIn('subprocess',source)
        self.assertNotIn('if __name__',source)

if __name__=='__main__': unittest.main(verbosity=2)
