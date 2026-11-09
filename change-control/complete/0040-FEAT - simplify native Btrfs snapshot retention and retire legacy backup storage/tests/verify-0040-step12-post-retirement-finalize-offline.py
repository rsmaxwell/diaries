#!/usr/bin/env python3
"""Offline safeguards for receipt-only finalisation after 0040 retirement."""
import hashlib
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
from unittest.mock import patch

TOOL = Path(__file__).resolve().parents[1] / 'tools' / 'retire-0040-obsolete-code.py'
loader = importlib.machinery.SourceFileLoader('retire0040finalize', str(TOOL))
spec = importlib.util.spec_from_loader(loader.name, loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)

stamp = '20261108-085914Z'
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    rollback = root / 'rollback'
    rollback.mkdir()
    paths = {
        host: [f'/usr/local/bin/btrfs-agreed-parent-{host}-{n}' for n in (1,2)]
        for host in ('mars','backup')
    }
    records = {}
    hashes = {}
    for host in ('mars','backup'):
        records[host] = []
        archive_path = rollback / f'legacy-code-{host}-{stamp}.tar'
        with tarfile.open(archive_path, 'w') as tar:
            for path in paths[host]:
                content = path.encode()
                item = {'path':path, 'sha256':hashlib.sha256(content).hexdigest(),
                        'mode':0o755, 'bytes':len(content)}
                records[host].append(item)
                info = tarfile.TarInfo(path.lstrip('/'))
                info.size = len(content)
                info.uid = info.gid = 0
                info.mode = 0o755
                tar.addfile(info, io.BytesIO(content))
        hashes[host] = hashlib.sha256(archive_path.read_bytes()).hexdigest()

    manifest = root/'manifest.json'
    manifest.write_text(json.dumps({'feature':'0040-FEAT','hosts':records}))
    acceptance = root/'prune-acceptance.json'
    acceptance.write_text(json.dumps({'feature':'0040-FEAT',
        'check':'first-unattended-receiver-simple-prune', 'date':'2026-11-08',
        'diagnostic_pass':True, 'formal_acceptance':'ACCEPTED'}))
    # The verified rollback archive must match both the manifest and original checksum.
    with patch.object(m, 'EVIDENCE', root):
        for host in ('mars','backup'):
            assert m.verify_saved_archive(host,records[host],stamp,hashes[host]).exists()
        try:
            m.verify_saved_archive('mars',records['mars'],stamp,'0'*64)
            raise AssertionError('Wrong rollback hash accepted')
        except RuntimeError as exc:
            assert 'checksum mismatch' in str(exc)

        # The post-removal audit must accept the expected systemd LoadState=not-found
        # without running list-unit-files (which exits 1 when the unit is absent).
        def ssh_unit(host, command, **kwargs):
            if 'systemctl show btrfs-native-push.service' in command:
                return 'ExecStart={ path=/usr/local/bin/btrfs-simplified-replication sender cycle ; }'
            if 'diaries-backup-status --json' in command:
                return json.dumps({'offsite':{'identity_verified':True,'relation':'equal',
                                'latest':{'snapshot':'20261108-030011Z'}},
                                   'replicationPreflight':{'ok':True}})
            if command.endswith('receiver status'):
                return json.dumps({'state':{'parent':{'timestamp':'20261108-030011Z'}}})
            if 'systemctl show btrfs-legacy-prune.timer -p LoadState' in command:
                return 'not-found\n'
            if 'systemctl is-active btrfs-receiver-simple-prune.timer' in command:
                return 'active\n'
            if 'test ! -e /etc/sudoers.d/diaries-native-btrfs' in command:
                return 'absent\n'
            raise AssertionError('Unexpected operation: '+command)
        with patch.object(m,'ssh',side_effect=ssh_unit):
            m.audit_deployment(legacy_units_removed=True)
        def ssh_unit_present(host, command, **kwargs):
            if 'systemctl show btrfs-legacy-prune.timer -p LoadState' in command:
                return 'loaded\n'
            return ssh_unit(host, command, **kwargs)
        with patch.object(m,'ssh',side_effect=ssh_unit_present):
            try:
                m.audit_deployment(legacy_units_removed=True)
                raise AssertionError('Loaded obsolete timer accepted')
            except RuntimeError as exc:
                assert 'still loaded' in str(exc)

        # The only host-side commands in this finalisation are inspections.
        def ssh_status(host, command, **kwargs):
            assert not any(part in command for part in (
                'daemon-reload', 'rm ', 'unlink', 'tar -xf', 'sender cycle', 'receiver receive'))
            if command.startswith('sudo -n python3 -c '):
                return json.dumps({'remaining':[]})
            if command.startswith('systemctl is-enabled '):
                return 'enabled\n'
            if command.startswith('systemctl is-active '):
                return 'active\n'
            raise AssertionError('Unexpected command: '+command)
        with patch.object(m, 'ssh', side_effect=ssh_status), \
             patch.object(m, 'audit_deployment') as deployed, \
             patch.object(m, 'audit_unretired_references') as refs:
            m.finalize(paths,manifest,acceptance,stamp,hashes,'FINALIZE-0040-RETIRED-CODE')
            deployed.assert_called_once_with(legacy_units_removed=True)
            assert refs.call_count == 2
        receipt = rollback/f'legacy-code-retirement-{stamp}.json'
        data = json.loads(receipt.read_text())
        assert data['status'] == 'VERIFIED_AFTER_RETIREMENT'
        assert data['removed_count'] == {'mars':2,'backup':2}
        assert data['archive_sha256'] == hashes
        try:
            m.finalize(paths,manifest,acceptance,stamp,hashes,'FINALIZE-0040-RETIRED-CODE')
            raise AssertionError('Receipt overwritten')
        except RuntimeError as exc:
            assert 'already exists' in str(exc)
        with patch.object(m, 'ssh', return_value=json.dumps({'remaining':[paths['mars'][0]]})):
            try:
                m.assert_removed('mars',records['mars'])
                raise AssertionError('Remaining retired path accepted')
            except RuntimeError as exc:
                assert 'still exist' in str(exc)
print('PASS: absent-unit audit, tamper-proof TAR validation, receipt-only finalisation and fail-closed guards')
