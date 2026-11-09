#!/usr/bin/python3
"""04C source-only unit regressions; no Btrfs, SSH or production mutation."""
import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-transfer-coordinator.py'
spec = importlib.util.spec_from_file_location('transfer_04c', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A = dict(timestamp='20261030-030033Z', uuid='d901ddd2-66c7-0b42-b26c-ab6886273b7a')
B = dict(timestamp='20261030-170009Z', uuid='a9b78fb9-4da6-cf4f-b242-13909f574193')
STATE = dict(schema=1, established=A, pending=B, previous=None)


def fixture(**override):
    calls = []
    reviewed = dict(status='prepared-transfer-review', source=STATE, receiver=STATE,
                    parent=A, candidate=B, state_changed=False, transfer_executed=False,
                    release_executed=False, authorizes_transfer=False,
                    authorizes_promote=False, authorizes_prune=False, authorizes_release=False)
    reviewed.update(override)
    commands = dict(parent=A, candidate=B, authorizes_transfer=False,
                    authorizes_prune=False, authorizes_release=False)
    kw = dict(timestamp=B['timestamp'],
              read_prepared=lambda target: (calls.append('review') or reviewed),
              exact_commands=lambda a, b: (calls.append('commands') or commands),
              receiver_plan=lambda cmd: (calls.append('plan') or dict(snapshot=B['timestamp'],
                   source_uuid=B['uuid'], parent=A['timestamp'], parent_uuid=A['uuid'], action='incremental')),
              execute_once=lambda cmd: (calls.append('execute') or dict(source_send_exit=0, receiver_receive_exit=0)),
              attest_receiver=lambda a,b: (calls.append('attest') or dict(receipt_valid=True,
                    readonly_received_uuid_valid=True, parent=A, candidate=B, state=STATE)),
              transfer_enabled=True)
    return kw,calls


class Tests(unittest.TestCase):
    def test_disabled_fails_before_observation(self):
        kw, calls=fixture();kw['transfer_enabled']=False
        with self.assertRaises(m.TransferRefused):m.transact(**kw)
        self.assertEqual(calls,[])
    def test_exact_success_and_no_release(self):
        kw,calls=fixture();result=m.transact(**kw)
        self.assertEqual(result['status'],'transferred-pending-unpromoted')
        self.assertEqual(calls,['review','commands','plan','execute','attest'])
        self.assertFalse(result['authorizes_release'])
    def test_divergence_fails_before_transfer(self):
        kw,calls=fixture(receiver=dict(STATE,pending=None))
        with self.assertRaises(m.TransferRefused):m.transact(**kw)
        self.assertNotIn('execute',calls)
    def test_authority_fails_before_transfer(self):
        kw,calls=fixture(authorizes_transfer=True)
        with self.assertRaises(m.TransferRefused):m.transact(**kw)
        self.assertNotIn('execute',calls)
    def test_receiver_plan_wrong_rejected(self):
        kw,calls=fixture();kw['receiver_plan']=lambda cmd: dict(action='full')
        with self.assertRaises(m.TransferRefused):m.transact(**kw)
        self.assertNotIn('execute',calls)
    def test_uncertain_execute_never_retries(self):
        kw,calls=fixture()
        def uncertain(_):calls.append('execute');raise TimeoutError('ssh')
        kw['execute_once']=uncertain
        with self.assertRaisesRegex(m.TransferRefused,'NEVER retry'):m.transact(**kw)
        self.assertEqual(calls.count('execute'),1)
    def test_nonzero_exit_refused(self):
        kw,calls=fixture();kw['execute_once']=lambda _:dict(source_send_exit=0, receiver_receive_exit=1)
        with self.assertRaises(m.TransferRefused):m.transact(**kw)
    def test_missing_attestation_refused(self):
        kw,calls=fixture();kw['attest_receiver']=lambda a,b: dict(receipt_valid=False)
        with self.assertRaises(m.TransferRefused):m.transact(**kw)
    def test_attestation_different_state_refused(self):
        kw,calls=fixture();kw['attest_receiver']=lambda a,b: dict(receipt_valid=True,
            readonly_received_uuid_valid=True,parent=A,candidate=B,state=dict(STATE,pending=None))
        with self.assertRaises(m.TransferRefused):m.transact(**kw)
    def test_no_production_main(self):
        self.assertFalse(hasattr(m,'main'))

if __name__=='__main__':unittest.main(verbosity=2)
