#!/usr/bin/env python3
"""0040-FEAT: source-only cutover-readiness checks; never contact hosts."""
import ast
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
ROLE = ROOT / 'roles/btrfs-replication'
MANAGER = ROOT / 'roles/snapshots/files/btrfs-snapshot-manager.py'
COMMAND = ROLE / 'files/btrfs-simplified-replication.py'
CONFIG = ROLE / 'templates/btrfs-receiver-manager.json.j2'
SERVICE = ROLE / 'templates/btrfs-native-push.service.j2'
DEFAULTS = ROOT / 'roles/snapshots/defaults/main.yaml'


def assignment_path(tree, symbol):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == symbol for t in node.targets):
            call = node.value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == 'Path':
                return Path(ast.literal_eval(call.args[0]))
    raise AssertionError(f'{symbol}: no literal Path found')


class Readiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = COMMAND.read_text(encoding='utf-8')
        cls.manager = MANAGER.read_text(encoding='utf-8')
        cls.cmdtree = ast.parse(cls.command)
        ast.parse(cls.manager)

    def test_native_endpoint_fallback_is_retired(self):
        native = (ROLE / 'tasks/native.yaml').read_text(encoding='utf-8')
        self.assertNotIn('btrfs-native-endpoint.py', native)
        self.assertNotIn('btrfs-native-push.py', native)
        self.assertIn('Native Btrfs | Keep retired endpoint sudoers absent', native)

    def test_simple_state_paths_match_manager_locations(self):
        source = assignment_path(self.cmdtree, 'SOURCE')
        received = assignment_path(self.cmdtree, 'RECEIVED')
        source_state = assignment_path(self.cmdtree, 'SOURCE_STATE')
        receiver_state = assignment_path(self.cmdtree, 'RECEIVER_STATE')
        self.assertEqual(source_state, source.parent / '.simple-agreed-parent.json')
        self.assertEqual(receiver_state, received.parent / '.replication-state/.simple-agreed-parent.json')
        fn = next(n for n in ast.walk(ast.parse(self.manager)) if isinstance(n, ast.FunctionDef) and n.name == 'simplified_agreed_parent_pins')
        body = ast.get_source_segment(self.manager, fn)
        self.assertIn('config.snapshot_root', body)
        self.assertIn('config.receiver_state_dir', body)
        self.assertIn('".simple-agreed-parent.json"', body)
        self.assertIn(str(receiver_state.parent), CONFIG.read_text(encoding='utf-8'))
        # Source effective snapshot root is rendered dynamically; verify real host config separately.

    def test_simple_state_is_used_in_both_prune_paths(self):
        tree = ast.parse(self.manager)
        callers = []
        for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
            if fn.name == 'simplified_agreed_parent_pins':
                continue
            if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and
                   n.func.id == 'simplified_agreed_parent_pins' for n in ast.walk(fn)):
                callers.append(fn.name)
        self.assertGreaterEqual(len(callers), 2, f'missing source/receiver prune protection: {callers}')

    def test_prune_and_replicate_share_configured_lock_path(self):
        path = assignment_path(self.cmdtree, 'MANAGER_LOCK')
        self.assertEqual(str(path), '/run/lock/btrfs-snapshot-manager.lock')
        self.assertIn(str(path), CONFIG.read_text(encoding='utf-8'))
        self.assertIn(str(path), DEFAULTS.read_text(encoding='utf-8'))

    def test_service_has_only_simplified_execstart(self):
        service = SERVICE.read_text(encoding='utf-8')
        self.assertNotIn('btrfs-native-push --latest', service)
        self.assertIn('User=root', service)
        self.assertIn('Group=root', service)
        self.assertIn('ConditionFileIsExecutable=/usr/local/bin/btrfs-simplified-replication', service)
        self.assertIn('ExecStart=/usr/local/bin/btrfs-simplified-replication sender cycle', service)
        native = (ROLE / 'tasks/native.yaml').read_text(encoding='utf-8')
        self.assertIn('btrfs_simplified_replication_install_enabled | bool', native)
        self.assertIn('btrfs_simplified_replication_active_enabled | bool', native)
        self.assertIn('Native Btrfs | Install simplified agreed-parent command (opt in)', native)
        self.assertIn('Native Btrfs | Install simplified Diaries backup status report', native)

    def test_current_runtime_and_qgroup_installation_defaults_are_fail_closed(self):
        defaults = (ROLE / 'defaults/main.yaml').read_text(encoding='utf-8')
        for variable in (
            'btrfs_simplified_replication_install_enabled',
            'btrfs_simplified_replication_active_enabled',
            'btrfs_stale_qgroup_maintenance_install_enabled',
            'btrfs_stale_qgroup_maintenance_enabled',
        ):
            with self.subTest(variable=variable):
                self.assertRegex(defaults, rf'(?m)^{re.escape(variable)}:\s*false\s*$')
        native = (ROLE / 'tasks/native.yaml').read_text(encoding='utf-8')
        self.assertIn('Native Btrfs | Enforce explicit receiver retention timer state', native)
        self.assertIn('Native Btrfs | Configure qgroup maintenance without activating by default', native)


if __name__ == '__main__':
    unittest.main(verbosity=2)
