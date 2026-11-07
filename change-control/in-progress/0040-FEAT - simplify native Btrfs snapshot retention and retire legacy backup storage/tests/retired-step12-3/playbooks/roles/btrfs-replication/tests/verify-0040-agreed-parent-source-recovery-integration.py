#!/usr/bin/python3
"""3H.5t dormant source-prepare recovery integration contract tests."""
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-source-recovery-integration.py'
spec = importlib.util.spec_from_file_location('integration_5t', P)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S={'schema':1,'established':A,'pending':None,'previous':None}
from pathlib import Path
class State:
    def validate(self, s):
        assert set(s)=={'schema','established','pending','previous'}
    def snapshot(self, x):
        assert set(x)=={'timestamp','uuid'}
    def prepare(self, s, x):
        return dict(s,pending=x)

class FakeTransition:
    state=State()
    def __init__(self): self.calls=0
    def transition(self, **k):
        self.calls+=1
        assert k['operation']=='prepare' and k['push_lock_held'] is True
        assert k['transaction_id']==B['timestamp']
        assert k['state_path'].is_absolute() and k['manager_lock'].is_absolute()
        k['verify_peer']('prepare',k['candidate'],k['expected_before'],self.state.prepare(S,B))
        return {'status':'success','state':self.state.prepare(S,B)}
class FakeRecovery:
    def decide(self, before, reply, candidate, checked_candidate, checked_parent, *, validate):
        validate(before)
        if reply['receiver'] != self.expected or checked_candidate != dict(B,verified=True) or checked_parent != dict(A,verified=True):
            raise RuntimeError('bad peer evidence')
        return {'status':'receiver-prepared-source-unprepared','authorizes_transfer':False}

class Tests(unittest.TestCase):
    def setUp(self):
        self.t=FakeTransition(); self.r=FakeRecovery(); self.r.expected=dict(S,pending=B)
        self.read_count=0
        self.reply={'receiver':self.r.expected}
    def read(self, tid):
        self.assertEqual(tid,B['timestamp']); self.read_count+=1; return self.reply
    def verify(self, identity): return dict(identity,verified=True)
    def call(self, **changes):
        args=dict(source_before=S,candidate=B,state_path=Path('/example/.agreed-parent.json'),
                  manager_lock=Path('/run/lock/btrfs-snapshot-manager.lock'),
                  push_lock_held=True,acquire_manager=lambda *x: None,
                  verify_source=self.verify,read_receiver=self.read,transition=self.t,recovery=self.r)
        args.update(changes)
        return m.prepare_source(**args)
    def test_happy(self):
        got=self.call(); self.assertEqual(got['status'],'source-prepared-verified'); self.assertEqual(self.read_count,1)
        self.assertFalse(got['authorizes_prune']); self.assertFalse(got['authorizes_transfer'])
    def test_no_push_lock(self):
        with self.assertRaises(m.Refused): self.call(push_lock_held=False)
        self.assertEqual(self.t.calls,0)
    def test_missing_reader(self):
        with self.assertRaises(m.Refused): self.call(read_receiver=None)
    def test_untrusted_transition_missing(self):
        with self.assertRaises(m.Refused): self.call(transition=None)
    def test_untrusted_recovery_missing(self):
        with self.assertRaises(m.Refused): self.call(recovery=None)
    def test_receiver_unprepared(self):
        self.reply={'receiver':S}
        with self.assertRaisesRegex(m.Refused,'do not retry'): self.call()
    def test_receiver_different_candidate(self):
        self.reply={'receiver':dict(S,pending=A)}
        with self.assertRaises(m.Refused): self.call()
    def test_failed_read(self):
        def fail(tid): raise OSError('ssh loss')
        with self.assertRaisesRegex(m.Refused,'do not retry'): self.call(read_receiver=fail)
    def test_source_pending_rejected(self):
        with self.assertRaises(m.Refused): self.call(source_before=dict(S,pending=B))
    def test_source_previous_rejected(self):
        with self.assertRaises(m.Refused): self.call(source_before=dict(S,previous=B))
    def test_bad_evidence(self):
        with self.assertRaises(m.Refused): self.call(verify_source=lambda x: x)
    def test_repeated_peer_read_rejected(self):
        orig=self.t.transition
        def duplicate(**k):
            k['verify_peer']('prepare',B,S,dict(S,pending=B))
            k['verify_peer']('prepare',B,S,dict(S,pending=B))
        self.t.transition=duplicate
        with self.assertRaises(m.Refused): self.call()
        self.assertEqual(self.read_count,1)
    def test_wrong_transition_operation(self):
        def invalid(**k): k['verify_peer']('promote',B,S,dict(S,pending=B))
        self.t.transition=invalid
        with self.assertRaises(m.Refused): self.call()
    def test_wrong_durable_postcondition(self):
        def incorrect(**k):
            k['verify_peer']('prepare',B,S,dict(S,pending=B))
            return {'status':'success','state':S}
        self.t.transition=incorrect
        with self.assertRaises(m.Refused): self.call()
    def test_no_executable_entrypoint(self):
        src=P.read_text(); self.assertNotIn("if __name__ == '__main__'",src)
        self.assertNotIn('subprocess',src); self.assertNotIn('os.system',src)

if __name__=='__main__': unittest.main(verbosity=2)
