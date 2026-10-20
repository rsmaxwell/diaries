import importlib.util, io, json, contextlib, sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('roles/snapshots/files/btrfs-snapshot-manager.py')
spec=importlib.util.spec_from_file_location('manager37',p)
m=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=m
spec.loader.exec_module(m)
dt=lambda s: datetime.fromisoformat(s+'+00:00')
source=m.SnapshotSource('@data',Path('/fake/data'))
cfg=m.Config(Path('/fake/repo'),Path('/tmp/l'),None,(source,),m.RetentionPolicy(0,0,0,3,0,30),m.VerificationPolicy(False,'','','',None))
legacy=[dict(source='@data', config='@data',number=i,timestamp=dt(t),kind='single',cleanup='timeline') for i,t in ((1,'2025-09-01T00:00:00'),(2,'2026-10-17T00:00:00'),(3,'2026-10-19T00:00:00'))]
with patch.object(m,'preflight'),patch.object(m,'managed_snapshot_sets',return_value=([('20261018-000000Z',dt('2026-10-18T00:00:00'))],{})),patch.object(m,'replication_pins',return_value=set()),patch.object(m,'read_checkpoint_holds',return_value={}),patch.object(m,'legacy_snapper_inventory',return_value={'@data':legacy}):
    buff=io.StringIO()
    with contextlib.redirect_stdout(buff): m.legacy_plan(cfg,['@data=@data'],True)
    payload=json.loads(buff.getvalue())
    decisions={e['number']:e for e in payload['decisions']}
    assert decisions[1]['decision']=='KEEP',decisions
    assert decisions[3]['decision']=='KEEP',decisions
    assert decisions[2]['decision']=='WOULD-DELETE',decisions
    assert payload['authorizes_deletion'] is False
print('PASS: native precedence / legacy history / newest legacy anchor / read-only output')
