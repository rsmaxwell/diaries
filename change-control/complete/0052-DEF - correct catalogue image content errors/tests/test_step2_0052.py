"""Offline, non-destructive unit tests for 0052's controlled Image repair."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

p = Path(__file__).resolve().parent.parent/'tools'/'step2-correct-catalogue-images.py'
spec=importlib.util.spec_from_file_location('step2_0052',p)
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class Step2Tests(unittest.TestCase):
    def test_sql_invariants(self):
        h='a'*64
        sql=app.write_sql(h)
        self.assertEqual(sql.count('UPDATE public.image SET'),2)
        self.assertIn('version=0',sql)
        self.assertIn("checksum='"+app.BEFORE[3]['checksum']+"'",sql)
        self.assertIn('version=1, width=776,height=502',sql)
        self.assertIn('version=1, width=720,height=480',sql)
        self.assertIn('FOR UPDATE',sql)
        self.assertIn('RAISE EXCEPTION',sql)
        reverse=app.write_sql(h,reverse=True)
        self.assertIn('version=1',reverse)
        self.assertIn('version=0, width=1060,height=718',reverse)
        self.assertIn('version=0, width=1859,height=1084',reverse)
        self.assertIn('COMMIT;',reverse)
    def test_development_sql_uses_infrastructure_container(self):
        with mock.patch.object(app, 'run', return_value='') as mocked:
            app.psql('development', 'SELECT 1;')
        command = mocked.call_args[0][0]
        self.assertEqual(command[:4], ['docker','exec','-i','diaries-development-db'])

    def test_mismatching_catalogue_rejected(self):
        rows={3:{'id':3,**app.BEFORE[3]},18:{'id':18,**app.BEFORE[18]}}
        app.guard_metadata(rows,app.BEFORE)
        rows[18]['version']=4
        with self.assertRaises(RuntimeError):app.guard_metadata(rows,app.BEFORE)
    def test_backup_atomic_copy_restore(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            orig=root/'served.jpeg';orig.write_bytes(b'original')
            replacement=root/'replacement.jpeg';replacement.write_bytes(b'corrected')
            missing=root/'processed.jpeg'
            manifest=[]
            app.backup_file(orig,root/'backup-1',manifest)
            app.backup_file(missing,root/'backup-2',manifest)
            app.atomic_copy(replacement,orig)
            app.atomic_copy(replacement,missing)
            self.assertEqual(orig.read_bytes(),b'corrected')
            self.assertEqual(missing.read_bytes(),b'corrected')
            app.restore_files(manifest)
            self.assertEqual(orig.read_bytes(),b'original')
            self.assertFalse(missing.exists())

if __name__=='__main__': unittest.main()
