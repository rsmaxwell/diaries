"""0040 Step 3D: receiver prune must fail closed until all guards hold.
Run via python3 <script> <manager-file>; makes no Btrfs calls or deletions.
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('snapshot_step3d', sys.argv[1])
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    root=Path(td); state=root/'state'; state.mkdir(); received=root/'received'; received.mkdir()
    stamp='20261023-030037Z'; uuid='a'*36
    (received/stamp).mkdir()
    (state/(stamp+'.json')).write_text(json.dumps({'source_uuid':uuid}))
    cfg=root/'config.json'
    cfg.write_text(json.dumps({'mode':'receiver','snapshot_root':str(root),
        'receiver_state_dir':str(state), 'writer_lock_path':str(state/'writer.lock'),
        'sources':[{'name':'@data','snapshot_directory':str(received)}],
        'retention': {'hourly':48,'daily':14,'weekly':12,'monthly':24,'yearly':5}}))
    (state/'writer.lock').touch()
    config=mod.load_config(cfg)
    assert config.receiver_prune_enabled is False
    approval=root/'approval.json'
    approval.write_text(json.dumps({'schema':1,'operation':'receiver-prune',
        'common_parent':{'snapshot':stamp,'source_uuid':uuid},
        'delete':['20261022-030037Z']}))
    for bad in [None,root/'missing']:
        try: mod.receiver_guarded_prune(config,bad)
        except mod.SnapshotError: pass
        else: raise AssertionError('missing approval accepted')
    data=json.loads(cfg.read_text()); data['receiver_prune_enabled']=True; cfg.write_text(json.dumps(data)); config=mod.load_config(cfg)
    pending=state/'.receiver-prune-pending.json'; pending.write_text('{}')
    try: mod.receiver_guarded_prune(config,approval)
    except mod.SnapshotError: pass
    else: raise AssertionError('pending journal ignored')
    pending.unlink()
    # Validation can be simulated; no destructive command may be invoked.
    fake_entries=[(stamp,mod.parse_timestamp(stamp),received/stamp)]
    with patch.object(mod,'receiver_inventory',return_value=fake_entries), patch.object(mod,'run',side_effect=AssertionError('unexpected btrfs mutation')):
        try: mod.receiver_guarded_prune(config,approval)
        except mod.SnapshotError: pass
        else: raise AssertionError('unrecognised candidate approved')
    assert (received/stamp).is_dir() and (state/(stamp+'.json')).is_file()
print('PASS: Step 3D refuses missing approval, pending journal and unknown candidate (no mutation)')
