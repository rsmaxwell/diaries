import importlib.util, tempfile, pathlib, os, json, unittest
from unittest.mock import patch
import sys
manager = pathlib.Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('manager_step06', manager)
m = importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
GOOD={'source':'@data','config':'@data','number':19605,'timestamp_utc':'2026-09-28T00:00:38+00:00','decision':'WOULD-DELETE','reasons':[]}
class Guarded(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
  self.policy=pathlib.Path(self.temp.name)/'approval.json'
  self.approval={'enabled':True,'allow_delete':True,'host':'mars','source':'@data','snapper_config':'@data','snapshot_id':19605}
  self.policy.write_text(json.dumps(self.approval))
  self.mockstat=patch.object(m.Path,'stat',autospec=True)
  self.statmock=self.mockstat.start();self.addCleanup(self.mockstat.stop)
  import stat
  self.statmock.return_value=type('S',(),{'st_mode':stat.S_IFREG|0o600,'st_uid':0})()
  self.mocklink=patch.object(m.Path,'is_symlink',return_value=False);self.mocklink.start();self.addCleanup(self.mocklink.stop)
  self.hostname=patch.object(m.socket,'gethostname',return_value='mars');self.hostname.start();self.addCleanup(self.hostname.stop)
 def invoke(self,execute=True,rows=None,source='@data',number=19605):
  rows=rows or [GOOD]
  with patch.object(m,'legacy_plan',return_value={'decisions':rows}) as plan,patch.object(m,'run') as run:
   m.legacy_delete(None,self.policy,source,'@data',number,execute)
   return run,plan
 def test_requires_execute(self):
  with self.assertRaises(m.SnapshotError):self.invoke(False)
 def test_rejects_wrong_host(self):
  self.approval['host']='backup';self.policy.write_text(json.dumps(self.approval))
  with self.assertRaises(m.SnapshotError):self.invoke()
 def test_rejects_disabled(self):
  self.approval['allow_delete']=False;self.policy.write_text(json.dumps(self.approval))
  with self.assertRaises(m.SnapshotError):self.invoke()
 def test_rejects_different_id(self):
  with self.assertRaises(m.SnapshotError):self.invoke(number=19629)
 def test_rejects_keep(self):
  with self.assertRaises(m.SnapshotError):self.invoke(rows=[{**GOOD,'decision':'KEEP'}])
 def test_rejects_missing(self):
  with self.assertRaises(m.SnapshotError):self.invoke(rows=[{**GOOD,'number':123}])
 def test_rejects_symlink(self):
  with patch.object(m.Path,'is_symlink',return_value=True):
   with self.assertRaises(m.SnapshotError):self.invoke()
 def test_rejects_untrusted_mode(self):
  import stat
  self.statmock.return_value=type('S',(),{'st_mode':stat.S_IFREG|0o666,'st_uid':0})()
  with self.assertRaises(m.SnapshotError):self.invoke()
 def test_revalidation_changed(self):
  with patch.object(m,'legacy_plan',side_effect=[{'decisions':[GOOD]},{'decisions':[{**GOOD,'timestamp_utc':'changed'}]}]),patch.object(m,'run') as run:
   with self.assertRaises(m.SnapshotError):m.legacy_delete(None,self.policy,'@data','@data',19605,True)
   run.assert_not_called()
 def test_revalidation_failure(self):
  with patch.object(m,'legacy_plan',side_effect=[{'decisions':[GOOD]},m.SnapshotError('pins unavailable')]),patch.object(m,'run') as run:
   with self.assertRaises(m.SnapshotError):m.legacy_delete(None,self.policy,'@data','@data',19605,True)
   run.assert_not_called()
 def test_one_exact_snapper_delete(self):
  run,_=self.invoke();run.assert_called_once_with(['snapper','-c','@data','delete','19605'])
 def test_snapper_delete_failure_propagates(self):
  with patch.object(m,'legacy_plan',return_value={'decisions':[GOOD]}),patch.object(m,'run',side_effect=m.SnapshotError('snapper failed')) as run:
   with self.assertRaises(m.SnapshotError):m.legacy_delete(None,self.policy,'@data','@data',19605,True)
   run.assert_called_once()
 def test_native_prune_unchanged(self):
  import inspect
  s=inspect.getsource(m.prune)
  self.assertNotIn('legacy_delete',s)
 def test_native_run_unchanged(self):
  import inspect
  self.assertNotIn('legacy_delete(config',inspect.getsource(m.main).split('elif args.command == "run":')[1])
if __name__=='__main__':
 sys.argv=[sys.argv[0]]
 unittest.main(verbosity=2)
