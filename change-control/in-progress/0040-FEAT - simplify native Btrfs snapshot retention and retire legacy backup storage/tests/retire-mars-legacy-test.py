#!/usr/bin/env python3
"""Offline, non-destructive regression for 0040 mars one-time retirement guards."""
import importlib.util
import pathlib
import tempfile
import json
from unittest import mock

file = pathlib.Path(__file__).resolve().parents[1] / 'tools' / 'retire-mars-legacy.py'
spec = importlib.util.spec_from_file_location('retire_mars_legacy', file)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def refused(callback):
    try:
        callback()
    except (m.Stop, OSError, ValueError, TypeError):
        return
    raise AssertionError('unsafe input accepted')

assert m.PATH_RE.fullmatch('/media/usb/@data/.snapshots/19886/snapshot')
for path in ('/media/usb/@snapshots/root/20261025-120005Z',
             '/media/usb/@snapshots/@data/20261025-120005Z',
             '/media/usb/.snapshots/1/snapshot',
             '/media/usb/@data/.snapshots/../snapshot',
             '/media/usb/@data/.snapshots/1/snapshot/extra',
             '/media/usb/@data/.snapshots/0/snapshot'):
    assert m.PATH_RE.fullmatch(path) is None, path

items = [{'path': f'/media/usb/@data/.snapshots/{i+1}/snapshot',
          'uuid': f'{i:08x}-aaaa-bbbb-cccc-000000000000',
          'subvolume_id': 1000+i, 'snapper_number': i+1} for i in range(17)]
manifest = {'feature': '0040-FEAT', 'host': 'mars', 'expected_count': 17, 'targets': items}
assert len(m.manifest_targets(manifest)) == 17
refused(lambda: m.manifest_targets({**manifest, 'host': 'backup'}))
refused(lambda: m.manifest_targets({**manifest, 'targets': items[:-1]}))
refused(lambda: m.manifest_targets({**manifest, 'targets': items[:-1] + [items[0]]}))
refused(lambda: m.manifest_targets({**manifest, 'targets': items[:-1] + [{**items[-1], 'subvolume_id': items[0]['subvolume_id']}]}))
refused(lambda: m.manifest_targets({**manifest, 'targets': items[:-1] + [{**items[-1], 'snapper_number': 999}]}))
refused(lambda: m.manifest_targets({**manifest, 'targets': items[:-1] + [{**items[-1], 'path': '/media/usb/@snapshots/root/snapshot'}]}))

with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp) / '42'
    d.mkdir()
    (d / 'snapshot').mkdir()
    (d / 'info.xml').write_text('<snapshot><num>42</num></snapshot>')
    path = str(d / 'snapshot')
    with mock.patch.object(m, 'PATH_RE', type('Match', (), {'fullmatch': lambda self, s: mock.Mock(group=lambda n: '42')})()):
        assert m.contents(path) == []
        (d / 'garbage').touch()
        refused(lambda: m.contents(path))
        (d / 'garbage').unlink()
        (d / 'info.xml').write_text('<snapshot><num>43</num></snapshot>')
        refused(lambda: m.contents(path))

with tempfile.TemporaryDirectory() as tmp:
    approval = pathlib.Path(tmp) / 'approval.json'
    approved = {'feature': '0040-FEAT', 'host': 'mars', 'manifest_sha256': m.MANIFEST_SHA256,
                'allow_delete': True, 'accept_legacy_history_loss': True}
    approval.write_text(json.dumps(approved))
    with mock.patch.object(m.os, 'stat', wraps=m.os.stat):
        # Test approval contents using simulated root ownership, without root permissions.
        st = approval.stat()
        mocked = type('S', (), {'st_mode': st.st_mode, 'st_uid': 0})()
        with mock.patch.object(pathlib.Path, 'stat', return_value=mocked):
            m.approval_ok(approval, m.MANIFEST_SHA256)
            for change in ({'accept_legacy_history_loss': False}, {'allow_delete': False}, {'host': 'backup'}, {'manifest_sha256': 'bad'}):
                approval.write_text(json.dumps({**approved, **change}))
                refused(lambda: m.approval_ok(approval, m.MANIFEST_SHA256))

valid_cfg = {'snapshot_root':'/media/usb/@snapshots', 'lock_path':'/run/lock/btrfs-snapshot-manager.lock',
             'writer_lock_path':'/media/usb/@data/backup/.btrfs-snapshot-writer.lock',
             'creation_source_names':['root','@data'], 'required_snapshot_sources':['root','@data'],
             'sources':[{'name':'root','path':'/media/usb'}, {'name':'@data','path':'/media/usb/@data'}],
             'checkpoint_holds': {'required':True}, 'replication_protection': {'required':True}}
m.guard_configuration(valid_cfg)
refused(lambda: m.guard_configuration({**valid_cfg, 'required_snapshot_sources':['@data']}))
refused(lambda: m.guard_configuration({**valid_cfg, 'replication_protection':{'required':False}}))

# Execution cannot progress without a signed-off approval, even if manifest looks valid.
with tempfile.TemporaryDirectory() as tmp:
    mf = pathlib.Path(tmp) / 'manifest.json'
    mf.write_text(json.dumps(manifest))
    with mock.patch.object(m.os, 'geteuid', return_value=0), mock.patch.object(m.os, 'uname', return_value=type('U', (), {'nodename':'mars'})()):
        refused(lambda: m.main(['--manifest', str(mf)]))  # hard-coded checksum rejects test manifest
        refused(lambda: m.main(['--manifest', str(mf), '--execute']))
print('PASS: host, paths, 17 exact identities, metadata, explicit loss approval, config and SHA256 fail-closed')
