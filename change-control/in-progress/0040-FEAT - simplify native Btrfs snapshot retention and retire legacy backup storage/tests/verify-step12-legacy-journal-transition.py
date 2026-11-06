#!/usr/bin/env python3
"""Disposable fixture coverage for 0040 legacy journal transition utility."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).parents[1] / 'tools/step12-legacy-journal-transition.py'
spec = importlib.util.spec_from_file_location('step12legacy', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A='20261030-170009Z'
D='20261030-030033Z'
B='20261101-140039Z'
C='20261102-140039Z'
U='11111111-1111-1111-1111-111111111111'

class Cases(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.state=root/'state'; self.state.mkdir()
        self.received=root/'received'; self.received.mkdir()
        self.manager=root/'manager.lock'; self.manager.touch()
        self.writer=self.state/'writer.lock'; self.writer.touch()
        self.journal=self.state/'.agreed-parent-transfer-pending.json'
        self.archive=self.state/'.0040-retired-legacy'
        self.value={'schema':1,'status':'receiving','parent':{'timestamp':D,'uuid':U},
                    'candidate':{'timestamp':A,'uuid':U},'nonce':'a'*64}
        self.journal.write_text(json.dumps(self.value)+'\n')
        self.journal.chmod(0o600)
        self.digest=hashlib.sha256(self.journal.read_bytes()).hexdigest()
        self.patchers=[patch.object(m, 'REQUIRED_OWNER_UID', os.getuid()),
            patch.object(m, 'STATE', self.state),
            patch.object(m, 'JOURNAL', self.journal),
            patch.object(m, 'ARCHIVE_DIR', self.archive),
            patch.object(m, 'RECEIVER_ROOT', self.received),
            patch.object(m, 'SIMPLE_RECEIVER', self.state/'.simple-agreed-parent.json'),
            patch.object(m, 'MANAGER', self.manager),
            patch.object(m, 'WRITER', self.writer),
            patch.object(m, 'filesystem', return_value=None),
            patch.object(m, 'info', return_value={
                'UUID':U,'Received UUID':U,'Flags':'readonly','Parent UUID':U})]
        for p in self.patchers:
            p.start()
            self.addCleanup(p.stop)

    def test_archive_is_single_journal_move_with_digest(self):
        m.archive(self.digest,A)
        self.assertFalse(self.journal.exists())
        destination=self.archive/('.agreed-parent-transfer-pending.'+self.digest+'.json')
        self.assertEqual(destination.read_bytes(),(json.dumps(self.value)+'\n').encode())
        self.assertEqual(self.archive.stat().st_mode & 0o777, 0o700)
        self.assertEqual(destination.stat().st_mode & 0o777, 0o600)

    def test_changed_hash_refused_without_modification(self):
        with self.assertRaisesRegex(m.Refuse,'changed since audit'):
            m.archive('0'*64,A)
        self.assertTrue(self.journal.exists())
        self.assertFalse(self.archive.exists())

    def test_existing_candidate_prevents_archive(self):
        (self.received/A).mkdir()
        with self.assertRaisesRegex(m.Refuse,'candidate exists'):
            m.archive(self.digest,A)
        self.assertTrue(self.journal.exists())

    def test_staging_binding_prevents_archive(self):
        self.value['staging']={'directory_dev':1,'directory_ino':2}
        self.journal.write_text(json.dumps(self.value))
        new_digest=hashlib.sha256(self.journal.read_bytes()).hexdigest()
        with self.assertRaisesRegex(m.Refuse,'Staging/publication'):
            m.archive(new_digest,A)
        self.assertTrue(self.journal.exists())

    def test_nonce_stage_prevents_archive(self):
        (self.received/('.receive-'+'a'*64)).mkdir()
        with self.assertRaisesRegex(m.Refuse,'staged object'):
            m.archive(self.digest,A)
        self.assertTrue(self.journal.exists())

    def test_receipt_prevents_archive(self):
        (self.state/(A+'.json')).touch()
        with self.assertRaisesRegex(m.Refuse,'receipt'):
            m.archive(self.digest,A)
        self.assertTrue(self.journal.exists())

    def test_second_legacy_marker_prevents_archive(self):
        (self.state/'.receiver-prune-pending.json').touch()
        with self.assertRaisesRegex(m.Refuse,'Additional active'):
            m.archive(self.digest,A)
        self.assertTrue(self.journal.exists())

    def test_existing_simple_state_prevents_archive(self):
        (self.state/'.simple-agreed-parent.json').touch()
        with self.assertRaisesRegex(m.Refuse,'already exists'):
            m.archive(self.digest,A)
        self.assertTrue(self.journal.exists())

    def completed_receipt(self, *, matching_parent=True):
        candidate=self.value['candidate']['timestamp']
        (self.received/candidate).mkdir(exist_ok=True)
        receipt = {
            'schema':1, 'transport':'btrfs-incremental',
            'snapshot':candidate, 'source_uuid':U, 'received_uuid':U,
            'source_filesystem_uuid':m.SOURCE_FS,
            'receiver_filesystem_uuid':m.RECEIVER_FS,
            'destination':str(self.received/candidate),
            'read_only_verified':True, 'source_send_exit':0, 'receiver_receive_exit':0,
            'parent_snapshot':self.value['parent']['timestamp'] if matching_parent else B,
            'parent_source_uuid':self.value['parent']['uuid'],
        }
        path=self.state/(candidate+'.json')
        path.write_text(json.dumps(receipt)+'\n')
        path.chmod(0o600)
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_explicit_completed_candidate_with_receipt_archives_journal_only(self):
        digest=self.completed_receipt()
        snap=self.received/self.value['candidate']['timestamp']
        receipt=self.state/(self.value['candidate']['timestamp']+'.json')
        before=receipt.read_bytes()
        m.archive(self.digest,self.value['candidate']['timestamp'],
                  allow_completed=True,expected_receipt_sha=digest)
        self.assertFalse(self.journal.exists())
        self.assertTrue(snap.exists())
        self.assertEqual(before,receipt.read_bytes())

    def test_completed_candidate_refused_without_explicit_optin(self):
        digest=self.completed_receipt()
        with self.assertRaisesRegex(m.Refuse,'explicit completed-candidate opt-in required'):
            m.archive(self.digest,self.value['candidate']['timestamp'])
        self.assertTrue(self.journal.exists())

    def test_completed_candidate_receipt_digest_change_refused(self):
        digest=self.completed_receipt()
        with self.assertRaisesRegex(m.Refuse,'receipt changed since audit'):
            m.archive(self.digest,self.value['candidate']['timestamp'],
                      allow_completed=True,expected_receipt_sha='0'*64)
        self.assertTrue(self.journal.exists())

    def test_completed_candidate_bad_parent_lineage_refused(self):
        digest=self.completed_receipt(matching_parent=False)
        with self.assertRaisesRegex(m.Refuse,'receipt does not match journal lineage'):
            m.archive(self.digest,self.value['candidate']['timestamp'],
                      allow_completed=True,expected_receipt_sha=digest)
        self.assertTrue(self.journal.exists())

    def test_completed_candidate_missing_receipt_refused(self):
        (self.received/self.value['candidate']['timestamp']).mkdir()
        with self.assertRaisesRegex(m.Refuse,'Completed candidate must have both snapshot and receipt'):
            m.archive(self.digest,self.value['candidate']['timestamp'],
                      allow_completed=True,expected_receipt_sha='0'*64)
        self.assertTrue(self.journal.exists())

    def test_completed_candidate_receipt_without_candidate_refused(self):
        digest=self.completed_receipt()
        (self.received/self.value['candidate']['timestamp']).rmdir()
        with self.assertRaisesRegex(m.Refuse,'Completed candidate must have both snapshot and receipt'):
            with patch.object(m, 'info', side_effect=lambda root, name: None if name == A else
                              {'UUID':U,'Received UUID':U,'Flags':'readonly','Parent UUID':U}):
                m.archive(self.digest,self.value['candidate']['timestamp'],
                          allow_completed=True,expected_receipt_sha=digest)
        self.assertTrue(self.journal.exists())

    def test_completed_candidate_later_than_common_parent_refused(self):
        self.value['candidate']['timestamp']=C
        self.journal.write_text(json.dumps(self.value)+'\n')
        digest_journal=hashlib.sha256(self.journal.read_bytes()).hexdigest()
        digest=self.completed_receipt()
        with self.assertRaisesRegex(m.Refuse,'not older than initial agreed parent'):
            m.archive(digest_journal,C,allow_completed=True,expected_receipt_sha=digest)
        self.assertTrue(self.journal.exists())

    def test_completed_candidate_readonly_mismatch_refused(self):
        digest=self.completed_receipt()
        with patch.object(m, 'info', side_effect=lambda root, name:
                {'UUID':U,'Received UUID':'-' if name == A else U,
                 'Flags':'readonly','Parent UUID':U}):
            with self.assertRaisesRegex(m.Refuse,'Btrfs identity/read-only mismatch'):
                m.archive(self.digest,self.value['candidate']['timestamp'],
                          allow_completed=True,expected_receipt_sha=digest)
        self.assertTrue(self.journal.exists())

    def test_wrong_expected_candidate_refuses(self):
        with self.assertRaisesRegex(m.Refuse,'Unexpected journal candidate'):
            m.archive(self.digest,B)
        self.assertTrue(self.journal.exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
