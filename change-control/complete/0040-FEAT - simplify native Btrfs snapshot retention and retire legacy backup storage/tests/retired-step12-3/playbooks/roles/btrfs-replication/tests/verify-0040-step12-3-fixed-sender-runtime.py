#!/usr/bin/env python3
"""Offline regression for the fixed sender runtime composition, no transfer."""
import importlib.util
from pathlib import Path
from unittest import TestCase, main, mock

SRC = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-sender-execution.py'
spec = importlib.util.spec_from_file_location('sender_execution_runtime', SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class Tests(TestCase):
    def test_no_public_entry(self):
        self.assertNotIn('if __name__', SRC.read_text())
    def test_fixed_module_names(self):
        self.assertEqual(len(mod._RUNTIME_NAMES), 9)
        self.assertTrue(all(x.startswith('btrfs-agreed-parent-') and x.endswith('.py')
                            for x in mod._RUNTIME_NAMES.values()))
    def test_incomplete_dependencies_refused(self):
        with self.assertRaisesRegex(mod.ExecutionRefused, 'incomplete'):
            mod.execute_installed_source_internal(A, B, modules={})
    def test_missing_dependency_refused(self):
        with self.assertRaisesRegex(mod.ExecutionRefused, 'missing'):
            mod.execute_installed_source_internal(A, B, modules=dict.fromkeys(mod._RUNTIME_NAMES))
    def test_verified_receipt_is_connected_to_sender_execution(self):
        seen = []
        class Receipt:
            def verify_receipt_over_ssh(self, parent, candidate, *, commands):
                seen.append(('receipt', parent, candidate, commands))
                return True
        class Handoff:
            read_sender_key = staticmethod(lambda: b'k' * 32)
        fixed = object()
        modules = {key: object() for key in mod._RUNTIME_NAMES}
        modules.update(receipt_readback=Receipt(), sender_handoff=Handoff(),
                       fixed_commands=fixed)

        def run_sender(a, b, **kwargs):
            self.assertTrue(kwargs['pinned_parent_verified'](a, b))
            self.assertEqual(kwargs['verify_final_receipt'](a, b), True)
            self.assertEqual(kwargs['read_sender_key'](), b'k' * 32)
            return {'authorizes_prune': False, 'authorizes_transition': False,
                    'authorizes_release': False}

        with mock.patch.object(mod, 'execute_with_verified_source') as locked:
            locked.side_effect = lambda a, b, **kw: kw['execution'](
                a, b, pinned_parent_verified=lambda *_: True)
            with mock.patch.object(mod, 'execute_provisional_then_receipt',
                                   side_effect=run_sender) as invoke:
                result = mod.execute_installed_source_internal(A, B, modules=modules)
        self.assertFalse(result['authorizes_prune'])
        self.assertEqual(seen, [('receipt', A, B, fixed)])
        invoke.assert_called_once()

    def test_missing_receipt_adapter_refuses_before_transfer(self):
        modules = {key: object() for key in mod._RUNTIME_NAMES}
        with mock.patch.object(mod, 'execute_with_verified_source') as locked:
            with self.assertRaisesRegex(mod.ExecutionRefused, 'receipt or sender key'):
                mod.execute_installed_source_internal(A, B, modules=modules)
            locked.assert_not_called()

    def test_nonroot_refuses_loader(self):
        with mock.patch.object(mod, '_RUNTIME_LIB', Path('/nonexistent')):
            with mock.patch('os.geteuid', return_value=1000):
                with self.assertRaisesRegex(mod.ExecutionRefused, 'requires root'):
                    mod._load_fixed_runtime_modules()

if __name__ == '__main__': main(verbosity=2)
