#!/usr/bin/env python3
"""Disposable real-kernel flock lifetime regression; no Btrfs or production paths."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

class LockLifetime(unittest.TestCase):
    def test_surviving_worker_retains_both_locks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            locks = [root / 'manager', root / 'writer']
            ready = root / 'ready'
            for path in locks: path.touch()
            # Coordinator holds flock, exec worker inherits the same open-file
            # descriptions, then coordinator exits abruptly (simulated crash).
            script = '''import fcntl, os, subprocess, sys, time
files = [open(p, "r+") for p in sys.argv[1:3]]
for f in files: fcntl.flock(f, fcntl.LOCK_EX)
worker = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(1.2)'],
                          pass_fds=tuple(f.fileno() for f in files),
                          stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, start_new_session=True)
open(sys.argv[3], 'w').write(str(worker.pid))
os._exit(7)
'''
            owner = subprocess.Popen([sys.executable, '-c', script, *map(str, locks), str(ready)])
            owner.wait(timeout=5)
            self.assertEqual(owner.returncode, 7)
            self.assertTrue(ready.exists())
            handles = [p.open('r+') for p in locks]
            try:
                for h in handles:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
                deadline = time.monotonic() + 8
                for h in handles:
                    while True:
                        try:
                            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            break
                        except BlockingIOError:
                            if time.monotonic() > deadline:
                                self.fail('worker-held lock not released within deadline')
                            time.sleep(.1)
                    fcntl.flock(h, fcntl.LOCK_UN)
            finally:
                for h in handles: h.close()

if __name__ == '__main__': unittest.main(verbosity=2)
