import importlib.util,json,tempfile,sys
from pathlib import Path
from unittest.mock import patch
P=Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd()/'roles/snapshots/files/btrfs-snapshot-manager.py'
spec=importlib.util.spec_from_file_location('snapshot_step3b',P); mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory() as td:
    p=Path(td); d=p/'received';d.mkdir();state=p/'state';state.mkdir()
    raw={'mode':'receiver','snapshot_root':str(p),'receiver_state_dir':str(state),'sources':[{'name':'@data','snapshot_directory':str(d)}]}
    config=p/'config.json';config.write_text(json.dumps(raw))
    c=mod.load_config(config)
    assert c.mode=='receiver' and mod.source_directory(c,c.sources[0])==d
    for command in ['create','prune','run','hold-add','legacy-prune']:
        args=['--config',str(config),command]
        if command=='hold-add':args+=['20261023-030037Z','--reason','test']
        assert mod.main(args)==2,command
    with patch.object(mod,'preflight'),patch.object(mod,'run') as run:
        stamp='20261023-030037Z'; sub=d/stamp;sub.mkdir()
        data={'schema':1,'snapshot':stamp,'destination':str(sub),'source_uuid':'a'*36,'received_uuid':'a'*36,'read_only_verified':True}
        (state/(stamp+'.json')).write_text(json.dumps(data))
        from subprocess import CompletedProcess
        def fake(cmd,check=True):
            return CompletedProcess(cmd,0, 'Received UUID: '+('a'*36)+'\n' if cmd[1]=='subvolume' else 'ro=true\n','')
        run.side_effect=fake
        mod.receiver_inventory(c)
        data['source_uuid']='b'*36;(state/(stamp+'.json')).write_text(json.dumps(data))
        try:mod.receiver_inventory(c)
        except mod.SnapshotError:pass
        else:raise AssertionError('bad receipt accepted')
    raw.pop('receiver_state_dir');config.write_text(json.dumps(raw))
    try:mod.load_config(config)
    except mod.SnapshotError:pass
    else:raise AssertionError('missing receiver state accepted')
    raw.pop('mode');raw['sources']=[{'name':'@data','path':str(p)}];config.write_text(json.dumps(raw));assert mod.load_config(config).mode=='source'
print('PASS: Step 3B receiver read-only and source backwards compatibility')
