#!/usr/bin/python3
"""Offline regression for read-only parent transfer plan."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main, mock

P = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-transfer-plan.py'
spec = importlib.util.spec_from_file_location('transfer_plan', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-180000Z', 'uuid': 'a901ddd2-66c7-0b42-b26c-ab6886273b7a'}
STATE = {'schema': 1, 'established': A, 'pending': None, 'previous': None}

class Tests(TestCase):
    def deps(self, *, state=None, comparison='matched', ssh=0, receipt=True, bad_authority=False):
        local = dict(STATE if state is None else state)
        order = []
        def lock(stack, path): order.append(('lock', path))
        def load(path, require_root):
            order.append(('load', path)); self.assertTrue(require_root); return local
        def verify(item):
            order.append(('verify', item['timestamp'])); return dict(item, verified=True)
        def inspect(src, stdout, ssh_exit):
            order.append(('bridge', ssh_exit)); return {'comparison': comparison, 'receiver': local,
                'authorizes_transition': bad_authority, 'authorizes_prune': False}
        def select(**args):
            order.append(('select', args['target']['timestamp']))
            if not receipt: raise RuntimeError('missing receipt')
            self.assertEqual(args['source_parent'], A)
            self.assertEqual(args['receiver_receipts'], [{'snapshot': A['timestamp'], 'source_uuid': A['uuid']}])
            return {'parent': A['timestamp'], 'parent_uuid': A['uuid'], 'authorizes_transfer': False, 'authorizes_release': False}
        dep = (SimpleNamespace(lock=lock), SimpleNamespace(load=load, validate=lambda s: None),
               SimpleNamespace(verify_source=verify), SimpleNamespace(inspect=inspect),
               SimpleNamespace(select=select))
        return dep, order

    def run_plan(self, **kwargs):
        dep, order = self.deps(**kwargs)
        with mock.patch.object(m, 'target_identity', return_value=B), mock.patch.object(m.subprocess, 'run', return_value=SimpleNamespace(returncode=kwargs.get('ssh', 0), stdout='{}')) as ssh:
            if kwargs.get('ssh', 0):
                with self.assertRaisesRegex(RuntimeError, 'SSH failed'): m.plan(B['timestamp'], dependencies=dep)
                return order, ssh
            if kwargs.get('comparison', 'matched') != 'matched' or kwargs.get('bad_authority', False):
                with self.assertRaisesRegex(RuntimeError, 'disagreement or authority'): m.plan(B['timestamp'], dependencies=dep)
                return order, ssh
            if kwargs.get('receipt') is False:
                with self.assertRaisesRegex(RuntimeError, 'missing receipt'): m.plan(B['timestamp'], dependencies=dep)
                return order, ssh
            outcome=m.plan(B['timestamp'], dependencies=dep)
            self.assertEqual(outcome['parent'], A['timestamp'])
            self.assertIs(outcome['authorizes_transfer'], False)
            self.assertIs(outcome['authorizes_release'], False)
            self.assertIs(outcome['authorizes_transition'], False)
            self.assertIs(outcome['authorizes_prune'], False)
            self.assertEqual(ssh.call_args.args[0], list(m.SSH))
            return order, ssh

    def test_order_and_no_transfer(self):
        order, _=self.run_plan()
        self.assertEqual([x[0] for x in order], ['lock','lock','load','verify','verify','bridge','select'])
        self.assertEqual(order[0][1], m.SOURCE_LOCK)
        self.assertEqual(order[1][1], m.MANAGER_LOCK)

    def test_bad_ssh(self): self.run_plan(ssh=255)
    def test_diverged(self): self.run_plan(comparison='diverged')
    def test_unsafe_authority(self): self.run_plan(bad_authority=True)
    def test_missing_receipt(self): self.run_plan(receipt=False)

    def test_pending_prevents_ssh(self):
        dep, order=self.deps(state=dict(STATE, pending=B))
        with mock.patch.object(m, 'target_identity') as target, mock.patch.object(m.subprocess, 'run') as ssh:
            with self.assertRaisesRegex(RuntimeError, 'unfinished transition'): m.plan(B['timestamp'], dependencies=dep)
            target.assert_not_called(); ssh.assert_not_called()

    def test_previous_prevents_ssh(self):
        dep, order=self.deps(state=dict(STATE, previous=B))
        with mock.patch.object(m, 'target_identity') as target, mock.patch.object(m.subprocess, 'run') as ssh:
            with self.assertRaisesRegex(RuntimeError, 'unfinished transition'): m.plan(B['timestamp'], dependencies=dep)
            target.assert_not_called(); ssh.assert_not_called()

    def test_target_path_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'invalid target'): m.target_identity('../etc/passwd')

    def test_target_must_be_readonly(self):
        with mock.patch.object(m.Path, 'is_symlink', return_value=False), mock.patch.object(m.Path, 'is_dir', return_value=True):
            result=SimpleNamespace(returncode=0, stdout='UUID: '+ B['uuid']+'\nFlags: -\nReceived UUID: -')
            with self.assertRaisesRegex(RuntimeError, 'readonly mismatch'):
                m.target_identity(B['timestamp'], runner=lambda *a, **kw: result)

    def test_target_uuid_extracted(self):
        with mock.patch.object(m.Path, 'is_symlink', return_value=False), mock.patch.object(m.Path, 'is_dir', return_value=True):
            result=SimpleNamespace(returncode=0, stdout='UUID: '+ B['uuid']+'\nFlags: readonly\nReceived UUID: -')
            self.assertEqual(m.target_identity(B['timestamp'], runner=lambda *a, **kw: result), B)

if __name__ == '__main__': main(verbosity=2)
