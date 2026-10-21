"""Read-only 0037 Step 4 regression: installed Snapper CSV header variants."""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

path = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('snapshot_manager_csv_0037', path)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

with tempfile.TemporaryDirectory() as temp:
    source_path = Path(temp) / 'root'
    source_path.mkdir()
    source = m.SnapshotSource('root', source_path)
    config = m.Config(Path(temp)/'repo', Path(temp)/'lock', None, (source,),
                      m.RetentionPolicy(48,14,12,24,5,30),
                      m.VerificationPolicy(False,'','','',None))
    config_text = f'Key | Value\nSUBVOLUME | {source_path}\n'
    snapdir = source_path / '.snapshots' / '123' / 'snapshot'
    snapdir.mkdir(parents=True)
    headers = {
        'modern': 'number,type,pre-number,date,user,used-space,cleanup,description,userdata,active,default,subvolume,config',
        'historical': '#,Type,Pre #,Date,User,Cleanup,Description,Userdata',
    }
    def run_with_csv(args):
        if 'get-config' in args:
            return subprocess.CompletedProcess(args, 0, stdout=config_text)
        if 'list' in args:
            return subprocess.CompletedProcess(args, 0, stdout=csv_value[0])
        if args[:3] == ['btrfs','property','get']:
            return subprocess.CompletedProcess(args, 0, stdout='ro=true\n')
        raise AssertionError(f'unexpected external command: {args}')
    csv_value = ['']
    with (patch.object(m, 'run', side_effect=run_with_csv),
          patch.object(m, 'require_btrfs'), patch.object(m, 'require_subvolume')):
        for label, header in headers.items():
            cols = header.split(',')
            zero = {key: '' for key in cols}
            zero[cols[0]]='0'; zero[cols[1]]='single'
            import csv, io
            def encode(rows):
                sio=io.StringIO(); w=csv.DictWriter(sio,fieldnames=cols,lineterminator='\n')
                w.writeheader(); w.writerows(rows); return sio.getvalue()
            csv_value[0] = encode([zero])
            assert m.legacy_snapper_inventory(config,['root=root']) == {'root': []}
            print(f'PASS: {label} empty Snapper CSV')
            one=dict(zero); one[cols[0]]='123'
            one[[x for x in cols if x.lower() == 'date'][0]]='2026-10-01T00:00:00+00:00'
            one[[x for x in cols if x.lower() == 'cleanup'][0]]='timeline'
            csv_value[0] = encode([zero,one])
            result = m.legacy_snapper_inventory(config,['root=root'])['root']
            assert len(result)==1 and result[0]['number']==123 and result[0]['cleanup']=='timeline'
            print(f'PASS: {label} numbered Snapper CSV')
        csv_value[0] = 'number,#,type,date,cleanup\n0,0,single,,\n'
        try:
            m.legacy_snapper_inventory(config,['root=root'])
        except m.SnapshotError as exc:
            assert 'unexpected Snapper CSV columns' in str(exc)
        else:
            raise AssertionError('ambiguous snapshot number headers accepted')
        print('PASS: ambiguous numeric headers rejected')
