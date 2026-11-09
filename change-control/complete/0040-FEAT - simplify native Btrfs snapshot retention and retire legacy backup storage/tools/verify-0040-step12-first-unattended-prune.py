#!/usr/bin/env python3
"""0040 Step 12: read-only acceptance capture for first unattended prune.

Execute on mango from /home/richard/diaries. Never invokes receiver-simple-prune,
changes timer state, deletes snapshots, or touches agreed-parent records.
A machine PASS is a diagnostic, not formal feature-closure approval.
"""
import datetime as dt
import json
from pathlib import Path
import re
import subprocess
import sys

FEATURE = Path('change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage')
EVIDENCE = FEATURE / 'evidence/Step 12/raw-logs'
DAY = '2026-11-08'


def ssh(host, command, *, timeout=180):
    run = subprocess.run(['ssh', '-o', 'BatchMode=yes', host, command],
                         capture_output=True, text=True, timeout=timeout, check=False)
    return {'exit': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def main():
    require(Path.cwd().resolve().name == 'diaries', 'run from /home/richard/diaries on mango')
    require(subprocess.run(['hostname', '-s'], capture_output=True, text=True).stdout.strip() == 'mango',
            'capture must run on mango')
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%SZ')
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    commands = {
        'backup_service': ('backup',
            'systemctl show btrfs-receiver-simple-prune.service '
            '-p Result -p ExecMainStatus -p ExecMainStartTimestamp -p ExecMainExitTimestamp --no-pager'),
        'backup_timer': ('backup',
            'systemctl show btrfs-receiver-simple-prune.timer -p ActiveState -p UnitFileState -p LastTriggerUSec --no-pager'),
        'backup_journal': ('backup',
            'sudo -n journalctl -u btrfs-receiver-simple-prune.service '
            '--since "2026-11-08 04:00:00 UTC" --until "2026-11-09 00:00:00 UTC" '
            '--utc --no-pager -o short-iso'),
        'backup_plan': ('backup',
            'sudo -n /usr/local/sbin/btrfs-snapshot-manager '
            '--config /etc/btrfs-snapshot-manager.json receiver-simple-plan'),
        'backup_parent': ('backup',
            'sudo -n /usr/local/bin/btrfs-simplified-replication receiver status'),
        'mars_parent': ('mars',
            'sudo -n cat /media/usb/@snapshots/.simple-agreed-parent.json'),
        'backup_legacy_unit': ('backup',
            'systemctl cat btrfs-legacy-prune.service btrfs-legacy-prune.timer'),
        'mars_source_timer': ('mars', 'systemctl show btrfs-native-push.timer -p ActiveState -p UnitFileState --no-pager'),
    }
    captured = {name: ssh(host, command) for name, (host, command) in commands.items()}
    raw = EVIDENCE / f'step12-first-unattended-prune-{stamp}.txt'
    with raw.open('w', encoding='utf-8') as out:
        for name, (host, command) in commands.items():
            item = captured[name]
            out.write(f'=== {name} on {host}: {command} [exit={item["exit"]}] ===\n')
            out.write(item['stdout'] + '\n' + item['stderr'] + '\n')

    errors = []
    for name in ('backup_service', 'backup_timer', 'backup_journal',
                 'backup_plan', 'backup_parent', 'mars_parent', 'mars_source_timer'):
        if captured[name]['exit'] != 0:
            errors.append(f'{name} returned {captured[name]["exit"]}')
    service = dict(re.findall(r'^([A-Za-z]+)=(.*)$', captured['backup_service']['stdout'], re.M))
    timer = dict(re.findall(r'^([A-Za-z]+)=(.*)$', captured['backup_timer']['stdout'], re.M))
    if timer.get('ActiveState') != 'active' or timer.get('UnitFileState') != 'enabled':
        errors.append('receiver prune timer is not active and enabled')
    source_timer = dict(re.findall(r'^([A-Za-z]+)=(.*)$', captured['mars_source_timer']['stdout'], re.M))
    if source_timer.get('ActiveState') != 'active' or source_timer.get('UnitFileState') != 'enabled':
        errors.append('source sender timer is not active and enabled')
    if service.get('Result') != 'success' or service.get('ExecMainStatus') != '0':
        errors.append('receiver prune service did not report success/exit 0')
    # This checks the time of the *last run*, not merely whether the timer is enabled.
    last_start = service.get('ExecMainStartTimestamp', '')
    if not re.search(r'\b2026-11-08\b|\bSun 2026-11-08\b', last_start):
        errors.append(f'last service start is not {DAY}: {last_start!r}')
    journal = captured['backup_journal']['stdout']
    matches = re.findall(r'RECEIVER-SIMPLE-DELETED count=(\d+)\b', journal)
    if len(matches) != 1:
        errors.append(f'expected exactly one unattended completion receipt on {DAY}, found {len(matches)}')
    elif int(matches[0]) > 10:
        errors.append(f'prune exceeded 10-delete limit: {matches[0]}')
    if 'RECEIVER-SIMPLE-PLAN ' not in captured['backup_plan']['stdout']:
        errors.append('receiver retention plan not present')
    try:
        local_state = json.loads(captured['mars_parent']['stdout'])
        remote_status = json.loads(captured['backup_parent']['stdout'])
        remote_state = remote_status['state']
        if local_state != remote_state:
            errors.append('sender and receiver agreed-parent records differ')
        for name in ('parent', 'prior'):
            if remote_state.get(name) != local_state.get(name):
                errors.append(f'{name} mismatch')
    except (ValueError, KeyError, TypeError) as exc:
        errors.append('unable to parse agreed-parent records: ' + str(exc))

    result = {'feature': '0040-FEAT', 'check': 'first-unattended-receiver-simple-prune',
              'date': DAY, 'captured_utc': stamp, 'diagnostic_pass': not errors,
              'deleted_count': int(matches[0]) if len(matches) == 1 else None,
              'errors': errors, 'raw_log': str(raw),
              'formal_acceptance': 'PENDING_OPERATOR_REVIEW'}
    summary = EVIDENCE / f'step12-first-unattended-prune-{stamp}.json'
    summary.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(2)
