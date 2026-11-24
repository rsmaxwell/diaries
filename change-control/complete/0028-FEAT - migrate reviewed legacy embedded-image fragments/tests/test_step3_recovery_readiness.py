import pathlib
import tempfile
import unittest
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from step3_recovery_readiness_summary import summarize,parse_status

class RecoveryReadiness(unittest.TestCase):
 def test_status_healthy(self):
  raw='=== DIARIES BACKUP STATUS ===\n'+ '{"component":"diaries","health":"healthy","latest":{"backupId":"20261124-000000Z","lastRetainedSnapshot":"20261124-080000Z"},"warnings":[],"evidence":"retained manifest identity"}'+'\nDIARIES_BACKUP_STATUS_EXIT=0\n'
  self.assertEqual(parse_status(raw)['latest']['backupId'],'20261124-000000Z')
 def test_status_exit_error_not_healthy(self):
  raw='=== DIARIES BACKUP STATUS ===\n{"component":"diaries","health":"healthy"}\nDIARIES_BACKUP_STATUS_EXIT=2\n'
  self.assertEqual(parse_status(raw)['health'],'error')
 def test_missing_exit_marker_not_healthy(self):
  raw='=== DIARIES BACKUP STATUS ===\n{"component":"diaries","health":"healthy"}\n'
  self.assertEqual(parse_status(raw)['health'],'error')
 def test_missing_status_not_healthy(self):
  self.assertEqual(parse_status('noise')['health'],'unavailable')
 def test_collection_never_approves(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   (root/'PROBE-STATUS.tsv').write_text('host\tprobe\texit_status\npluto\truntime-and-backup-metadata\t0\nmars\tretained-backup-status\t0\nbackup\tretained-backup-status\t0\n')
   for host in ('mars','backup'):
    (root/(host+'-retained-backup-status.log')).write_text('=== DIARIES BACKUP STATUS ===\n{"component":"diaries","health":"healthy","latest":{"backupId":"20261124-000000Z"},"evidence":"retained manifest identity"}\nDIARIES_BACKUP_STATUS_EXIT=0\n')
   result=summarize(root/'PROBE-STATUS.tsv')
   self.assertEqual(result['probeCollection'],'COMPLETE')
   self.assertEqual(result['retainedIdentityAlignment'],'SAME_LATEST_BACKUP_ID_NOT_RESTORE_VERIFIED')
   self.assertFalse(result['productionApplyAuthorised'])
   self.assertEqual(result['matchingFreshProductionDBAndFilesRecoveryPoint'],'NOT_VERIFIED')
 def test_probe_failure_marks_incomplete(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   (root/'PROBE-STATUS.tsv').write_text('host\tprobe\texit_status\npluto\truntime-and-backup-metadata\t1\nmars\tretained-backup-status\t0\nbackup\tretained-backup-status\t0\n')
   result=summarize(root/'PROBE-STATUS.tsv')
   self.assertEqual(result['probeCollection'],'INCOMPLETE')
 def test_missing_host_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   path=pathlib.Path(d)/'PROBE-STATUS.tsv'
   path.write_text('host\tprobe\texit_status\npluto\tx\t0\nmars\tx\t0\n')
   with self.assertRaises(ValueError):summarize(path)

if __name__=='__main__':unittest.main()
