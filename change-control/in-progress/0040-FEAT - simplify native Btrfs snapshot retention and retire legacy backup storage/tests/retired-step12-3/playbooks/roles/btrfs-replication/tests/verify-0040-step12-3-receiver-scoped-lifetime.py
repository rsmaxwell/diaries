#!/usr/bin/env python3
"""Source-level opt-in scoped receiver containment checks; no systemd effects."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
PATH=Path(__file__).resolve().parents[1]/'files'/'btrfs-agreed-parent-receive-core.py'
spec=importlib.util.spec_from_file_location('scoped_receive',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
UNIT='btrfs-agreed-receive-20261102-080000Z.scope'
class Fake:
    pid=999991
    returncode=0
    def communicate(self,timeout=None):return b'',b''
class Tests(unittest.TestCase):
    def invoke(self, *, unit=UNIT, observer=None, rc=0):
        calls=[]
        def spawn(command,**kw):
            calls.append(command)
            f=Fake();f.returncode=rc;return f
        def kill(pid,sig):raise ProcessLookupError
        if observer is None:observer=lambda unit:{'unit':unit,'active_state':'inactive','tasks_current':0,'cleanup_authorized':False,'journal_bound':False}
        try:
            m.run_bounded_receive_group(['/usr/local/bin/receiver'], stdin=object(), timeout=12,
                popen=spawn,kill_group=kill,clock=lambda:0, scope_unit=unit,scope_query=observer)
            return calls
        except Exception:
            self.calls=calls
            raise
    def test_opt_in_launch(self):
        self.assertEqual(self.invoke()[0][:5],['systemd-run','--system','--scope','--quiet','--unit='+UNIT])
    def test_inactive_empty(self):self.assertEqual(len(self.invoke()),1)
    def test_active_refused(self):
        with self.assertRaisesRegex(RuntimeError,'not independently empty'):
            self.invoke(observer=lambda u:{'active_state':'active','tasks_current':1})
    def test_unknown_refused(self):
        with self.assertRaisesRegex(RuntimeError,'not independently empty'):
            self.invoke(observer=lambda u:{'active_state':'unknown','tasks_current':0})
    def test_missing_observer_refused(self):
        with self.assertRaisesRegex(RuntimeError,'Missing independent'):
            m.run_bounded_receive_group(['receiver'],stdin=object(),timeout=10,scope_unit=UNIT)
    def test_invalid_scope_refused(self):
        with self.assertRaisesRegex(RuntimeError,'Invalid receiver scope'):
            self.invoke(unit='arbitrary.scope')
    def test_observer_failure_retains_journal(self):
        with self.assertRaisesRegex(RuntimeError,'observation failed'):
            self.invoke(observer=lambda u:1/0)
    def test_nonzero_exit_refused(self):
        with self.assertRaisesRegex(RuntimeError,'Btrfs receive failed'):
            self.invoke(rc=1)
if __name__=='__main__':unittest.main(verbosity=2)
