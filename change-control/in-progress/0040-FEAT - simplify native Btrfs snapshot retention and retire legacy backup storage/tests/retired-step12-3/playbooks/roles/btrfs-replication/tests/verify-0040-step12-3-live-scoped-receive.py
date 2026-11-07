#!/usr/bin/env python3
"""Source regression for live scope observation without cleanup authority."""
import importlib.util
from pathlib import Path
import subprocess
import unittest

root = Path(__file__).resolve().parents[1] / 'files'
spec = importlib.util.spec_from_file_location('recv_live', root / 'btrfs-agreed-parent-receive-core.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
UNIT = 'btrfs-agreed-receive-20261102-080000Z-abcdef0123456789.scope'

class Proc:
    pid = 123456789
    returncode = 0
    def __init__(self, ticks=1): self.ticks = ticks
    def wait(self, timeout=None): return self.returncode
    def communicate(self, timeout=None):
        if self.ticks:
            self.ticks -= 1
            raise subprocess.TimeoutExpired('systemd-run', timeout)
        return b'', b''

class Tests(unittest.TestCase):
    def run_receive(self, evidence, *, ticks=1, rc=0):
        proc = Proc(ticks)
        proc.returncode = rc
        observed = iter(evidence)
        def query(unit):
            self.assertEqual(unit, UNIT)
            return next(observed)
        return m.run_bounded_receive_group(
            ['receiver'], stdin=object(), timeout=10,
            popen=lambda command, **opts: proc,
            kill_group=lambda pid, sig: (_ for _ in ()).throw(ProcessLookupError()),
            clock=lambda: 0, scope_unit=UNIT, scope_query=query, scope_lifecycle=True)
    def active(self):
        return {'unit':UNIT, 'status':'active', 'tasks_current':1,
                'cleanup_authorized':False, 'terminated_independently_proven':False}
    def unloaded(self):
        return {'unit':UNIT,'status':'unloaded-ambiguous','tasks_current':None,
                'cleanup_authorized':False,'terminated_independently_proven':False}
    def test_live_then_unloaded_success_no_cleanup(self):
        self.assertEqual(self.run_receive([self.active(), self.unloaded()]).returncode,0)
    def test_never_started_unloaded_refused(self):
        with self.assertRaisesRegex(RuntimeError,'lifecycle ambiguous'):
            self.run_receive([self.unloaded(),self.unloaded()])
    def test_wrong_live_unit_refused(self):
        d=self.active();d['unit']='other.scope'
        with self.assertRaisesRegex(RuntimeError,'interrupted/timed out'):
            self.run_receive([d])
    def test_active_after_exit_refused(self):
        with self.assertRaisesRegex(RuntimeError,'lifecycle ambiguous'):
            self.run_receive([self.active(),self.active()])
    def test_no_live_sample_refused(self):
        with self.assertRaisesRegex(RuntimeError,'lifecycle ambiguous'):
            self.run_receive([self.unloaded()],ticks=0)
    def test_failed_receive_not_accepted(self):
        with self.assertRaisesRegex(RuntimeError,'Btrfs receive failed'):
            self.run_receive([self.active(),self.unloaded()],rc=2)

if __name__ == '__main__':unittest.main(verbosity=2)
