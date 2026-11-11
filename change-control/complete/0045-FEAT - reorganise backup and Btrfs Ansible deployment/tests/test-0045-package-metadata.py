#!/usr/bin/env python3
"""Focused no-host-mutation regression for the Step 1 package metadata reader."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from subprocess import CompletedProcess
from unittest import TestCase, main
from unittest.mock import patch

collector_path = Path(__file__).resolve().parents[1] / 'tools' / 'collect-0045-host-state.py'
spec = spec_from_file_location('collector0045', collector_path)
collector = module_from_spec(spec)
spec.loader.exec_module(collector)


class PackageMetadata(TestCase):
    def check_record(self, stdout, expected, returncode=0, stderr=b''):
        command = ['dpkg-query', '-W', '-f=${Status}\t${Version}', 'acl']
        response = CompletedProcess(command, returncode, stdout, stderr)
        with patch.object(collector, 'run', return_value=response) as runner:
            actual = collector.package_fingerprint('acl')
        runner.assert_called_once_with(command)
        self.assertEqual(actual, expected)

    def test_installed_package_with_version(self):
        self.check_record(b'install ok installed\t2.3.2-1\n', {
            'present': True, 'dpkg_status': 'install ok installed',
            'version': '2.3.2-1',
        })

    def test_not_installed_package_empty_version_keeps_tab(self):
        # This is the dpkg-query shape that triggered the 11 Nov failure.
        self.check_record(b'unknown ok not-installed\t', {
            'present': False, 'dpkg_status': 'unknown ok not-installed',
            'version': '',
        })

    def test_config_files_remain_but_no_installed_version(self):
        self.check_record(b'deinstall ok config-files\t\n', {
            'present': False, 'dpkg_status': 'deinstall ok config-files',
            'version': '',
        })

    def test_no_package_record(self):
        self.check_record(b'', {'present': False}, 1,
                          b'dpkg-query: no packages found matching acl\n')

    def test_malformed_record_still_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected package metadata format: acl'):
            self.check_record(b'broken status with no tab', {})


if __name__ == '__main__':
    main(verbosity=2)
