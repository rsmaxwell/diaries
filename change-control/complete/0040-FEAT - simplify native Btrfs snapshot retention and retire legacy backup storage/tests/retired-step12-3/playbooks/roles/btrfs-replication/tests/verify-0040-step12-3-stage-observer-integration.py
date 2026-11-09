#!/usr/bin/env python3
"""Bounded receive stage observer tests, with simulated scope and subprocess."""
from pathlib import Path
import importlib.util
import subprocess
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-receive-core.py'
spec = importlib.util.spec_from_file_location('receive_core_observer',path)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
SCOPE = 'btrfs-agreed-receive-20261103-010000Z-' + 'a'*16 + '.scope'

class Proc:
    pid = 12345
    returncode = 0
    def __init__(self):
        self.calls=0
    def communicate(self,timeout=None):
        self.calls+=1
        if self.calls==1:
            raise subprocess.TimeoutExpired(['test'], timeout)
        return b'',b''
    def wait(self,timeout=None):
        return 0

class Cases(unittest.TestCase):
    def run_group(self, observe):
        proc=Proc()
        with patch.object(core.os,'geteuid',return_value=0):
            result=core.run_bounded_receive_group(
                ['/fake/btrfs','receive'],stdin=object(),timeout=5,
                popen=lambda cmd,**kw:proc,
                kill_group=lambda pid,sig: (_ for _ in ()).throw(ProcessLookupError()),
                clock=lambda:0,
                lock_fds=(42,43),scope_unit=SCOPE,
                scope_query=lambda unit: {
                    'unit':unit,
                    'status':'active' if proc.calls<2 else 'unloaded-ambiguous',
                    'tasks_current':1 if proc.calls<2 else 0,
                    'cleanup_authorized':False,
                    'terminated_independently_proven':False},
                scope_lifecycle=True,stage_observer=observe)
        return result
    def test_observer_polled_and_confirmed(self):
        calls=[]
        self.assertEqual(self.run_group(lambda:calls.append(1) or True).returncode,0)
        self.assertGreaterEqual(len(calls),2)
    def test_missing_ownership_witness_refuses_success(self):
        with self.assertRaisesRegex(RuntimeError,'creation witness'):
            self.run_group(lambda:False)
    def test_invalid_observer_refused(self):
        with self.assertRaises(RuntimeError):
            self.run_group('not-callable')
    def test_installer_and_core_use_ownership(self):
        src=(path.read_text())
        self.assertIn('btrfs-agreed-parent-stage-ownership.py',src)
        self.assertIn('stage_observer=observer',src)
        installer=(path.parents[1]/'tasks/agreed-parent-runtime.yaml').read_text()
        self.assertIn('    - stage-ownership',installer)

if __name__=='__main__':
    unittest.main(verbosity=2)
