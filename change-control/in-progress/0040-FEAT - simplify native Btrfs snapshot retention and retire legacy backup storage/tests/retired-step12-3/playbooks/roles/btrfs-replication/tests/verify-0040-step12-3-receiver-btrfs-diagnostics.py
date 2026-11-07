#!/usr/bin/env python3
"""Read-only receiver Btrfs diagnostic regressions."""
from pathlib import Path
import importlib.util
from unittest import TestCase, main, mock
f=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-incomplete-inspection.py'
spec=importlib.util.spec_from_file_location('inspection_diagnostics',f)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
B={'timestamp':'20261101-140039Z'}
class Tests(TestCase):
    def test_missing_is_readonly(self):
        with mock.patch.object(m.Path,'is_symlink',return_value=False),mock.patch.object(m.Path,'exists',return_value=False):
            v=m.inspect_btrfs_destination(B)
        self.assertEqual(v['status'],'absent');self.assertFalse(v['cleanup_authorized'])
    def test_btrfs_metadata_is_not_ownership_proof(self):
        out='UUID: 69ef9a57-50ff-9a4e-92ed-8f10560ab1f2\nFlags: -\nReceived UUID: -\n'
        with mock.patch.object(m.Path,'is_symlink',return_value=False),mock.patch.object(m.Path,'exists',return_value=True),mock.patch.object(m.Path,'is_dir',return_value=True):
            v=m.inspect_btrfs_destination(B,runner=lambda *a,**k:mock.Mock(returncode=0,stdout=out))
        self.assertEqual(v['status'],'btrfs-subvolume-observed')
        self.assertFalse(v['journal_ownership_proven']);self.assertFalse(v['process_fencing_proven']);self.assertFalse(v['cleanup_authorized'])
    def test_symlink_refused(self):
        with mock.patch.object(m.Path,'is_symlink',return_value=True):
            with self.assertRaises(m.InspectionRefused):m.inspect_btrfs_destination(B)
    def test_not_a_subvolume_refused(self):
        with mock.patch.object(m.Path,'is_symlink',return_value=False),mock.patch.object(m.Path,'exists',return_value=True),mock.patch.object(m.Path,'is_dir',return_value=True):
            with self.assertRaises(m.InspectionRefused):m.inspect_btrfs_destination(B,runner=lambda *a,**k:mock.Mock(returncode=1,stdout=''))
    def test_bad_uuid_refused(self):
        with mock.patch.object(m.Path,'is_symlink',return_value=False),mock.patch.object(m.Path,'exists',return_value=True),mock.patch.object(m.Path,'is_dir',return_value=True):
            with self.assertRaises(m.InspectionRefused):m.inspect_btrfs_destination(B,runner=lambda *a,**k:mock.Mock(returncode=0,stdout='UUID: garbage'))
    def test_wrong_root_refused(self):
        with self.assertRaises(m.InspectionRefused):m.inspect_btrfs_destination(B,destination_root='/tmp')
if __name__=='__main__':main(verbosity=2)
