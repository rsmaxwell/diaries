"""Source-only full-duplex sender/receiver transaction protocol regression.

Usage: python3 /dev/stdin PUSH_SOURCE RECEIVER_SOURCE
All paths are local source files; no SSH, sudo or Btrfs commands run.
"""
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import socket
import tempfile
import threading
import types
import unittest
import sys


def load(name, filename):
    spec = importlib.util.spec_from_loader(name, SourceFileLoader(name, filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

sender_source, receiver_source = map(str, sys.argv[1:3])
sender = load('sender_under_test', sender_source)
receiver = load('receiver_under_test', receiver_source)
sys.argv = sys.argv[:1]
PARENT='20261023-030037Z'
CANDIDATE='20261012-100003Z'
UUID='fdcabd00-aa98-7647-bd3a-de5e23186d38'

class Connection:
    def __init__(self, sock):
        self.read = sock.makefile('r', encoding='utf-8', newline='\n')
        self.write = sock.makefile('w', encoding='utf-8', newline='\n')
    def close(self):
        self.read.close();self.write.close()

class ProcessAdapter:
    def __init__(self, channel, worker):
        self.stdout=channel.read
        self.stdin=channel.write
        self.worker=worker
    def wait(self, timeout=None):
        self.worker.join(timeout)
        if self.worker.is_alive(): raise TimeoutError('Receiver did not terminate')
        return 1 if self.worker.error else 0

class Tests(unittest.TestCase):
    def run_exchange(self, *, fail_manager=False, invalid_second_pin=False):
        left, right = socket.socketpair()
        left.settimeout(1);right.settimeout(1)
        sender_ch=Connection(left);receiver_ch=Connection(right)
        pins=[];result=[]
        manager_calls=[]
        class Worker(threading.Thread):
            error=None
            def run(self):
                try:
                    with tempfile.TemporaryDirectory() as temp:
                        root=Path(temp);state=root/'state';state.mkdir()
                        lock=root/'manager.lock';lock.touch()
                        writer=state/'writer.lock';writer.touch()
                        config=types.SimpleNamespace(mode='receiver',receiver_state_dir=state,
                            receiver_prune_enabled=False,lock_path=lock,writer_lock_path=writer)
                        def manager_delete(cfg,target,*,protected_stamp,expected_parent_uuid,
                                           verify_source_pin,delete_subvolume):
                            self_test.assertEqual(target,CANDIDATE)
                            self_test.assertEqual(expected_parent_uuid,UUID)
                            verify_source_pin()
                            if fail_manager: raise RuntimeError('injected journal failure')
                            manager_calls.append('committed')
                        mgr=types.SimpleNamespace(receiver_delete_one_locked=manager_delete)
                        def planner(stamp,uuid):
                            return {'snapshot':stamp,'source_uuid':uuid,'authorizes_prune':False,
                                    'deletion_executed':False,'candidates':[CANDIDATE]}
                        result.append(receiver.run_manager_bound_transaction(
                            PARENT,UUID,CANDIDATE,manager=mgr,config=config,
                            incoming=receiver_ch.read,outgoing=receiver_ch.write,
                            planner=planner,delete_subvolume=lambda path:None))
                except Exception as exc:
                    self.error=exc
                finally:
                    try: receiver_ch.close()
                    except OSError: pass
        self_test=self
        worker=Worker(daemon=True)
        worker.start()
        proc=ProcessAdapter(sender_ch,worker)
        def pin(role, stamp):
            self.assertEqual((role,stamp),('protect-prune-source',PARENT))
            pins.append(role)
            return {'source_uuid': '00000000-0000-0000-0000-000000000000' if invalid_second_pin and len(pins)==2 else UUID}
        try:
            if fail_manager or invalid_second_pin:
                with self.assertRaises((RuntimeError,EOFError,OSError,TimeoutError)):
                    sender.answer_transaction_challenges(proc,PARENT,UUID,CANDIDATE,protect_pin=pin)
            else:
                completed=sender.answer_transaction_challenges(proc,PARENT,UUID,CANDIDATE,protect_pin=pin)
                self.assertTrue(completed['journal_transaction_completed'])
        finally:
            # SSH subprocess owner must close stdin when sender rejects a pin.
            # Half-close the transport so the receiver can fail on EOF.
            try: left.shutdown(socket.SHUT_WR)
            except OSError: pass
            worker.join(2)
            try: left.shutdown(socket.SHUT_RD)
            except OSError: pass
            sender_ch.close()
            left.close();right.close()
        self.assertFalse(worker.is_alive(),'Receiver left running')
        return pins,result,manager_calls,worker.error
    def test_successful_full_duplex_two_rounds(self):
        pins,results,calls,error=self.run_exchange()
        self.assertEqual(len(pins),2)
        self.assertEqual(calls,['committed'])
        self.assertIsNone(error)
        self.assertEqual(results[0]['kind'],'transaction-completed')
    def test_manager_failure_no_false_completion(self):
        pins,results,calls,error=self.run_exchange(fail_manager=True)
        self.assertEqual(len(pins),2)
        self.assertFalse(results)
        self.assertFalse(calls)
        self.assertIn('injected journal failure',str(error))
    def test_second_source_pin_changed_fails_closed(self):
        pins,results,calls,error=self.run_exchange(invalid_second_pin=True)
        self.assertEqual(len(pins),2)
        self.assertFalse(results)
        self.assertFalse(calls)
        self.assertIsNotNone(error)
    def test_no_public_delete_switch(self):
        self.assertNotIn("parser.add_argument('--execute-prune'",Path(sender_source).read_text())
        self.assertNotIn("parser.add_argument('--execute-prune'",Path(receiver_source).read_text())

if __name__ == '__main__':
    unittest.main(verbosity=2)
