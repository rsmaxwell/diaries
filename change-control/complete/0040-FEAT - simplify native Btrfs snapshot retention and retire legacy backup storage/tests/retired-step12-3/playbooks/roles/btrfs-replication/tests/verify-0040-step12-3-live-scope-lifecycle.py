#!/usr/bin/env python3
"""Systemd 255 live-scope observation contracts; no cleanup authority."""
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
p = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-scope-observer.py'
spec = importlib.util.spec_from_file_location('scope_observer', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
UNIT = 'btrfs-agreed-receive-20261102-083000Z-0123456789abcdef.scope'
BASE = dict(Id=UNIT, LoadState='loaded', ActiveState='active', SubState='running',
            ControlGroup='/system.slice/' + UNIT, TasksCurrent='1')
def fake(**fields):
    values = dict(BASE, **fields)
    output = '\n'.join('%s=%s' % kv for kv in values.items()) + '\n'
    return lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=output)
class Tests(unittest.TestCase):
    def test_active(self):
        report=m.inspect_scope_lifecycle(UNIT, runner=fake())
        self.assertEqual(report['status'], 'active')
        self.assertFalse(report['cleanup_authorized'])
    def test_unloaded_after_exit_is_ambiguous(self):
        report=m.inspect_scope_lifecycle(UNIT, runner=fake(
            LoadState='not-found', ActiveState='inactive', SubState='dead',
            ControlGroup='', TasksCurrent='[not set]'))
        self.assertEqual(report['status'], 'unloaded-ambiguous')
        self.assertIsNone(report['tasks_current'])
        for field in ('journal_bound','started_independently_proven',
                      'terminated_independently_proven','cleanup_authorized','retransmit_authorized'):
            self.assertFalse(report[field])
    def test_loaded_empty_diagnostic_not_fencing(self):
        report=m.inspect_scope_lifecycle(UNIT, runner=fake(
            ActiveState='inactive', SubState='dead', TasksCurrent='0'))
        self.assertEqual(report['status'], 'loaded-and-empty')
        self.assertFalse(report['terminated_independently_proven'])
    def test_unloaded_with_tasks_refused(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope_lifecycle(UNIT, runner=fake(
            LoadState='not-found', ActiveState='inactive', SubState='dead', ControlGroup='', TasksCurrent='1'))
    def test_running_without_tasks_refused(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope_lifecycle(UNIT, runner=fake(TasksCurrent='0'))
    def test_wrong_unit_refused(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope_lifecycle(UNIT, runner=fake(Id='wrong.scope'))
    def test_strict_observer_still_refuses_unloaded(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope(UNIT, runner=fake(
            LoadState='not-found', ActiveState='inactive', SubState='dead', ControlGroup='', TasksCurrent='[not set]'))
if __name__ == '__main__': unittest.main(verbosity=2)
