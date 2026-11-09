#!/usr/bin/env python3
"""Offline receiver entry to migrated core integration, no real stream."""
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch
F=Path(__file__).resolve().parents[1]/'files'
def load(name):
    spec=importlib.util.spec_from_file_location('step123_'+name.replace('-','_'),F/name)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('btrfs-agreed-parent-receiver-entry.py')
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
class S:
    def read(self,n=-1): return b''
class T(unittest.TestCase):
    def setUp(self):
        self.r={'schema':1,'snapshot':A['timestamp'],'source_uuid':A['uuid'],
                'received_uuid':A['uuid'],'destination':'/@data/mars-received/@data/'+A['timestamp'],
                'source_filesystem_uuid':'source-fs','receiver_filesystem_uuid':'receiver-fs',
                'read_only_verified':True,'transport':'btrfs-full','source_send_exit':0,
                'receiver_receive_exit':0}
        self.att=SimpleNamespace(SOURCE_FS='source-fs',RECEIVER_FS='receiver-fs',strict_receipt=lambda p,s:self.r)
        self.endpoint=SimpleNamespace(inspect_snapshot=lambda stamp:{'flags':'readonly','received_uuid':A['uuid']})
    def test_verified_parent(self):
        self.assertTrue(m.verify_established_parent_locked(A['timestamp'],A['uuid'],endpoint=self.endpoint,attestation=self.att)['receiver_verified_under_lock'])
    def test_bad_receipt(self):
        for k,v in [('source_send_exit',True),('received_uuid','different'),('destination','/tmp/x')]:
            with self.subTest(k=k):
                orig=self.r[k];self.r[k]=v
                with self.assertRaises(RuntimeError):m.verify_established_parent_locked(A['timestamp'],A['uuid'],endpoint=self.endpoint,attestation=self.att)
                self.r[k]=orig
    def test_bad_observed_identity(self):
        x=SimpleNamespace(inspect_snapshot=lambda stamp:{'flags':'readonly','received_uuid':B['uuid']})
        with self.assertRaises(RuntimeError):m.verify_established_parent_locked(A['timestamp'],A['uuid'],endpoint=x,attestation=self.att)
    def test_fail_closed_default(self):
        with self.assertRaisesRegex(RuntimeError,'not enabled'):m.receive_from_migrated_core_internal(A,B,input_stream=S())
    def test_no_cli(self):
        source=(F/'btrfs-agreed-parent-receiver-entry.py').read_text()
        self.assertNotIn("add_argument('--execute",source)
        self.assertNotIn('receive_from_migrated_core_internal(parent, candidate, input_stream=sys.stdin',source)
    def test_single_core_owner(self):
        calls=[]
        class Core:
            def receive_prepared_candidate_integrated(self,a,b,**kw):
                calls.append(kw)
                selfv=kw['verify_parent'](a['timestamp'],a['uuid'])
                assert selfv['receiver_verified_under_lock']
                return {'status':'receiver-provisional-only','receipt_committed':False,
                        'transfer_finalized':False,'authorizes_transition':False,
                        'authorizes_prune':False,'authorizes_release':False}
        deps=dict(core=Core(),state=object(),absence=object(),endpoint=self.endpoint,
                  journal=object(),attestation=self.att,manager_lock=m.MANAGER,
                  writer_lock=m.WRITER,state_dir=m.STATE,runner=lambda *a:None,
                  inspect_received=lambda *a:None)
        result=m.receive_from_migrated_core_internal(A,B,input_stream=S(),dependencies=deps)
        self.assertEqual(len(calls),1)
        self.assertEqual(result['status'],'receiver-provisional-only')
    def test_unsafe_core_result(self):
        class Core:
            def receive_prepared_candidate_integrated(self,*a,**kw):return {'status':'receiver-provisional-only','receipt_committed':True}
        deps=dict(core=Core(),state=object(),absence=object(),endpoint=self.endpoint,
                  journal=object(),attestation=self.att,manager_lock=m.MANAGER,
                  writer_lock=m.WRITER,state_dir=m.STATE,runner=lambda *a:None,
                  inspect_received=lambda *a:None)
        with self.assertRaisesRegex(RuntimeError,'unsafe'):m.receive_from_migrated_core_internal(A,B,input_stream=S(),dependencies=deps)
if __name__=='__main__':unittest.main(verbosity=2)
