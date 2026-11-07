#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-finalisation-core.py'
spec = importlib.util.spec_from_file_location('finalisation', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
NONCE = 'a' * 64
BOOT = 'e87ccc64-fddc-41e7-a6e0-a4151dbb3fad'

def journal():
    return {'schema':1, 'status':'receiving', 'parent':A, 'candidate':B,
            'nonce':NONCE, 'scope_unit':'btrfs-agreed-receive-'+B['timestamp']+'-'+NONCE[:16]+'.scope',
            'scope_binding':'reserved-not-termination-evidence', 'receiver_boot_id':BOOT}

class Cases(unittest.TestCase):
    def test_scoped_finalisation_commits_receipt_only(self):
        commits=[]
        proof={'authenticated_session':True,'source_send_exit':0,'ssh_exit':0,
               'receiver_receive_exit':0,'parent':A,'candidate':B}
        receipt={'snapshot':B['timestamp'],'source_uuid':B['uuid'],
                 'received_uuid':B['uuid'],'parent_snapshot':A['timestamp'],
                 'parent_source_uuid':A['uuid'],'transport':'btrfs-incremental',
                 'read_only_verified':True,'source_send_exit':0,'receiver_receive_exit':0}
        result=m.finalize_locked(A,B,read_state=lambda:{'schema':1,'established':A,'pending':B,'previous':None},
            read_journal=journal,verify_source_completion=lambda a,b,n:proof if n==NONCE else None,
            inspect_received=lambda s:{'uuid':'receiver','flags':'readonly','received_uuid':B['uuid']},
            receipt_absent=lambda s:True,commit_receipt=lambda s,r:commits.append((s,r)),
            receipt_fields=receipt,manager_lock_held=True,writer_lock_held=True)
        self.assertEqual(len(commits),1)
        self.assertFalse(result['authorizes_transition'])
        self.assertFalse(result['authorizes_prune'])

    def test_scoped_accepts(self):
        self.assertEqual(m.validate_provisional_journal(journal(),A,B)['nonce'],NONCE)
    def test_legacy_accepts(self):
        j=journal()
        for field in ('scope_unit','scope_binding','receiver_boot_id'): j.pop(field)
        self.assertEqual(m.validate_provisional_journal(j,A,B)['nonce'],NONCE)
    def test_refuses_modified_scope(self):
        j=journal(); j['scope_unit']='other.scope'
        with self.assertRaises(m.FinalisationRefused): m.validate_provisional_journal(j,A,B)
    def test_refuses_modified_binding(self):
        j=journal(); j['scope_binding']='terminated'
        with self.assertRaises(m.FinalisationRefused): m.validate_provisional_journal(j,A,B)
    def test_refuses_missing_boot(self):
        j=journal(); j.pop('receiver_boot_id')
        with self.assertRaises(m.FinalisationRefused): m.validate_provisional_journal(j,A,B)
    def test_refuses_bad_boot(self):
        j=journal(); j['receiver_boot_id']='garbage'
        with self.assertRaises(m.FinalisationRefused): m.validate_provisional_journal(j,A,B)
    def test_refuses_extra_field(self):
        j=journal(); j['extra']=True
        with self.assertRaises(m.FinalisationRefused): m.validate_provisional_journal(j,A,B)
    def test_refuses_wrong_candidate(self):
        with self.assertRaises(m.FinalisationRefused): m.validate_provisional_journal(journal(),B,B)

if __name__=='__main__': unittest.main(verbosity=2)
