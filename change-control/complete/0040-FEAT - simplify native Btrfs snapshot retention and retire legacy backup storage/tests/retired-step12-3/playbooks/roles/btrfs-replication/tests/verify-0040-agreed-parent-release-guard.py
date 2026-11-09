#!/usr/bin/env python3
"""0040 3G: fail-closed source release guard, disposable-only tests."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-native-endpoint.py'
spec = importlib.util.spec_from_file_location('native_guard_0040', MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
STAMP = '20261030-030033Z'
UUID = 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'

def state():
    return {'schema': 1, 'established': {'timestamp': STAMP, 'uuid': UUID},
            'pending': None, 'previous': None}

class Guard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / '.agreed-parent.json'

    def put(self, obj):
        self.path.write_text(json.dumps(obj))
        os.chmod(self.path, 0o600)
        # Root ownership is enforced by production code, while these tests
        # can run unprivileged by mocking the narrow metadata check.

    def read(self):
        original = Path.stat
        path = self.path
        class Meta:
            def __init__(self, info):
                self.st_mode = info.st_mode
                self.st_nlink = info.st_nlink
                self.st_size = info.st_size
                self.st_uid = 0
        def fake(obj, *args, **kwargs):
            value = original(obj, *args, **kwargs)
            return Meta(value) if obj == path else value
        with patch.object(Path, 'stat', fake):
            return mod.agreed_parent_protected(path)

    def test_absent_is_legacy_compatible(self):
        self.assertEqual(self.read(), {})

    def test_established_blocks_release(self):
        self.put(state())
        self.assertEqual(self.read()[STAMP], UUID)

    def test_pending_and_previous_protected(self):
        for field in ('pending', 'previous'):
            with self.subTest(field=field):
                st = state()
                st[field] = {'timestamp': '20261029-030003Z',
                             'uuid': '3a2cc82d-a9ab-964f-af85-f073dd45f0a4'}
                self.put(st)
                self.assertEqual(len(self.read()), 2)

    def test_corruption_rejected(self):
        self.path.write_text('{bad json')
        os.chmod(self.path, 0o600)
        with self.assertRaises(RuntimeError): self.read()

    def test_bad_schema_rejected(self):
        st = state(); st['schema'] = 2
        self.put(st)
        with self.assertRaises(RuntimeError): self.read()

    def test_symlink_rejected(self):
        target = Path(self.tmp.name) / 'target'
        target.write_text('{}')
        self.path.symlink_to(target)
        with self.assertRaises(RuntimeError): self.read()

    def test_duplicate_identity_rejected(self):
        st = state(); st['pending'] = st['established']
        self.put(st)
        with self.assertRaises(RuntimeError): self.read()

    def test_unsafe_permissions_rejected(self):
        self.put(state())
        os.chmod(self.path, 0o666)
        with self.assertRaises(RuntimeError): self.read()

    def test_guard_executed_before_release(self):
        source = MODULE.read_text()
        segment = source[source.index('def protection_update('):]
        self.assertLess(segment.index('agreed_parent_protected(AGREED_PARENT)'), segment.index('del pins[stamp]'))

if __name__ == '__main__': unittest.main(verbosity=2)
