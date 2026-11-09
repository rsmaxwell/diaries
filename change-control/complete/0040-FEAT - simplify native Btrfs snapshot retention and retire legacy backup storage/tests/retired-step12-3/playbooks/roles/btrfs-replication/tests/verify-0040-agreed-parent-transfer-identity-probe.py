#!/usr/bin/python3
"""Pure mocked transport tests: never contact SSH or production endpoints."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
P=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-transfer-identity-probe.py'
s=importlib.util.spec_from_file_location('probe04p',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Cases(unittest.TestCase):
    def ok(self,argv,**kw):
        self.assertEqual(tuple(argv),m.COMMAND)
        self.assertEqual(kw['timeout'],25)
        self.assertEqual(kw['capture_output'],True)
        self.assertEqual(kw['text'],True)
        self.assertEqual(kw['check'],False)
        return subprocess.CompletedProcess(argv,0,'richard\n','')
    def test_success_two_probes(self):
        calls=[]
        def run(*args,**kwargs): calls.append(1); return self.ok(*args,**kwargs)
        result=m.probe(run=run)
        self.assertEqual(len(calls),2)
        self.assertFalse(result['cross_channel_binding_verified'])
        self.assertFalse(result['authorizes_transfer'])
        self.assertFalse(result['transfer_executed'])
    def test_no_root_ssh(self):
        self.assertEqual(m.COMMAND[:5],('/usr/sbin/runuser','-u','richard','--','ssh'))
    def test_failed_first(self):
        with self.assertRaises(m.ProbeRefused):m.probe(run=lambda *a,**k:subprocess.CompletedProcess(a,255,'',''))
    def test_failed_second(self):
        count=[0]
        def run(*a,**k):
            count[0]+=1
            return self.ok(*a,**k) if count[0]==1 else subprocess.CompletedProcess(a,255,'','')
        with self.assertRaises(m.ProbeRefused):m.probe(run=run)
    def test_wrong_account(self):
        with self.assertRaises(m.ProbeRefused):m.probe(run=lambda a,**k:subprocess.CompletedProcess(a,0,'root\n',''))
    def test_extra_output(self):
        with self.assertRaises(m.ProbeRefused):m.probe(run=lambda a,**k:subprocess.CompletedProcess(a,0,'richard\nother\n',''))
    def test_timeout(self):
        def run(*a,**k):raise subprocess.TimeoutExpired(a,25)
        with self.assertRaises(m.ProbeRefused):m.probe(run=run)
    def test_oserror(self):
        def run(*a,**k):raise OSError('no ssh')
        with self.assertRaises(m.ProbeRefused):m.probe(run=run)
    def test_invalid_deadline(self):
        for t in (True,0,15,61,'25'):
            with self.subTest(t=t),self.assertRaises(m.ProbeRefused):m.probe(run=self.ok,timeout=t)
    def test_reject_bool_rc(self):
        with self.assertRaises(m.ProbeRefused):m.probe(run=lambda a,**k:subprocess.CompletedProcess(a,False,'richard\n',''))
    def test_bounded_error_output(self):
        with self.assertRaises(m.ProbeRefused):m.probe(run=lambda a,**k:subprocess.CompletedProcess(a,0,'richard\n','e'*8193))
    def test_cli_review_only(self):
        import ast
        tree=ast.parse(P.read_text())
        self.assertNotIn('--execute-transfer',P.read_text())
        self.assertNotIn('Popen(',P.read_text())
        self.assertTrue(any(isinstance(n,ast.FunctionDef) and n.name=='main' for n in tree.body))
if __name__=='__main__':unittest.main(verbosity=2)
