#!/usr/bin/env python3
"""Offline guards for the production maintenance tool; no remote connections."""
import importlib.util
from pathlib import Path
from unittest import TestCase, main, mock

M = Path(__file__).resolve().parents[1] / 'tools/0028-pluto-maintenance-window.py'
spec = importlib.util.spec_from_file_location('control0028', M)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

NORMAL = b'''# test pg_hba.conf\nlocal   all all trust\nhost all all 127.0.0.1/32 trust\nhost all all ::1/128 trust\nhost all all all scram-sha-256\n'''

class Tests(TestCase):
    def test_preserves_original_bytes_outside_insert(self):
        patched = mod.patch_bytes(NORMAL)
        self.assertEqual(patched.replace(mod.REJECT.encode(), b''), NORMAL)
        self.assertEqual(patched.count(b'0.0.0.0/0 reject'), 1)
        self.assertEqual(patched.count(b'::/0 reject'), 1)
    def test_existing_marker_rejected(self):
        with self.assertRaises(mod.Stop):
            mod.patch_bytes(mod.patch_bytes(NORMAL))
    def test_missing_catchall_rejected(self):
        with self.assertRaises(mod.Stop):
            mod.patch_bytes(NORMAL.replace(b'host all all all scram-sha-256', b'host all all all trust'))
    def test_duplicate_catchall_rejected(self):
        with self.assertRaises(mod.Stop):
            mod.patch_bytes(NORMAL + b'host all all all scram-sha-256\n')
    def test_not_a_direct_production_migration_tool(self):
        text = M.read_text()
        for forbidden in ('--mode apply', 'pg_restore', 'btrfs subvolume delete', 'docker compose down', 'DROP TABLE'):
            self.assertNotIn(forbidden, text)
    def test_preflight_rejects_active_backup_before_mutation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'compose.yaml').write_text('services: {}')
            (base / '.env').write_text('')
            with mock.patch.object(mod, 'PROJECT', base), mock.patch.object(mod, 'call') as run, \
                 mock.patch.object(mod, 'unit_active') as active, mock.patch.object(mod, 'unit_enabled', return_value='enabled'):
                run.return_value = mock.Mock(returncode=0)
                active.side_effect = lambda x: 'active'
                with self.assertRaises(mod.Stop):
                    mod.preflight()
                self.assertFalse(any('stop' in str(c) for c in run.call_args_list))
    def test_reopen_restores_hba_first(self):
        events = []
        with mock.patch.object(mod, 'call', side_effect=lambda args, **kw: events.append(args) or mock.Mock(returncode=0)), \
             mock.patch.object(mod, 'docker_running', side_effect=lambda name: name == mod.DB), \
             mock.patch.object(mod, 'hba_path', return_value='/var/lib/postgresql/18/docker/pg_hba.conf'), \
             mock.patch.object(mod, 'exists_in_container', return_value=True), \
             mock.patch.object(mod, 'hba_bytes', return_value=NORMAL), \
             mock.patch.object(mod, 'reload_hba'), \
             mock.patch.object(mod, 'original_rules'), \
             mock.patch.object(mod, 'unit_active', side_effect=lambda u: 'inactive'), \
             mock.patch.object(mod, 'unit_enabled', return_value='enabled'):
            # Reopen refuses if responder not actually running; check operation ordering.
            with self.assertRaises(mod.Stop):
                mod.reopen()
            labels = [str(x) for x in events]
            self.assertTrue(any('cp' in x for x in labels))
            self.assertTrue(any('up' in x for x in labels))
            self.assertLess(next(i for i, x in enumerate(labels) if 'cp' in x), next(i for i, x in enumerate(labels) if 'up' in x))
    def test_shipped_modes_explicit(self):
        src = M.read_text()
        self.assertIn("('preflight', 'isolate', 'status', 'reopen')", src)
        self.assertNotIn('docker rm', src)
        self.assertNotIn('systemctl disable', src)
    def test_receiver_hold_not_claimed(self):
        self.assertNotIn('receiver hold created', M.read_text())

if __name__ == '__main__':
    main(verbosity=2)
