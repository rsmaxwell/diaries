#!/usr/bin/env python3
"""0040: guarded, exact-file, post-acceptance removal of obsolete code.

Run from /home/richard/diaries on mango. Default --capture is read-only.
--apply requires a verified actual unattended prune receipt and explicit
operator approval; it makes local rollback tarballs before any remote unlink.
Never targets Btrfs datasets, snapshots, receipts, agreed-parent state or holds.
"""
import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile

FEATURE = Path('change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage')
CANDIDATES = FEATURE / 'tools/legacy-code-candidate-paths.json'
EVIDENCE = FEATURE / 'evidence/Step 12'

# Executed with sudo -n python3 -c on the two named endpoints, from SSH stdin.
# Validation and existence checks are repeated immediately before unlinking.
REMOTE_CODE = r'''
import hashlib, json, os, pathlib, stat, sys
req = json.load(sys.stdin)
assert os.uname().nodename.split('.')[0] == req['host'] in ('mars', 'backup')
assert os.geteuid() == 0
items = req['targets']
assert isinstance(items, list) and 1 <= len(items) <= 100
result = []
for item in items:
    path = item['path']
    assert path.startswith(('/usr/local/bin/', '/usr/local/libexec/', '/usr/local/sbin/')) or path in (
        '/etc/systemd/system/btrfs-legacy-prune.service',
        '/etc/systemd/system/btrfs-legacy-prune.timer')
    assert '..' not in pathlib.PurePosixPath(path).parts
    assert os.path.realpath(path) == path, 'symlink/redirected path: ' + path
    f = os.lstat(path)
    assert stat.S_ISREG(f.st_mode) and f.st_uid == 0 and f.st_gid == 0 and f.st_nlink == 1, path
    mode = stat.S_IMODE(f.st_mode)
    assert mode in (0o644, 0o755), path
    with open(path,'rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    actual = {'path':path, 'sha256':digest, 'mode':mode, 'bytes':f.st_size}
    if req['op'] == 'delete':
        assert actual == item, 'file changed since approved capture: ' + path
    result.append(actual)
if req['op'] == 'delete':
    # No recursive deletion. All identities are validated before the first unlink.
    for item in result:
        path = item['path']
        with open(path,'rb') as stream:
            assert hashlib.file_digest(stream,'sha256').hexdigest() == item['sha256'], path
        os.unlink(path)
    print(json.dumps({'host':req['host'],'removed':len(result),'paths':[v['path'] for v in result]}))
else:
    print(json.dumps({'host':req['host'],'targets':result}))
'''


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def run(argv, *, data=None, binary=False, timeout=120):
    cmd = subprocess.run(argv, input=data, capture_output=True, text=not binary,
                         timeout=timeout, check=False)
    require(cmd.returncode == 0, f'command failed rc={cmd.returncode}: {argv[:3]}: '
            + (cmd.stderr.decode(errors='replace') if binary else cmd.stderr)[-1000:])
    return cmd.stdout


def ssh(host, command, *, data=None, binary=False):
    return run(['ssh', '-T', '-o', 'BatchMode=yes', host, command], data=data, binary=binary, timeout=180)


def remote(host, op, items):
    payload = json.dumps({'host':host, 'op':op, 'targets':items})
    result = ssh(host, 'sudo -n python3 -c ' + shlex.quote(REMOTE_CODE), data=payload)
    return json.loads(result)


def allowed_paths():
    source = json.loads(CANDIDATES.read_text())
    require(source['feature'] == '0040-FEAT', 'wrong candidate file')
    require(set(source['hosts']) == {'mars','backup'}, 'wrong hosts')
    for host, paths in source['hosts'].items():
        require(len(paths) == len(set(paths)) and len(paths) >= 2, 'duplicated/empty candidate list')
        for path in paths:
            require(path.startswith(('/usr/local/bin/', '/usr/local/libexec/', '/usr/local/sbin/')) or
                    (host == 'backup' and path in
                     ('/etc/systemd/system/btrfs-legacy-prune.service',
                      '/etc/systemd/system/btrfs-legacy-prune.timer')),
                    'outside approved executable/unit paths')
            name = Path(path).name
            require(name in ('btrfs-legacy-prune.service', 'btrfs-legacy-prune.timer') or
                    name.startswith('btrfs-agreed-parent-') or
                    name in ('btrfs-native-push', 'btrfs-native-push-receiver',
                             'btrfs-native-endpoint', 'btrfs-receiver-prune'),
                    'non-legacy candidate: ' + path)
            require(not any(term in path for term in ('__pycache__', 'btrfs-simplified-replication',
                                                      'btrfs-snapshot-manager')),
                    'unsafe removal candidate')
    return source['hosts']


def capture(allowed):
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%SZ')
    targets = {}
    for host in ('mars','backup'):
        targets[host] = remote(host, 'inspect', [{'path':path} for path in allowed[host]])['targets']
        print(f'PASS: {host} observed {len(targets[host])} exact legacy files')
    payload = {'feature':'0040-FEAT', 'captured_utc':now,
               'note':'Reviewed SHA-256/owner/mode path manifest; no snapshots or state files',
               'hosts':targets}
    location = EVIDENCE / 'manifests' / f'legacy-code-retirement-manifest-{now}.json'
    location.parent.mkdir(parents=True, exist_ok=True)
    require(not location.exists(), 'manifest already exists')
    location.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(f'READ ONLY: manifest prepared {location}')


def audit_deployment(*, legacy_units_removed=False):
    source_unit = ssh('mars', 'systemctl show btrfs-native-push.service -p ExecStart --value')
    require('/usr/local/bin/btrfs-simplified-replication sender cycle' in source_unit,
            'source service does not use simplified sender')
    check = json.loads(ssh('mars', 'sudo -n /usr/local/sbin/diaries-backup-status --json'))
    require(check.get('offsite',{}).get('identity_verified') is True and
            check.get('replicationPreflight',{}).get('ok') is True and
            check['offsite'].get('relation') == 'equal',
            'new status command has not been deployed or validation fails')
    status = json.loads(ssh('backup', 'sudo -n /usr/local/bin/btrfs-simplified-replication receiver status'))
    require(status['state']['parent']['timestamp'] == check['offsite']['latest']['snapshot'],
            'receiver parent changed after status check')
    timer = ssh('backup', 'systemctl list-unit-files btrfs-legacy-prune.timer --no-legend --no-pager').strip()
    if legacy_units_removed:
        require(re.search(r'(?m)^btrfs-legacy-prune\.timer\s', timer) is None,
                'obsolete legacy prune timer remains installed')
    else:
        require('btrfs-legacy-prune.timer' in timer and 'disabled' in timer,
                'legacy prune timer must be installed but disabled before controlled retirement')
        legacy_state = ssh('backup', 'systemctl show btrfs-legacy-prune.timer -p ActiveState --value').strip()
        require(legacy_state == 'inactive', 'legacy prune timer must be inactive')
    active = ssh('backup', 'systemctl is-active btrfs-receiver-simple-prune.timer').strip()
    require(active == 'active', 'simplified receiver timer must be active')
    sudo_rule = ssh('mars', 'test ! -e /etc/sudoers.d/diaries-native-btrfs && echo absent').strip()
    require(sudo_rule == 'absent', 'legacy sender sudoers must be retired by Playbooks first')
    print('PASS: new status, agreed parent, scheduled sender/receiver and sudoers guards')


def audit_unretired_references(host, items):
    """Reject active configuration/scripts still calling an exact retired path.

    Targeted files themselves may call each other, so only scan remaining
    operational configs and scripts. The disabled legacy timer/service being
    retired in the SAME manifest is explicitly excluded on backup.
    """
    remote_script = r'''
import json, os, pathlib, stat, sys
req=json.load(sys.stdin)
assert os.uname().nodename.split('.')[0] == req['host']
files={p['path'] for p in req['targets']}
legacy={p for p in files if p.startswith('/usr/local/')}
roots=('/etc/systemd/system','/etc/cron.d','/etc/cron.daily',
       '/etc/cron.hourly','/etc/cron.weekly','/etc/cron.monthly',
       '/usr/local/bin','/usr/local/sbin','/usr/local/libexec','/root/scripts')
extra=('/home/richard/.ssh/authorized_keys','/root/.ssh/authorized_keys',
       '/etc/crontab','/etc/sudoers')
checks=set(extra)
for root in roots:
    if not os.path.isdir(root): continue
    for base, dirs, names in os.walk(root, followlinks=False):
        # Bytecode caches are generated artefacts, not runnable entrypoints.
        # They can contain obsolete string constants from files retired together.
        # Continue scanning actual scripts, systemd units and other configs.
        dirs[:]=[d for d in dirs if d != '__pycache__' and
                 not os.path.islink(os.path.join(base,d))]
        for name in names:
            checks.add(os.path.join(base,name))
errors=[]
for filename in sorted(checks):
    if filename in files: continue
    try:
        state=os.lstat(filename)
        if not stat.S_ISREG(state.st_mode) or state.st_size > 2_000_000: continue
        with open(filename,'rb') as inp: content=inp.read()
    except (OSError, PermissionError): continue
    for candidate in legacy:
        if candidate.encode() in content:
            errors.append({'file':filename,'reference':candidate})
print(json.dumps({'host':req['host'],'references':errors}))
'''
    reply = ssh(host, 'sudo -n python3 -c ' + shlex.quote(remote_script),
                data=json.dumps({'host':host,'targets':items}))
    refs = json.loads(reply)['references']
    require(not refs, f'{host} still has unretired references: {refs[:12]}')
    print(f'PASS: {host} no exact legacy executable references in operational files')


def archive(host, items, stamp):
    place = EVIDENCE / 'rollback' / f'legacy-code-{host}-{stamp}.tar'
    place.parent.mkdir(parents=True, exist_ok=True)
    require(not place.exists(), 'archive already exists: ' + str(place))
    paths = [v['path'].lstrip('/') for v in items]
    command = 'sudo -n tar -cf - -C / -- ' + shlex.join(paths)
    stream = ssh(host, command, binary=True)
    # Verify every member's bytes and identity before trusting the rollback.
    with tarfile.open(fileobj=io.BytesIO(stream), mode='r:') as archive_file:
        members = archive_file.getmembers()
        require({m.name for m in members} == set(paths) and len(members) == len(items),
                'tar archive contains unexpected/missing paths')
        for item in items:
            member = archive_file.getmember(item['path'].lstrip('/'))
            require(member.isfile() and member.uid == 0 and member.gid == 0 and
                    member.mode == item['mode'], 'unsafe rollback archive metadata')
            content = archive_file.extractfile(member).read()
            require(hashlib.sha256(content).hexdigest() == item['sha256'],
                    'rollback archive checksum differs: '+item['path'])
    with place.open('xb') as out:
        out.write(stream)
    place.chmod(0o600)
    print(f'PASS: {host} verified rollback archive {place} sha256={hashlib.sha256(stream).hexdigest()}')
    return place


def apply(allowed, manifest_path, receipt_path, approval):
    require(approval == 'RETIRE-0040-OBSOLETE-CODE', 'explicit operator acceptance absent')
    receipt = json.loads(Path(receipt_path).read_text())
    require(receipt.get('feature') == '0040-FEAT' and
            receipt.get('check') == 'first-unattended-receiver-simple-prune' and
            receipt.get('date') == '2026-11-08' and receipt.get('diagnostic_pass') is True and
            receipt.get('formal_acceptance') == 'ACCEPTED',
            'unattended receiver-prune evidence has not been formally accepted')
    data = json.loads(Path(manifest_path).read_text())
    require(data['feature'] == '0040-FEAT' and set(data['hosts']) == {'mars','backup'},
            'wrong manifest')
    for host in ('mars','backup'):
        items = data['hosts'][host]
        require({v['path'] for v in items} == set(allowed[host]),
                'manifest does not exactly match reviewed candidate paths')
        live = remote(host, 'inspect', [{'path':v['path']} for v in items])['targets']
        require(live == items, f'{host} installed files differ from approved manifest')
    audit_deployment()
    for host in ('mars','backup'):
        audit_unretired_references(host, data['hosts'][host])
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%SZ')
    backups = {host: archive(host, data['hosts'][host], stamp) for host in ('mars','backup')}
    require(all(archive_file.exists() for archive_file in backups.values()),
            'rollback evidence not established')
    for host in ('mars','backup'):
        result = remote(host,'delete',data['hosts'][host])
        require(result.get('removed') == len(data['hosts'][host]), 'incomplete removal')
        print(f'PASS: {host} retired {result["removed"]} checksum-validated files')
    ssh('backup', 'sudo -n systemctl daemon-reload')
    audit_deployment(legacy_units_removed=True)
    receipt_out = EVIDENCE / 'rollback' / f'legacy-code-retirement-{stamp}.json'
    receipt_out.write_text(json.dumps({'feature':'0040-FEAT','completed_utc':stamp,
       'source_manifest':str(manifest_path),'acceptance_report':str(receipt_path),
       'archives':{h:str(v) for h,v in backups.items()},
       'removed_count':{h:len(data['hosts'][h]) for h in backups}},indent=2)+'\n')
    print(f'PASS: post-removal audit; receipt {receipt_out}')


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--capture', action='store_true', help='read-only capture of approved path/sha manifest')
    args.add_argument('--apply', action='store_true', help='destructive mode, requires acceptance and explicit approval')
    args.add_argument('--manifest')
    args.add_argument('--prune-acceptance')
    args.add_argument('--confirm')
    opts = args.parse_args()
    require(Path.cwd().resolve().name == 'diaries' and
            run(['hostname','-s']).strip() == 'mango', 'run from /home/richard/diaries on mango')
    allowed = allowed_paths()
    require(opts.capture != opts.apply, 'choose exactly one of --capture or --apply')
    if opts.capture:
        require(not any((opts.manifest,opts.prune_acceptance,opts.confirm)),
                '--capture does not use destructive options')
        capture(allowed)
    else:
        require(all((opts.manifest,opts.prune_acceptance,opts.confirm)),
                'apply requires manifest, prune acceptance and exact confirmation')
        apply(allowed,opts.manifest,opts.prune_acceptance,opts.confirm)

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError,ValueError,KeyError,OSError,subprocess.TimeoutExpired) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(2)
