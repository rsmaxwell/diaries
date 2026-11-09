#!/usr/bin/env python3
"""Fail-closed fixed finalisation command tests; no production writes."""
import importlib.util
import io
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch
import sys

P=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-receiver-entry.py'
spec=importlib.util.spec_from_file_location('receiver_entry_finalise_gate',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class Tests(TestCase):
    def test_nonroot_refuses(self):
        with patch.object(m.os,'geteuid',return_value=1000):
            with self.assertRaisesRegex(RuntimeError,'root'):m.finalise_fixed(A,B)
    def test_root_still_refuses_without_sender_proof(self):
        with patch.object(m.os,'geteuid',return_value=0):
            with self.assertRaisesRegex(RuntimeError,'sender completion proof required'):m.finalise_fixed(A,B)
    def test_remote_success_cannot_be_supplied(self):
        with patch.object(sys,'argv',['receiver','--finalise','--parent',A['timestamp'],'--parent-uuid',A['uuid'],'--candidate',B['timestamp'],'--candidate-uuid',B['uuid'],'--source-send-exit','0']):
            with self.assertRaises(SystemExit) as result:m.main()
        self.assertEqual(result.exception.code,2)
    def test_finalise_does_not_load_adapters(self):
        def bad_loader(_):self.fail('untrusted adapter loaded')
        with patch.object(m.os,'geteuid',return_value=0):
            with self.assertRaisesRegex(RuntimeError,'sender completion proof required'):m.finalise_fixed(A,B,loader=bad_loader)
    def test_invalid_identity(self):
        with patch.object(m.os,'geteuid',return_value=0):
            with self.assertRaisesRegex(RuntimeError,'identity'):m.finalise_fixed(dict(A,uuid='oops'),B)
    def test_no_prune_or_promote(self):
        source=P.read_text()
        self.assertNotIn("add_argument('--promote'",source)
        self.assertNotIn("add_argument('--prune'",source)

if __name__=='__main__':main(verbosity=2)
