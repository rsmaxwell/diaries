import importlib.util, sys, tempfile, json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
from dataclasses import replace
src=Path(sys.argv[1]); spec=importlib.util.spec_from_file_location('manager',src); m=importlib.util.module_from_spec(spec);sys.modules['manager']=m;spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 root=Path(d); state=root/'state'; state.mkdir(); snaps=root/'snap';snaps.mkdir()
 older='20261001-030000Z'; latest='20261022-030000Z'; protected=latest
 target=snaps/older;target.mkdir();(snaps/latest).mkdir()
 rec={'schema':1,'snapshot':older,'source_uuid':'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','received_uuid':'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','destination':str(target),'read_only_verified':True}
 (state/(older+'.json')).write_text(json.dumps(rec))
 (state/(latest+'.json')).write_text(json.dumps({**rec, 'snapshot':latest, 'destination':str(snaps/latest)}))
 config=m.Config(snapshot_root=root,lock_path=root/'l',writer_lock_path=state/'writer.lock',sources=(m.SnapshotSource('@data',None,snaps),),retention=m.RetentionPolicy(0,0,0,0,0,30),verification=m.VerificationPolicy(False,'','','',None),mode='receiver',receiver_state_dir=state)
 entries=[(latest,datetime(2026,10,22,tzinfo=timezone.utc),snaps/latest),(older,datetime(2026,10,1,tzinfo=timezone.utc),target)]
 def deletion(p):p.rmdir()
 with patch.object(m,'receiver_inventory',return_value=entries),patch.object(m,'validate_prune_candidate'),patch.object(m,'native_prune_subvolume_id',return_value=123):
  def no_pin():raise m.SnapshotError('source pin unavailable')
  try:m.receiver_delete_one_locked(config,older,protected_stamp=protected,verify_source_pin=no_pin,delete_subvolume=deletion)
  except m.SnapshotError:pass
  else:raise AssertionError('missing pin allowed')
  assert target.exists() and not (state/'.receiver-prune-pending.json').exists()
  try:m.receiver_delete_one_locked(config,protected,protected_stamp=protected,verify_source_pin=lambda:None,delete_subvolume=deletion)
  except m.SnapshotError:pass
  else:raise AssertionError('protected parent allowed')
  def crash(p):raise RuntimeError('injected crash')
  try:m.receiver_delete_one_locked(config,older,protected_stamp=protected,verify_source_pin=lambda:None,delete_subvolume=crash)
  except RuntimeError:pass
  else:raise AssertionError('injected crash not raised')
  assert target.exists() and (state/'.receiver-prune-pending.json').exists()
  print('PASS: missing pin refuses deletion; protected parent rejected; crash retains journal')
  (state/'.receiver-prune-pending.json').unlink()
  m.receiver_delete_one_locked(config,older,protected_stamp=protected,verify_source_pin=lambda:None,delete_subvolume=deletion)
  assert not target.exists() and not (state/(older+'.json')).exists() and not (state/'.receiver-prune-pending.json').exists() and (snaps/latest).exists()
  print('PASS: isolated transaction removes target, receipt and journal; parent survives')
 # CLI remains explicitly blocked regardless of enabled state
 try:m.receiver_guarded_prune(replace(config,receiver_prune_enabled=True))
 except m.SnapshotError as e:assert 'blocked' in str(e)
 else:raise AssertionError('production prune not blocked')
 print('PASS: production receiver prune remains disabled')
