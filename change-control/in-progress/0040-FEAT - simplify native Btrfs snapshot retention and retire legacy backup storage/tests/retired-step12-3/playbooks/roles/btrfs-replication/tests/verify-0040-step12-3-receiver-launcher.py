#!/usr/bin/env python3
"""Gate B12 static tests for the fixed, separately gated launcher."""
from pathlib import Path
import unittest

LAUNCHER = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-receiver-command'

class GateB12(unittest.TestCase):
    def test_launcher_is_fixed_and_single_exec(self):
        lines = [s.strip() for s in LAUNCHER.read_text().splitlines()
                 if s.strip() and not s.startswith('#')]
        self.assertEqual(lines, ['exec /usr/bin/python3 /usr/local/libexec/btrfs-agreed-parent-receiver-entry.py "$@"'])

    def test_no_sudo_or_shell_interpolation(self):
        contents = LAUNCHER.read_text()
        self.assertNotIn('sudo ', contents)
        self.assertNotIn('eval ', contents)
        self.assertNotIn('sh -c', contents)
        self.assertNotIn('PYTHONPATH=', contents)

    def test_receiver_enforces_root_and_fixed_cli(self):
        entry = (LAUNCHER.parents[0] / 'btrfs-agreed-parent-receiver-entry.py').read_text()
        self.assertIn('os.geteuid() != 0', entry)
        self.assertIn("mode.add_argument('--receive'", entry)
        self.assertIn("mode.add_argument('--finalise'", entry)
        self.assertIn("mode.add_argument('--session'", entry)
        self.assertIn("mode.add_argument('--receipt'", entry)
        self.assertNotIn("mode.add_argument('--promote'", entry)

if __name__ == '__main__':
    unittest.main(verbosity=2)
