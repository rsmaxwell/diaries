#!/usr/bin/env python3
"""Tests for 0045 Step 3 narrow systemd runtime-hash reconciliation.
Uses the already accepted v2 baseline, not host access or backup data.
"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

COMPARATOR = Path(__file__).resolve().parents[1] / 'tools' / 'compare-0045-installed-state.py'
BASELINE_ZIP = None  # Tests use self-contained synthetic v2 manifests.
UNITS = (
    'btrfs-clear-stale-qgroups.service',
    'btrfs-native-push.service',
    'btrfs-snapshot-create.service',
    'btrfs-snapshot-prune.service',
    'diaries-pull.service',
)


def manifest(host):
    managed = {}
    units = {}
    for unit in UNITS:
        path = '/etc/systemd/system/' + unit
        managed[path] = {'type': 'file', 'sha256': 'a'*64, 'mode': '0644', 'uid': 0, 'gid': 0, 'present': True}
        managed[path + '.d'] = {'present': False}
        units[unit] = {
            'ExecStartSHA256': 'b'*64,
            'DropInPaths': '', 'FragmentPath': path,
            'Group': 'root', 'LoadState': 'loaded',
            'UnitFileState': 'static', 'User': 'root',
        }
    units['btrfs-snapshot-create.timer'] = {
        'LoadState': 'loaded', 'ActiveState': 'active', 'UnitFileState': 'enabled',
        'schedule': {'OnCalendar': ['*-*-* *:00:00 UTC'], 'Persistent': ['true']},
    }
    return {
        'schema': '0045-static-installed-v2', 'host': host,
        'managed': managed, 'mutable_state_metadata': {}, 'packages': {},
        'systemd_units': units, 'cron': {}, 'acl': {}, 'mount': {},
    }


class ComparisonCases(unittest.TestCase):
    def check(self, mutation, success):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            before = root/'before'
            after = root/'after'
            before.mkdir()
            after.mkdir()
            for host in ('mars', 'backup'):
                initial = manifest(host)
                final = copy.deepcopy(initial)
                if host == 'mars':
                    mutation(final)
                (before / f'{host}-installed-static.json').write_text(json.dumps(initial), encoding='utf-8')
                (after / f'{host}-installed-static.json').write_text(json.dumps(final), encoding='utf-8')
            result = subprocess.run([sys.executable, str(COMPARATOR), str(before), str(after)],
                                    capture_output=True, text=True, check=False)
            if success:
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('Both hosts static fingerprints identical', result.stdout)
            else:
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('FAIL: mars', result.stdout)
            return result.stdout

    def test_unchanged_state(self):
        self.check(lambda d: None, True)

    def test_five_oneshot_execstart_runtime_hashes_change(self):
        def alter(d):
            for unit in UNITS:
                d['systemd_units'][unit]['ExecStartSHA256'] = 'c'*64
        output = self.check(alter, True)
        self.assertEqual(output.count('RECONCILED:'), 5)

    def test_changed_systemd_unit_file_fails(self):
        def alter(d):
            unit = UNITS[0]
            d['systemd_units'][unit]['ExecStartSHA256'] = 'c'*64
            d['managed']['/etc/systemd/system/'+unit]['sha256'] = 'd'*64
        self.check(alter, False)

    def test_changed_service_user_fails(self):
        def alter(d):
            d['systemd_units'][UNITS[0]]['ExecStartSHA256'] = 'c'*64
            d['systemd_units'][UNITS[0]]['User'] = 'someone-else'
        self.check(alter, False)

    def test_changed_timer_schedule_fails(self):
        self.check(lambda d: d['systemd_units']['btrfs-snapshot-create.timer']['schedule'].update(
            {'OnCalendar': ['*-*-* 08:00:00 UTC']}), False)

    def test_changed_drop_in_fails(self):
        def alter(d):
            unit = UNITS[0]
            path = '/etc/systemd/system/' + unit
            d['systemd_units'][unit]['ExecStartSHA256'] = 'c'*64
            d['managed'][path+'.d/override.conf'] = {'type':'file','sha256':'e'*64}
        self.check(alter, False)

    def test_untracked_drop_in_never_ignored(self):
        def alter(d):
            unit = UNITS[0]
            d['systemd_units'][unit]['ExecStartSHA256'] = 'c'*64
            d['systemd_units'][unit]['DropInPaths'] = '/etc/systemd/system/'+unit+'.d/surprise.conf'
        self.check(alter, False)

    def test_not_loaded_service_never_ignored(self):
        def alter(d):
            unit = UNITS[0]
            d['systemd_units'][unit]['ExecStartSHA256'] = 'c'*64
            d['systemd_units'][unit]['LoadState'] = 'not-found'
        self.check(alter, False)

    def test_unmanaged_unit_fragment_never_ignored(self):
        def alter(d):
            unit = UNITS[0]
            d['systemd_units'][unit]['ExecStartSHA256'] = 'c'*64
            d['systemd_units'][unit]['FragmentPath'] = '/run/systemd/system/'+unit
        self.check(alter, False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
