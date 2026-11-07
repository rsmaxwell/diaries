#!/usr/bin/python3
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
import stat
from unittest.mock import patch
from contextlib import ExitStack

P = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-locked-get-state.py'
spec=importlib.util.spec_from_file_location('locked_get', P)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
T='20261030-170009Z'
RESPONSE={'schema':1,'receiver':{},'authorizes_prepare':False,'authorizes_promote':False,'authorizes_transfer':False,'authorizes_prune':False,'authorizes_release':False}
class Tests(unittest.TestCase):
    def test_owner_contract(self):
        self.assertEqual(m.expected_owner(m.MANAGER_LOCK), 0)
        with patch.object(m.pwd, 'getpwnam', return_value=SimpleNamespace(pw_uid=1001)) as lookup:
            self.assertEqual(m.expected_owner(m.PUSH_LOCK), 1001)
            lookup.assert_called_once_with('richard')
        with self.assertRaisesRegex(RuntimeError, 'unknown source lock'):
            m.expected_owner(Path('/tmp/other.lock'))

    def test_operator_push_lock_accepted(self):
        m.validate_lock_metadata(SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=1, st_uid=1001), 1001)

    def test_root_manager_lock_accepted(self):
        m.validate_lock_metadata(SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=1, st_uid=0), 0)

    def test_swapped_owners_rejected(self):
        for uid, expected in [(0, 1001), (1001, 0)]:
            with self.subTest(uid=uid):
                with self.assertRaisesRegex(RuntimeError, 'unsafe source lock'):
                    m.validate_lock_metadata(SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=1, st_uid=uid), expected)

    def test_unsafe_permissions_or_links_rejected(self):
        for mode, links in [(0o620, 1), (0o660, 1), (0o644, 1), (0o600, 2)]:
            with self.subTest(mode=mode, links=links):
                with self.assertRaisesRegex(RuntimeError, 'unsafe source lock'):
                    m.validate_lock_metadata(SimpleNamespace(st_mode=stat.S_IFREG | mode, st_nlink=links, st_uid=1001), 1001)

    def test_non_regular_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'unsafe source lock'):
            m.validate_lock_metadata(SimpleNamespace(st_mode=stat.S_IFLNK | 0o600, st_nlink=1, st_uid=1001), 1001)

    def test_order_and_lifetime(self):
        events=[]
        class Lock:
            def __init__(self, name): self.name=name
            def __enter__(self):events.append('enter:'+self.name);return self
            def __exit__(self,*a):events.append('exit:'+self.name)
        def acquire(stack,path):
            events.append('acquire:'+path.name)
            stack.enter_context(Lock(path.name))
        def read(tid,**kw):
            self.assertEqual(tid,T);self.assertIs(kw['source_lock_held'],True)
            events.append('transport');return dict(RESPONSE)
        self.assertEqual(m.get_state(T,acquire_lock=acquire,transport=SimpleNamespace(get_state=read)),RESPONSE)
        self.assertEqual(events,['acquire:.native-push.lock','enter:.native-push.lock',
            'acquire:btrfs-snapshot-manager.lock','enter:btrfs-snapshot-manager.lock','transport',
            'exit:btrfs-snapshot-manager.lock','exit:.native-push.lock'])
    def test_first_lock_failure_blocks_io(self):
        with self.assertRaisesRegex(RuntimeError,'busy'):
            m.get_state(T,acquire_lock=lambda *a: (_ for _ in ()).throw(RuntimeError('busy')),
                transport=SimpleNamespace(get_state=lambda *a,**kw:self.fail('called')))
    def test_second_lock_failure_blocks_io(self):
        calls=[]
        def acquire(stack,path):
            calls.append(path)
            if len(calls)==2: raise RuntimeError('busy')
        with self.assertRaisesRegex(RuntimeError,'busy'):
            m.get_state(T,acquire_lock=acquire,transport=SimpleNamespace(get_state=lambda *a,**kw:self.fail('called')))
        self.assertEqual(calls,[m.PUSH_LOCK,m.MANAGER_LOCK])
    def test_transport_failure_propagates(self):
        with self.assertRaisesRegex(RuntimeError,'SSH failed'):
            m.get_state(T,acquire_lock=lambda *a:None,transport=SimpleNamespace(get_state=lambda *a,**kw: (_ for _ in ()).throw(RuntimeError('SSH failed'))))
    def test_mutation_authority_rejected(self):
        bad=dict(RESPONSE,authorizes_prepare=True)
        with self.assertRaisesRegex(RuntimeError,'mutation authority'):
            m.get_state(T,acquire_lock=lambda *a:None,transport=SimpleNamespace(get_state=lambda *a,**kw:bad))
    def test_no_public_lock_boolean(self):
        import inspect
        self.assertNotIn('source_lock_held',inspect.signature(m.get_state).parameters)
    def test_read_only_cli(self):
        source=P.read_text()
        self.assertIn("if __name__ == '__main__'",source)
        self.assertIn('--transaction-id',source)
        self.assertNotIn('btrfs send',source)
        self.assertNotIn('btrfs receive',source)
if __name__=='__main__':unittest.main(verbosity=2)
