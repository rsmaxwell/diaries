"""0040 Step 3G: read-only receiver lock-held contract (no real Btrfs mutation)."""
import importlib.util, json, sys, tempfile
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('step3g_manager',sys.argv[1]); mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory() as td:
    base=Path(td); state=base/'state'; state.mkdir(); received=base/'received'; received.mkdir()
    stamp='20261023-030037Z'; uuid='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    (state/'writer.lock').touch(); path=received/stamp;path.mkdir()
    (state/(stamp+'.json')).write_text(json.dumps({'source_uuid':uuid}))
    cfgfile=base/'config.json';cfgfile.write_text(json.dumps({'mode':'receiver','snapshot_root':str(base),'receiver_state_dir':str(state),'writer_lock_path':str(state/'writer.lock'),'sources':[{'name':'@data','snapshot_directory':str(received)}]}))
    cfg=mod.load_config(cfgfile)
    entry=(stamp,mod.parse_timestamp(stamp),path)
    with patch.object(mod,'receiver_inventory',return_value=[entry]):
        out=mod.receiver_coordination_check(cfg,stamp,uuid)
        assert out['receiver_verified_under_lock'] and not out['authorizes_prune'] and not out['source_pin_verified']
        for badstamp,baduuid in [(stamp,'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'),('20261022-030037Z',uuid),('invalid',uuid)]:
            try: mod.receiver_coordination_check(cfg,badstamp,baduuid)
            except mod.SnapshotError: pass
            else: raise AssertionError('unsafe parent accepted')
        pending=state/'.receiver-prune-pending.json'; pending.write_text('{}')
        try:mod.receiver_coordination_check(cfg,stamp,uuid)
        except mod.SnapshotError:pass
        else:raise AssertionError('pending transaction accepted')
        pending.unlink()
    # Even enabling receiver_prune_enabled never authorizes deletion.
    assert not cfg.receiver_prune_enabled
    assert '"receiver-coordination-check"' in Path(sys.argv[1]).read_text()
print('PASS: Step 3G lock-held receiver coordination preflight; no deletion authority')
