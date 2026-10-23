#!/usr/bin/env python3
"""Non-destructive local child-process lifecycle regression. argv[1] = sender source."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

spec = importlib.util.spec_from_file_location('sender', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
STAMP = '20261023-030037Z'
UUID = 'fdcabd00-aa98-7647-bd3a-de5e23186d38'
CANDIDATE = '20261022-030026Z'

CHILD = r'''import json, sys, time
stamp, uuid, candidate, mode = sys.argv[1:]
for i in range(2):
    print(json.dumps({'kind':'transaction-pin-challenge', 'nonce':format(i+1,'064x'), 'snapshot':stamp, 'source_uuid':uuid, 'candidate':candidate}),flush=True)
    response=sys.stdin.readline()
    if not response:
        sys.exit(3)
    if mode == 'abort' and i == 1:
        time.sleep(60)
        sys.exit(4)
if mode == 'error':
    sys.exit(5)
print(json.dumps({'kind':'transaction-completed', 'snapshot':candidate, 'protected_parent':stamp, 'protected_parent_uuid':uuid, 'journal_transaction_completed':True}),flush=True)
'''

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.lock = Path(self.temp.name)/'source.lock'
        self.lock.touch()
        self.seen = []

    def pin(self, role, stamp):
        self.seen.append((role,stamp))
        return {'source_uuid':UUID}

    def run_child(self, mode, *, pin=None):
        return module.run_private_transaction_process(
            [sys.executable,'-u','-c',CHILD,STAMP,UUID,CANDIDATE,mode],
            STAMP,UUID,CANDIDATE,source_lock=self.lock,
            protect_pin=pin or self.pin,abort_timeout=0.1)

    def test_success_keeps_lock_and_two_pin_checks(self):
        result=self.run_child('success')
        self.assertEqual(result['snapshot'], CANDIDATE)
        self.assertEqual(len(self.seen), 2)

    def test_failed_receiver_exits_without_success(self):
        with self.assertRaises(RuntimeError): self.run_child('error')
        self.assertEqual(len(self.seen), 2)

    def test_second_pin_changed_aborts_waiting_child(self):
        def changed(role, stamp):
            self.seen.append((role,stamp))
            return {'source_uuid':UUID if len(self.seen)==1 else '00000000-0000-0000-0000-000000000000'}
        with self.assertRaises(RuntimeError): self.run_child('abort',pin=changed)
        self.assertEqual(len(self.seen), 2)
        # Lock is released after the child is reaped.
        self.assertIsNotNone(self.run_child('success'))

    def test_missing_lock_rejected_without_spawn(self):
        self.lock.unlink()
        with self.assertRaises(RuntimeError): self.run_child('success')

    def test_private_no_cli(self):
        source=Path(sys.argv[1]).read_text()
        main=source.split('def main():',1)[1]
        self.assertNotIn('run_private_transaction_process(',main)

if __name__=='__main__':
    unittest.main(verbosity=2,argv=[sys.argv[0]])
