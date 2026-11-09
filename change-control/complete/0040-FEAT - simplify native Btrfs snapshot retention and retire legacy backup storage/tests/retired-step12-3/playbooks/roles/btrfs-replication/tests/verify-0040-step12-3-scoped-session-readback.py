#!/usr/bin/env python3
"""Regression for the receiver's scoped journal session readback under real lock calls."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]/'files'
def load(name):
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),BASE/name)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
entry=load('btrfs-agreed-parent-receiver-entry.py')
core=load('btrfs-agreed-parent-finalisation-core.py')
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
N='a'*64

def journal(scoped=True):
    data={'schema':1,'status':'receiving','parent':A,'candidate':B,'nonce':N}
    if scoped:
        data.update(scope_unit='btrfs-agreed-receive-'+B['timestamp']+'-'+N[:16]+'.scope',scope_binding='reserved-not-termination-evidence',receiver_boot_id='e87ccc64-fddc-41e7-a6e0-a4151dbb3fad')
    return data

class Cases(unittest.TestCase):
    def run_session(self,j):
        class Receiver:
            @staticmethod
            def _lock(stack,path): pass
        class Storage:
            @staticmethod
            def read_state(path):return {'schema':1,'established':A,'pending':B,'previous':None}
            @staticmethod
            def read_journal(path):return j
        modules={'receiver':Receiver,'finalisation-storage':Storage,'finalisation-core':core}
        with patch.object(entry.os,'geteuid',return_value=0):
            return entry.session_fixed(A,B,loader=lambda name:modules[name])
    def test_legacy_session(self): self.assertEqual(self.run_session(journal(False))['nonce'],N)
    def test_scoped_session(self):
        result=self.run_session(journal())
        self.assertEqual(result['nonce'],N)
        self.assertFalse(result['receipt_committed'])
        self.assertFalse(result['authorizes_transition'])
    def test_bad_scope_refused(self):
        j=journal();j['scope_unit']='unrelated.scope'
        with self.assertRaises(core.FinalisationRefused):self.run_session(j)
    def test_partial_scoped_refused(self):
        j=journal();j.pop('receiver_boot_id')
        with self.assertRaises(core.FinalisationRefused):self.run_session(j)
    def test_bad_boot_refused(self):
        j=journal();j['receiver_boot_id']='not-a-uuid'
        with self.assertRaises(core.FinalisationRefused):self.run_session(j)
    def test_extra_field_refused(self):
        j=journal();j['cleanup_authorized']=True
        with self.assertRaises(core.FinalisationRefused):self.run_session(j)

if __name__=='__main__':unittest.main(verbosity=2)
