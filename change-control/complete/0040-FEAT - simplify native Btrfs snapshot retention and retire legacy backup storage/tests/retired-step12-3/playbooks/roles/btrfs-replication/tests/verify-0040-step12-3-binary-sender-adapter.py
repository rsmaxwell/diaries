#!/usr/bin/env python3
import importlib.util
import pathlib
import subprocess
import sys
import unittest

p=pathlib.Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-stream-adapter.py'
s=importlib.util.spec_from_file_location('stream_adapter', p)
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)


def command(code):
    return [sys.executable, '-c', code]

class Tests(unittest.TestCase):
    def test_both_exits_observed(self):
        result=m.run_binary_send_ssh(command('import sys;sys.stdout.buffer.write(b"a"*10000)'),
                command('import sys;sys.exit(0 if len(sys.stdin.buffer.read())==10000 else 7)'))
        self.assertEqual(result, {'source_send_exit':0,'ssh_exit':0})
    def test_sender_failure(self):
        result=m.run_binary_send_ssh(command('import sys;sys.exit(9)'),command('import sys;sys.stdin.buffer.read()'))
        self.assertEqual(result['source_send_exit'],9)
    def test_receiver_failure(self):
        result=m.run_binary_send_ssh(command('import sys;sys.stdout.write("x")'), command('import sys;sys.exit(8)'))
        self.assertEqual(result['ssh_exit'],8)
    def test_timeout_fails_closed(self):
        with self.assertRaises(m.StreamUncertain):
            m.run_binary_send_ssh(command('import time;time.sleep(3)'),command('import sys;sys.stdin.read()'),timeout_seconds=1)
    def test_invalid_deadline(self):
        with self.assertRaises(m.StreamUncertain):
            m.run_binary_send_ssh(command('print(1)'),command('print(1)'),timeout_seconds=True)
    def test_surviving_process_group_cleanup_refuses(self):
        from unittest.mock import patch
        class FakeProcess:
            pid = 99991
            def poll(self): return 0
            def wait(self, timeout=None): return 0
        with patch.object(m, '_group_alive', return_value=True), \
             patch.object(m.os, 'killpg'), \
             patch.object(m.time, 'sleep'):
            ticks = iter([0, 1, 2, 3, 4, 5, 6, 7, 8])
            with self.assertRaises(m.StreamUncertain):
                m._stop_group(FakeProcess(), grace=0.1, clock=lambda: next(ticks))

    def test_no_cli(self):
        self.assertNotIn('if __name__',p.read_text())

if __name__ == '__main__':
    unittest.main(verbosity=2)
