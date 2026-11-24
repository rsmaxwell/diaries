#!/usr/bin/env python3
"""0028 production writer-access outage: operator-executed on pluto via SSH stdin.

Actions: preflight, isolate, status, reopen. Never backs up, migrates, restores data,
changes MQTT, or creates journal tables. No credentials printed or read into this process.
Only supports the exact deployment contract verified 2026-11-24.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path('/home/richard/projects/diaries')
COMPOSE = ["docker", "compose", "--file", str(PROJECT / "compose.yaml"),
           "--env-file", str(PROJECT / ".env")]
DB = 'diaries-postgres'
RESP = 'diaries-responder'
TIMER = 'diaries-complete-backup-publish.timer'
BACKUP_SERVICE = 'diaries-complete-backup-publish.service'
MARK = '# 0028-MAINTENANCE-ISOLATION'
REJECT = (MARK + ' BEGIN\n'
          'host all all 0.0.0.0/0 reject\n'
          'host all all ::/0 reject\n'
          + MARK + ' END\n')
CATCHALL = re.compile(rb'(?m)^host[ \t]+all[ \t]+all[ \t]+all[ \t]+scram-sha-256[ \t]*(?:\#.*)?$')


class Stop(RuntimeError):
    pass


def call(args: list[str], *, data: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess:
    # Secrets in command environment/files never displayed; print only stderr on failure.
    p = subprocess.run(args, input=data, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=False)
    if check and p.returncode:
        details = p.stderr.decode(errors='replace').strip()
        raise Stop(f"Failed: {args[0]} {args[1] if len(args) > 1 else ''} (exit={p.returncode}): {details[:650]}")
    return p


def output(args: list[str]) -> str:
    return call(args).stdout.decode('utf-8').strip()


def unit_active(unit: str) -> str:
    return output(['systemctl', 'show', unit, '--property=ActiveState', '--value'])


def unit_enabled(unit: str) -> str:
    return output(['systemctl', 'show', unit, '--property=UnitFileState', '--value'])


def docker_running(name: str) -> bool:
    value = output(['docker', 'inspect', '--format', '{{.State.Running}}', name])
    if value not in ('true', 'false'):
        raise Stop(f'Unexpected Docker state for {name}: {value}')
    return value == 'true'


def db_sql(sql: str) -> str:
    # Executes only on the existing container-local Unix socket, not published TCP.
    return output(['docker', 'exec', DB, 'sh', '-c',
                   'exec psql -X -A -t -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"',
                   'sh', sql])


def hba_path() -> str:
    value = db_sql('show hba_file').strip()
    if not value.startswith('/var/lib/postgresql/') or not value.endswith('/pg_hba.conf') or '\n' in value:
        raise Stop('Unexpected PostgreSQL HBA path, refusing change')
    return value


def original_rules() -> None:
    text = db_sql("select type||'|'||coalesce(address,'-')||'|'||auth_method from pg_hba_file_rules where error is null order by line_number")
    parts = text.splitlines()
    expected = [
        'local|-|trust', 'host|127.0.0.1|trust', 'host|::1|trust',
        'local|-|trust', 'host|127.0.0.1|trust', 'host|::1|trust',
        'host|all|scram-sha-256',
    ]
    if parts != expected:
        raise Stop('PostgreSQL HBA rule order differs from accepted seven-rule contract')
    if db_sql('select count(*) from pg_hba_file_rules where error is not null') != '0':
        raise Stop('PostgreSQL HBA syntax errors found')


def isolated_rules() -> None:
    text = db_sql("select type||'|'||coalesce(address,'-')||'|'||auth_method from pg_hba_file_rules where error is null order by line_number")
    expected = [
        'local|-|trust', 'host|127.0.0.1|trust', 'host|::1|trust',
        'local|-|trust', 'host|127.0.0.1|trust', 'host|::1|trust',
        'host|0.0.0.0|reject', 'host|::|reject', 'host|all|scram-sha-256',
    ]
    if text.splitlines() != expected or db_sql('select count(*) from pg_hba_file_rules where error is not null') != '0':
        raise Stop('HBA isolation syntax/order not verified; do not continue')


def original_backup(hba: str) -> str:
    return hba + '.0028-original'


def exists_in_container(path: str) -> bool:
    p = call(['docker', 'exec', '-u', '0', DB, 'test', '-e', path], check=False)
    if p.returncode not in (0, 1):
        raise Stop('Could not test presence of original HBA backup')
    return p.returncode == 0


def hba_bytes(hba: str) -> bytes:
    return call(['docker', 'exec', '-u', '0', DB, 'cat', hba]).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_bytes(data: bytes) -> bytes:
    if MARK.encode() in data:
        raise Stop('HBA already contains 0028 maintenance marker')
    if len(CATCHALL.findall(data)) != 1:
        raise Stop('Expected one exact general SCRAM HBA rule; nothing changed')
    # Insert immediately before catch-all, leaving all original file bytes otherwise identical.
    insert = REJECT.encode('ascii')
    updated = CATCHALL.sub(lambda match: insert + match.group(0), data, count=1)
    if updated == data or updated.count(insert) != 1:
        raise Stop('Failed to construct isolated HBA')
    return updated


def put_hba(hba: str, data: bytes) -> None:
    tmp = hba + '.0028-incoming'
    if exists_in_container(tmp):
        raise Stop('Existing 0028 temporary HBA file: manual inspection required')
    # BusyBox/Alpine compatible: cp -p preserves mode/owner, atomic replace.
    script = ('set -e; target="$1"; temp="$2"; '
              'test ! -e "$temp"; cp -p "$target" "$temp"; '
              'cat > "$temp"; mv -f "$temp" "$target"')
    call(['docker', 'exec', '-i', '-u', '0', DB, 'sh', '-c', script, 'sh', hba, tmp], data=data)


def reload_hba() -> None:
    if db_sql('select pg_reload_conf()') != 't':
        raise Stop('PostgreSQL configuration reload failed')
    # For postmaster HBA reload asynchronous, require old/new parsed layout within 5s.
    import time
    for _ in range(20):
        if db_sql('select count(*) from pg_hba_file_rules where error is not null') == '0':
            return
        time.sleep(0.25)
    raise Stop('PostgreSQL HBA parse errors after reload')


def session_count() -> int:
    x = db_sql("select count(*) from pg_stat_activity where backend_type='client backend' and pid <> pg_backend_pid()")
    return int(x)


def confirm_denied_ipv4() -> None:
    cmd = ('set -eu; ip=$(hostname -i | awk \'{print $1}\'); '
           'case "$ip" in *:*) echo "Not a usable IPv4 address" >&2; exit 4;; esac; '
           'exec psql -X -w -h "$ip" -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select 1"')
    p = call(['docker', 'exec', DB, 'sh', '-c', cmd], check=False)
    diag = (p.stdout + p.stderr).decode('utf-8', errors='replace')
    if p.returncode == 0 or 'pg_hba.conf rejects connection' not in diag:
        raise Stop('Nonloopback IPv4 rejection NOT proven (refusing maintenance PASS)')


def preflight() -> None:
    if not (PROJECT / 'compose.yaml').is_file() or not (PROJECT / '.env').is_file():
        raise Stop('Expected deployed Compose or .env missing')
    if call(['sudo', '-n', 'true'], check=False).returncode:
        raise Stop('sudo -n not available; run in established interactive pluto SSH terminal with sudo capability')
    call(COMPOSE + ['config', '--quiet'])
    if unit_active('diaries-compose.service') != 'active':
        raise Stop('Diaries Compose supervisor not active')
    if unit_active(BACKUP_SERVICE) != 'inactive':
        raise Stop('Production backup publisher is active or unknown')
    if unit_active(TIMER) != 'active' or unit_enabled(TIMER) != 'enabled':
        raise Stop('Backup timer is not initially active+enabled; manual restoration design required')
    for name in (DB, 'diaries-mosquitto', RESP):
        if not docker_running(name):
            raise Stop(f'Expected {name} to be running at isolation entry')
    ports = json.loads(output(['docker', 'inspect', '-f', '{{json .NetworkSettings.Ports}}', DB]))
    bindings = ports.get('5432/tcp') or []
    if not all(any(row.get('HostIp') == host and row.get('HostPort') == '5433' for row in bindings)
               for host in ('0.0.0.0', '::')):
        raise Stop('PostgreSQL 5433 IPv4/IPv6 published bindings drifted')
    original_rules()
    hba = hba_path()
    if exists_in_container(original_backup(hba)):
        raise Stop('A prior 0028 HBA backup exists; inspect and reopen before new isolation')
    original = hba_bytes(hba)
    patch_bytes(original)
    print('PASS: live preflight; original timer enabled+active, backup inactive, responder running')
    print('HBA original SHA256:', sha(original))
    print('Observed active client sessions:', session_count())
    print('PRODUCTION APPLY NOT AUTHORISED')


def isolate() -> None:
    preflight()
    hba = hba_path()
    original = hba_bytes(hba)
    backup = original_backup(hba)
    print('=== BEGIN APPROVED WRITER ISOLATION (production changes follow) ===', flush=True)
    call(['docker', 'exec', '-u', '0', DB, 'cp', '-p', hba, backup])
    if hba_bytes(backup) != original:
        raise Stop('HBA rollback copy verification FAILED; do not continue')
    call(['sudo', '-n', 'systemctl', 'stop', TIMER])
    if unit_active(TIMER) != 'inactive' or unit_active(BACKUP_SERVICE) != 'inactive':
        raise Stop('Backup scheduler/service not quiescent')
    call(COMPOSE + ['stop', RESP])
    if docker_running(RESP):
        raise Stop('Responder stop did not complete')
    # Do not drop existing client sessions silently; a still-live client is a hard stop.
    # HBA admission closes direct ingress before final session verification.
    put_hba(hba, patch_bytes(original))
    reload_hba()
    isolated_rules()
    confirm_denied_ipv4()
    if session_count() != 0:
        raise Stop('Other database sessions remain; writer isolation NOT VERIFIED. Reopen or investigate while stopped.')
    if docker_running(RESP) or unit_active(TIMER) != 'inactive':
        raise Stop('Responder/timer reactivated unexpectedly')
    print('PASS: timer stopped, responder stopped, nonloopback TCP reject effective')
    print('PASS: no other PostgreSQL client sessions seen at final checkpoint')
    print('HBA rollback copy:', backup, '| SHA256:', sha(original))
    print('IPv6 reject rule parsed; runtime IPv6 external negative probe not yet demonstrated')
    print('Files-root external/NAS writers must be independently excluded before claiming full writer isolation')
    print('WINDOW: WRITER ISOLATION PARTIAL until Files/IPv6 checks; NO BACKUP OR DRY-RUN EXECUTED')
    print('PRODUCTION APPLY NOT AUTHORISED')


def status() -> None:
    print('Timer:', unit_active(TIMER), 'backup service:', unit_active(BACKUP_SERVICE))
    print('Responder running:', docker_running(RESP))
    print('DB running:', docker_running(DB), 'MQTT running:', docker_running('diaries-mosquitto'))
    hba = hba_path()
    print('HBA backup exists:', exists_in_container(original_backup(hba)))
    print('HBA 0028 markers:', MARK.encode() in hba_bytes(hba))
    print('Other client sessions:', session_count())
    print('NO PRODUCTION APPLY AUTHORISED')


def reopen() -> None:
    if call(['sudo', '-n', 'true'], check=False).returncode:
        raise Stop('sudo -n unavailable')
    if not docker_running(DB):
        raise Stop('DB not running; cannot safely restore HBA')
    hba = hba_path()
    backup = original_backup(hba)
    if exists_in_container(backup):
        original = hba_bytes(backup)
        if MARK.encode() in original or len(CATCHALL.findall(original)) != 1:
            raise Stop('Rollback HBA copy fails integrity contract')
        # Copy original bytes exactly and restore metadata from backup.
        call(['docker', 'exec', '-u', '0', DB, 'cp', '-p', backup, hba])
        reload_hba()
        original_rules()
        if hba_bytes(hba) != original:
            raise Stop('HBA original byte identity was not restored')
        print('PASS: restored original HBA bytes, SHA256:', sha(original))
    else:
        original_rules()
        print('PASS: original HBA already in use; no rollback copy exists')
    if not docker_running(RESP):
        call(COMPOSE + ['up', '-d', '--no-deps', RESP])
    if not docker_running(RESP):
        raise Stop('Responder did not start')
    if unit_active(TIMER) != 'active':
        call(['sudo', '-n', 'systemctl', 'start', TIMER])
    if unit_active(TIMER) != 'active' or unit_enabled(TIMER) != 'enabled':
        raise Stop('Original backup timer state not restored')
    print('PASS: responder running; original HBA and timer restored')
    print('CHECK REQUIRED: responder health, MQTT, Editor and Reader before closing maintenance')
    print('HBA rollback copy deliberately retained for recovery audit')
    print('NO MIGRATION APPLY RUN')


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('preflight', 'isolate', 'status', 'reopen'):
        raise Stop('Usage: python3 - {preflight|isolate|status|reopen} < 0028-pluto-maintenance-window.py')
    {'preflight': preflight, 'isolate': isolate, 'status': status, 'reopen': reopen}[sys.argv[1]]()


if __name__ == '__main__':
    try:
        main()
    except (Stop, ValueError, json.JSONDecodeError) as exc:
        print('FAIL:', exc, file=sys.stderr)
        print('IF ISOLATION STARTED: stop, inspect; use reopen to restore original HBA/responder/timer.', file=sys.stderr)
        sys.exit(2)
