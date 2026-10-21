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
        if args == ['timedatectl','show','-p','Timezone','--value']:
            return subprocess.CompletedProcess(args, 0, stdout=host_tz[0]+'\n')
        if args[:3] == ['btrfs','property','get']:
            return subprocess.CompletedProcess(args, 0, stdout='ro=true\n')
        raise AssertionError(f'unexpected external command: {args}')
    csv_value = ['']
    host_tz = ['Etc/UTC']
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

        # Snapper's installed CSV omits an explicit timezone offset.
        modern = headers['modern'].split(',')
        zero = {key:'' for key in modern}
        zero['number']='0';zero['type']='single'
        one=dict(zero)
        one.update(number='123',date='2024-05-26 13:00:20',cleanup='timeline')
        import csv,io
        buff=io.StringIO();writer=csv.DictWriter(buff,fieldnames=modern,lineterminator='\n')
        writer.writeheader();writer.writerows([zero,one]);csv_value[0]=buff.getvalue()
        host_tz[0]='Etc/UTC'
        result=m.legacy_snapper_inventory(config,['root=root'])['root']
        assert result[0]['timestamp'].isoformat() == '2024-05-26T13:00:20+00:00'
        print('PASS: installed Snapper timezone-less date accepted on verified UTC host')
        host_tz[0]='Europe/London'
        try:
            m.legacy_snapper_inventory(config,['root=root'])
        except m.SnapshotError as exc:
            assert 'requires verified UTC host' in str(exc)
        else:
            raise AssertionError('non-UTC host was incorrectly accepted')
        print('PASS: timezone-less date rejected on non-UTC host')
        host_tz[0]=''
        try:
            m.legacy_snapper_inventory(config,['root=root'])
        except m.SnapshotError as exc:
            assert 'requires verified UTC host' in str(exc)
        else:
            raise AssertionError('unknown timezone was incorrectly accepted')
        print('PASS: timezone-less date rejected when timezone unavailable')
        # Explicit offsets are usable regardless of host timezone.
        one['date']='2026-10-01T01:00:00+01:00'
        buff=io.StringIO();writer=csv.DictWriter(buff,fieldnames=modern,lineterminator='\n')
        writer.writeheader();writer.writerows([zero,one]);csv_value[0]=buff.getvalue()
        result=m.legacy_snapper_inventory(config,['root=root'])['root']
        assert result[0]['timestamp'].isoformat() == '2026-10-01T00:00:00+00:00'
        print('PASS: explicit timezone offset normalised to UTC')
