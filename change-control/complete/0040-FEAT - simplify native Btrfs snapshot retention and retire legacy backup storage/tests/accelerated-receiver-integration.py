import importlib.util, json, tempfile, pathlib, sys
source=pathlib.Path(sys.argv[1]); template=pathlib.Path(sys.argv[2]); tasks=pathlib.Path(sys.argv[3]); defaults=pathlib.Path(sys.argv[4])
spec=importlib.util.spec_from_file_location('btrfs_manager',source)
import sys as _sys
module=importlib.util.module_from_spec(spec);_sys.modules[spec.name]=module;spec.loader.exec_module(module)
cfg=json.loads(template.read_text())
assert cfg['mode']=='receiver' and cfg['receiver_prune_enabled'] is False
assert cfg['writer_lock_path']==cfg['receiver_state_dir']+'/writer.lock'
assert cfg['sources'][0]['snapshot_directory']=='/@data/mars-received/@data'
assert cfg['retention']==dict(hourly=48,daily=14,weekly=12,monthly=24,yearly=5,minimum_age_minutes=30)
assert 'btrfs_native_receiver_manager_install_enabled: false' in defaults.read_text()
assert tasks.read_text().count('btrfs_native_receiver_manager_install_enabled | bool')==2
with tempfile.TemporaryDirectory() as d:
    f=pathlib.Path(d)/'manager.json';f.write_text(json.dumps(cfg)); parsed=module.load_config(f)
    assert parsed.mode=='receiver' and parsed.receiver_prune_enabled is False
    assert parsed.writer_lock_path==parsed.receiver_state_dir/'writer.lock'
print('PASS: 0040 receiver manager opt-in config, identity, locks and retention; deletion disabled')
