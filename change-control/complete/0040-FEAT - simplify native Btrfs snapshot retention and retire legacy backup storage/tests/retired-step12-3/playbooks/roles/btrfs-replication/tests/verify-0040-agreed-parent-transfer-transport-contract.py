#!/usr/bin/python3
"""Pure 0040 Integration 04B transfer-contract regressions; no real processes."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-transfer-transport-contract.py'
spec = importlib.util.spec_from_file_location('transfer_contract', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class Tests(unittest.TestCase):
    def test_exact_parent_sender(self):
        c=m.exact_incremental_commands(A,B)
        self.assertEqual(c['sender'][-4:], ('--snapshot',B['timestamp'],'--parent',A['timestamp']))
    def test_receiver_fixed_exact_args(self):
        c=m.exact_incremental_commands(A,B)
        self.assertEqual(c['receiver_plan'][0],m.RECEIVER)
        self.assertEqual(c['receiver_accept'][-1],'--accept')
        self.assertIn(A['uuid'], c['receiver_accept'])
    def test_no_release_or_prune(self):
        c=m.exact_incremental_commands(A,B)
        self.assertFalse(c['authorizes_transfer'])
        self.assertFalse(c['authorizes_release'])
        self.assertFalse(c['authorizes_prune'])
        self.assertNotIn('release-source',str(c))
    def test_backward_refused(self):
        with self.assertRaises(m.Refused): m.exact_incremental_commands(B,A)
    def test_invalid_uuid_refused(self):
        with self.assertRaises(m.Refused): m.exact_incremental_commands(A,dict(B,uuid='bad'))
    def test_extra_identity_fields_refused(self):
        with self.assertRaises(m.Refused): m.exact_incremental_commands(dict(A,other=1),B)
    def test_valid_receiver_plan(self):
        self.assertTrue(m.validate_receiver_plan(dict(snapshot=B['timestamp'],source_uuid=B['uuid'],parent=A['timestamp'],parent_uuid=A['uuid'],action='incremental'),A,B))
    def test_wrong_receiver_plan_refused(self):
        with self.assertRaises(m.Refused): m.validate_receiver_plan(dict(snapshot=B['timestamp'],source_uuid=B['uuid'],parent=A['timestamp'],parent_uuid=A['uuid'],action='full-baseline'),A,B)
    def test_receipt_validation(self):
        r=dict(schema=1,transport='btrfs-incremental',snapshot=B['timestamp'],source_uuid=B['uuid'],received_uuid=B['uuid'],parent_snapshot=A['timestamp'],parent_source_uuid=A['uuid'],read_only_verified=True,source_send_exit=0,receiver_receive_exit=0)
        self.assertTrue(m.validate_receipt(r,A,B))
        with self.assertRaises(m.Refused): m.validate_receipt(dict(r,received_uuid=A['uuid']),A,B)
        with self.assertRaises(m.Refused): m.validate_receipt(dict(r,receiver_receive_exit=True),A,B)

if __name__=='__main__': unittest.main(verbosity=2)
