#!/usr/bin/env python3
"""Non-destructive guards for the one-off backup legacy retirement tool."""
import importlib.util
import pathlib
import tempfile

p = pathlib.Path(__file__).resolve().parents[1] / 'tools' / 'retire-backup-legacy.py'
spec = importlib.util.spec_from_file_location('retire_backup_legacy', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def rejected(fn):
    try:
        fn()
    except m.Stop:
        return
    raise AssertionError('unsafe condition accepted')

assert m.PATH_PATTERN.fullmatch('/.snapshots/123/snapshot')
assert m.PATH_PATTERN.fullmatch('/@data/.snapshots/123/snapshot')
for value in ('/@data/mars-received/@data/20261025-030026Z',
              '/.snapshots/test-1/snapshot', '/.snapshots/1/../../etc',
              '/.snapshots/1/snapshot/child'):
    assert m.PATH_PATTERN.fullmatch(value) is None

items = [{'path': f'/.snapshots/{i+2}/snapshot', 'uuid': f'{i:08x}-aaaa-bbbb-cccc-000000000000'} for i in range(113)]
raw = dict(feature='0040-FEAT', host='backup', expected_count=113, targets=items)
assert len(m.manifest_targets(raw)) == 113
rejected(lambda: m.manifest_targets({**raw, 'targets': items[:-1]}))
rejected(lambda: m.manifest_targets({**raw, 'targets': items[:-1] + [items[0]]}))
rejected(lambda: m.manifest_targets({**raw, 'targets': items[:-1] + [{'path':'/@data/mars-received/@data/x','uuid':items[-1]['uuid']}]}))

with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp) / '42'
    d.mkdir()
    (d / 'snapshot').mkdir()
    (d / 'info.xml').write_text('<snapshot><num>42</num></snapshot>')
    assert m.exact_contents(d, '42') == []
    (d / 'filelist-41.txt.gz').write_bytes(b'test')
    assert m.exact_contents(d, '42') == ['filelist-41.txt.gz']
    (d / 'unknown').touch()
    rejected(lambda: m.exact_contents(d, '42'))
    (d / 'unknown').unlink()
    (d / 'filelist-41.txt.gz').unlink()
    (d / 'info.xml').write_text('<snapshot><num>99</num></snapshot>')
    rejected(lambda: m.exact_contents(d, '42'))
print('PASS: exact approved paths, UUID manifest, Snapper metadata and filelist guards')
