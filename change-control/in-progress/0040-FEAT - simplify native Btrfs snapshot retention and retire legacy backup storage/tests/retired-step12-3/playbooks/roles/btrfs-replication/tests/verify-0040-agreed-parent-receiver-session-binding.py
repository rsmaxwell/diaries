#!/usr/bin/python3
"""04Q dormant receiver channel registration regression tests."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-receiver-session-binding.py'
spec = importlib.util.spec_from_file_location('binding04q', PATH)
m = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = m
spec.loader.exec_module(m)
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
TOK = 'a'*64

def session(clock=lambda: 0):
    return m.ReceiverSession(A,B,lock_owner='writer-1',clock=clock,token_factory=lambda:TOK)

def reg(s, channel, *, connection=None, proof=None, **kw):
    return s.register(channel,token=TOK,parent=A,candidate=B,
        proof=proof if proof is not None else m.TransportProof('richard',connection or channel,True,'writer-1'),
        locks_held=True,lock_owner='writer-1',**kw)

class Tests(unittest.TestCase):
    def test_valid_two_channels(self):
        s=session(); self.assertEqual(reg(s,'data')['status'],'receiver-session-registering')
        r=reg(s,'control'); self.assertEqual(r['status'],'receiver-session-bound')
        self.assertFalse(r['authorizes_transfer']);self.assertTrue(s.bound(locks_held=True,lock_owner='writer-1'))
    def test_wrong_token(self):
        s=session()
        with self.assertRaises(m.BindingRefused): s.register('data',token='b'*64,parent=A,candidate=B,proof=m.TransportProof('richard','x',True,'writer-1'),locks_held=True,lock_owner='writer-1')
        self.assertEqual(s.phase,'failed')
    def test_wrong_parent(self):
        s=session()
        with self.assertRaises(m.BindingRefused): s.register('data',token=TOK,parent=B,candidate=B,proof=m.TransportProof('richard','x',True,'writer-1'),locks_held=True,lock_owner='writer-1')
    def test_wrong_principal(self):
        with self.assertRaises(m.BindingRefused):reg(session(),'data',proof=m.TransportProof('root','x',True,'writer-1'))
    def test_unverified(self):
        with self.assertRaises(m.BindingRefused):reg(session(),'data',proof=m.TransportProof('richard','x',False,'writer-1'))
    def test_untrusted_dictionary(self):
        with self.assertRaises(m.BindingRefused):reg(session(),'data',proof={'ssh_principal':'richard','authenticated':True,'connection_id':'x','receiver_lock_owner':'writer-1'})
    def test_duplicate_channel(self):
        s=session();reg(s,'data')
        with self.assertRaises(m.BindingRefused):reg(s,'data')
    def test_same_connection(self):
        s=session();reg(s,'data',connection='shared')
        with self.assertRaises(m.BindingRefused):reg(s,'control',connection='shared')
    def test_wrong_lock_owner(self):
        with self.assertRaises(m.BindingRefused): reg(session(),'data',proof=m.TransportProof('richard','x',True,'other'))
    def test_lost_locks(self):
        s=session()
        with self.assertRaises(m.BindingRefused):s.register('data',token=TOK,parent=A,candidate=B,proof=m.TransportProof('richard','x',True,'writer-1'),locks_held=False,lock_owner='writer-1')
    def test_deadline(self):
        t=[0];s=session(clock=lambda:t[0]);t[0]=121
        with self.assertRaises(m.BindingRefused):reg(s,'data')
    def test_bound_deadline(self):
        t=[0];s=session(clock=lambda:t[0]);reg(s,'data');reg(s,'control');t[0]=121
        with self.assertRaises(m.BindingRefused):s.bound(locks_held=True,lock_owner='writer-1')
    def test_close(self):
        s=session();reg(s,'data');s.close()
        with self.assertRaises(m.BindingRefused):reg(s,'control')
    def test_no_io_cli_or_execution(self):
        text=PATH.read_text();self.assertNotIn('import subprocess',text);self.assertNotIn('socket.',text);self.assertNotIn('__main__',text)
    def test_invalid_order(self):
        with self.assertRaises(m.BindingRefused):m.ReceiverSession(B,A,lock_owner='x')

if __name__=='__main__':unittest.main(verbosity=2)
