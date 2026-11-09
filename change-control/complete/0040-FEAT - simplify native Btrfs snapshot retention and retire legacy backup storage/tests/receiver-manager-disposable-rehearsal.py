#!/usr/bin/env python3
"""0040 Step 3 — disposable-only manager transaction rehearsal.

Runs from Windows Cygwin: retrieves manager source from mango and streams both
scripts to mars; neither host's installed snapshot manager is replaced.

IMPORTANT: the source protection callback is a LOCAL, DISPOSABLE stand-in,
NOT a trusted remote source-held lease. Never use to authorize real pruning.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import types

BASE = Path('/media/usb/@data/0040-step03-manager-rehearsal')
CONFIG = BASE / 'manager.json'
RECEIVED = BASE / 'received'
SOURCE = BASE / 'source'
STATE = BASE / 'state'
PARENT = '20261023-000003Z'
CANDIDATE = '20261023-000001Z'
INTERRUPT_CANDIDATE = '20261023-000002Z'
INTERRUPT_UUID = 'a4131935-d2e6-6241-89df-fa398d3c630d'
PARENT_UUID = 'db5eeff7-bdfe-9a4d-94af-13eedca6869f'
MANAGER = '/home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py'


def ensure_rehearsal_only(*, allow_pending=False):
    if os.geteuid() != 0:
        raise RuntimeError('root required on mars')
    if BASE.resolve(strict=True) != BASE:
        raise RuntimeError('rehearsal root mismatch')
    if BASE.stat().st_uid != 0 or BASE.stat().st_mode & 0o077:
        raise RuntimeError('rehearsal root not private/root-owned')
    for path in (CONFIG, SOURCE, RECEIVED, STATE, SOURCE / PARENT,
                 RECEIVED / PARENT):
        if path.is_symlink() or not path.exists() or path.resolve(strict=True) != path:
            raise RuntimeError(f'unsafe rehearsal path: {path}')
    for path in (SOURCE, RECEIVED, STATE):
        if path.stat().st_uid != 0 or path.stat().st_mode & 0o077:
            raise RuntimeError(f'unsafe rehearsal directory: {path}')
    if CONFIG.is_symlink() or CONFIG.stat().st_uid != 0:
        raise RuntimeError('unsafe rehearsal config')
    contents = json.loads(CONFIG.read_text())
    if (contents.get('mode') != 'receiver' or
            contents.get('receiver_prune_enabled') is not False or
            contents.get('snapshot_root') != str(BASE) or
            contents.get('receiver_state_dir') != str(STATE) or
            contents.get('writer_lock_path') != str(STATE / 'writer.lock') or
            contents.get('lock_path') != str(STATE / 'manager.lock') or
            contents.get('sources') != [{'name': '@data', 'snapshot_directory': str(RECEIVED)}] or
            contents.get('checkpoint_holds', {}).get('required') is not True or
            contents.get('checkpoint_holds', {}).get('path') != str(BASE / 'checkpoint-holds.json')):
        raise RuntimeError('rehearsal config does not match pinned test paths')
    pending = STATE / '.receiver-prune-pending.json'
    if pending.is_symlink() or (pending.exists() and not allow_pending):
        raise RuntimeError('pending journal; use inspect or reset-before, not another deletion')


def uuid_of(path, field):
    output = subprocess.run(['btrfs', 'subvolume', 'show', str(path)],
                            check=True, capture_output=True, text=True).stdout
    found = re.findall(r'^\s*' + re.escape(field) + r':\s*(\S+)\s*$',
                       output, re.MULTILINE)
    if len(found) != 1:
        raise RuntimeError(f'cannot read {field}: {path}')
    return found[0]


def read_only(path):
    output = subprocess.run(['btrfs', 'property', 'get', '-ts', str(path), 'ro'],
                            check=True, capture_output=True, text=True).stdout.strip()
    if output != 'ro=true':
        raise RuntimeError(f'not read only: {path}')


def verify_disposable_source():
    # An observable local stand-in only; NOT protection against remote pruning.
    if uuid_of(SOURCE / PARENT, 'UUID') != PARENT_UUID:
        raise RuntimeError('disposable source parent UUID mismatch')
    if uuid_of(RECEIVED / PARENT, 'Received UUID') != PARENT_UUID:
        raise RuntimeError('disposable received parent UUID mismatch')
    read_only(SOURCE / PARENT)
    read_only(RECEIVED / PARENT)


def execute_remote(scenario):
    ensure_rehearsal_only(allow_pending=scenario in ('inspect', 'reset-before', 'reconcile-after'))
    raw = base64.b64decode(MANAGER_SOURCE_B64)
    module = types.ModuleType('disposable_btrfs_manager')
    module.__file__ = 'mango:roles/snapshots/files/btrfs-snapshot-manager.py'
    sys.modules[module.__name__] = module
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    config = module.load_config(CONFIG)
    verify_disposable_source()
    print('PHASE: acquired rehearsal source identities', flush=True)
    # These are the very same locks used by the manager CLI, in its lock order.
    manager_lock = module.with_lock(config.lock_path, require_existing=True)
    try:
        writer_lock = module.with_lock(config.writer_lock_path, require_existing=True)
        try:
            print('PHASE: manager and receiver writer locks acquired', flush=True)
            if scenario == 'verify-final':
                print('PHASE: verifying completed transaction', flush=True)
                for stamp in (CANDIDATE, INTERRUPT_CANDIDATE):
                    path = RECEIVED / stamp
                    receipt = STATE / (stamp + '.json')
                    if path.exists() or path.is_symlink() or receipt.exists() or receipt.is_symlink():
                        raise RuntimeError(f'completed disposable candidate still exists: {stamp}')
                pending = STATE / '.receiver-prune-pending.json'
                if pending.exists() or pending.is_symlink():
                    raise RuntimeError('pending journal still exists')
                recovery = module.receiver_recovery_plan(config)
                if recovery != {'state': 'CLEAN', 'authorizes_repair': False}:
                    raise RuntimeError('final recovery classification not CLEAN')
                entries = module.receiver_inventory(config)
                if len(entries) != 1 or entries[0][0] != PARENT:
                    raise RuntimeError('final inventory not protected-parent only')
                from datetime import datetime, timezone
                held = module.receiver_verified_checkpoint_holds(config, entries)
                if held != {PARENT}:
                    raise RuntimeError('parent not independently held')
                verify_disposable_source()
                print('PASS: verify-final clean; one held protected parent; no pending journal or candidate receipts', flush=True)
            elif scenario == 'check':
                plan = module.receiver_plan(config)
                if CANDIDATE not in plan['candidates'] or PARENT not in plan['keep']:
                    raise RuntimeError('candidate/parent not as expected')
                recovery = module.receiver_recovery_plan(config)
                if recovery['state'] != 'CLEAN':
                    raise RuntimeError('recovery not CLEAN')
                print('PASS: disposable manager locks, eligibility and recovery preflight')
            elif scenario == 'success':
                plan = module.receiver_plan(config)
                if CANDIDATE not in plan['candidates'] or PARENT not in plan['keep']:
                    raise RuntimeError('candidate/parent mismatch')
                print('DISPOSABLE-DELETE BEGIN ' + CANDIDATE, flush=True)
                def delete_exact(path):
                    expected = RECEIVED / CANDIDATE
                    if path != expected or path.is_symlink() or path.resolve(strict=True) != expected:
                        raise RuntimeError('refusing Btrfs deletion outside exact disposable candidate')
                    verify_disposable_source()
                    read_only(path)
                    subprocess.run(['btrfs', 'subvolume', 'delete', str(path)], check=True)
                module.receiver_delete_one_locked(
                    config, CANDIDATE, protected_stamp=PARENT,
                    expected_parent_uuid=PARENT_UUID,
                    verify_source_pin=verify_disposable_source,
                    delete_subvolume=delete_exact)
                if (RECEIVED / CANDIDATE).exists() or (STATE / (CANDIDATE + '.json')).exists():
                    raise RuntimeError('candidate/receipt still present')
                if module.receiver_recovery_plan(config)['state'] != 'CLEAN':
                    raise RuntimeError('journal not clean')
                verify_disposable_source()
                print('PASS: actual manager journalled deletion; receipt reconciled; parent preserved')
            elif scenario == 'inspect':
                recovery = module.receiver_recovery_plan(config)
                if recovery['state'] not in ('BEFORE_DELETE', 'AFTER_DELETE_RECEIPT_PRESENT',
                                             'AFTER_RECEIPT_REMOVAL', 'INCONSISTENT'):
                    raise RuntimeError('no interrupted transaction to inspect')
                if recovery.get('snapshot') != INTERRUPT_CANDIDATE or recovery.get('authorizes_repair') is not False:
                    raise RuntimeError('unexpected recovery classification')
                verify_disposable_source()
                print('PASS: read-only interrupted transaction classification ' + recovery['state'])
            elif scenario == 'interrupt-before':
                plan = module.receiver_plan(config)
                if INTERRUPT_CANDIDATE not in plan['candidates'] or PARENT not in plan['keep']:
                    raise RuntimeError('interruption candidate/parent mismatch')
                def refuse_before_delete(path):
                    if path != RECEIVED / INTERRUPT_CANDIDATE:
                        raise RuntimeError('unexpected deletion target')
                    raise RuntimeError('EXPECTED_INJECTION_BEFORE_DELETE')
                try:
                    module.receiver_delete_one_locked(
                        config, INTERRUPT_CANDIDATE, protected_stamp=PARENT,
                        expected_parent_uuid=PARENT_UUID,
                        verify_source_pin=verify_disposable_source,
                        delete_subvolume=refuse_before_delete)
                except RuntimeError as exc:
                    if str(exc) != 'EXPECTED_INJECTION_BEFORE_DELETE':
                        raise
                else:
                    raise RuntimeError('injection failed')
                phase = module.receiver_recovery_plan(config)
                if phase['state'] != 'BEFORE_DELETE' or phase.get('authorizes_repair') is not False:
                    raise RuntimeError('BEFORE_DELETE not classified')
                verify_disposable_source()
                print('PASS: actual manager left durable BEFORE_DELETE journal; no deletion')
            elif scenario == 'reset-before':
                # Separate, operator-invoked disposal of the rehearsal's before-delete
                # journal only. Never repair a state following Btrfs deletion.
                recovery = module.receiver_recovery_plan(config)
                if recovery['state'] != 'BEFORE_DELETE' or recovery.get('snapshot') != INTERRUPT_CANDIDATE:
                    raise RuntimeError('reset allowed only for exact BEFORE_DELETE rehearsal')
                pending = STATE / '.receiver-prune-pending.json'
                record = json.loads(pending.read_text())
                expected = {'schema': 1, 'snapshot': INTERRUPT_CANDIDATE,
                            'destination': str(RECEIVED / INTERRUPT_CANDIDATE),
                            'receipt': str(STATE / (INTERRUPT_CANDIDATE + '.json')),
                            'source_uuid': INTERRUPT_UUID, 'protected_parent': PARENT,
                            'protected_parent_uuid': PARENT_UUID}
                if record != expected:
                    raise RuntimeError('journal identity differs from disposable expected record')
                if uuid_of(RECEIVED / INTERRUPT_CANDIDATE, 'Received UUID') != INTERRUPT_UUID:
                    raise RuntimeError('disposable candidate identity mismatch')
                read_only(RECEIVED / INTERRUPT_CANDIDATE)
                if not (STATE / (INTERRUPT_CANDIDATE + '.json')).is_file():
                    raise RuntimeError('candidate receipt missing')
                verify_disposable_source()
                # Explicitly cancel only this injection with no deletion, then fsync.
                directory_fd = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                try:
                    os.unlink(pending.name, dir_fd=directory_fd)
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
                if module.receiver_recovery_plan(config)['state'] != 'CLEAN':
                    raise RuntimeError('journal reset not clean')
                print('PASS: operator-directed disposable BEFORE_DELETE journal cancelled; candidate retained')
            elif scenario == 'interrupt-after':
                plan = module.receiver_plan(config)
                if INTERRUPT_CANDIDATE not in plan['candidates'] or PARENT not in plan['keep']:
                    raise RuntimeError('interruption candidate/parent mismatch')
                def delete_then_inject(path):
                    expected = RECEIVED / INTERRUPT_CANDIDATE
                    if path != expected or path.is_symlink() or path.resolve(strict=True) != expected:
                        raise RuntimeError('refusing deletion outside exact disposable candidate')
                    if uuid_of(path, 'Received UUID') != INTERRUPT_UUID:
                        raise RuntimeError('disposable target UUID mismatch')
                    verify_disposable_source()
                    read_only(path)
                    subprocess.run(['btrfs', 'subvolume', 'delete', str(path)], check=True)
                    raise RuntimeError('EXPECTED_INJECTION_AFTER_DELETE')
                try:
                    module.receiver_delete_one_locked(
                        config, INTERRUPT_CANDIDATE, protected_stamp=PARENT,
                        expected_parent_uuid=PARENT_UUID,
                        verify_source_pin=verify_disposable_source,
                        delete_subvolume=delete_then_inject)
                except RuntimeError as exc:
                    if str(exc) != 'EXPECTED_INJECTION_AFTER_DELETE':
                        raise
                else:
                    raise RuntimeError('injection failed')
                recovery = module.receiver_recovery_plan(config)
                if recovery['state'] != 'AFTER_DELETE_RECEIPT_PRESENT' or recovery.get('authorizes_repair') is not False:
                    raise RuntimeError('after-delete state not classified as expected')
                verify_disposable_source()
                print('PASS: genuine Btrfs deletion; receipt and pending journal preserved for manual recovery')
            elif scenario == 'reconcile-after':
                # Operator-directed reconciliation of one exact disposable
                # interrupted transaction. Not an authorization to prune.
                recovery = module.receiver_recovery_plan(config)
                if (recovery != {'state': 'AFTER_DELETE_RECEIPT_PRESENT',
                                 'snapshot': INTERRUPT_CANDIDATE,
                                 'authorizes_repair': False}):
                    raise RuntimeError('not the expected AFTER_DELETE_RECEIPT_PRESENT state')
                pending = STATE / '.receiver-prune-pending.json'
                receipt = STATE / (INTERRUPT_CANDIDATE + '.json')
                target = RECEIVED / INTERRUPT_CANDIDATE
                record = json.loads(pending.read_text(encoding='utf-8'))
                expected = {'schema': 1, 'snapshot': INTERRUPT_CANDIDATE,
                            'destination': str(target), 'receipt': str(receipt),
                            'source_uuid': INTERRUPT_UUID,
                            'protected_parent': PARENT,
                            'protected_parent_uuid': PARENT_UUID}
                if record != expected:
                    raise RuntimeError('pending journal not exact disposable transaction')
                if (pending.is_symlink() or receipt.is_symlink() or
                        not pending.is_file() or not receipt.is_file()):
                    raise RuntimeError('journal/receipt missing or unsafe')
                for item in (pending, receipt):
                    metadata = item.stat()
                    if metadata.st_uid != 0 or metadata.st_mode & 0o077:
                        raise RuntimeError(f'unsafe journal/receipt ownership or mode: {item}')
                saved = json.loads(receipt.read_text(encoding='utf-8'))
                expected_receipt = {'schema': 1, 'snapshot': INTERRUPT_CANDIDATE,
                                    'destination': str(target),
                                    'source_uuid': INTERRUPT_UUID,
                                    'received_uuid': INTERRUPT_UUID,
                                    'read_only_verified': True}
                if saved != expected_receipt:
                    raise RuntimeError('candidate receipt differs from expected disposable identity')
                if target.exists() or target.is_symlink():
                    raise RuntimeError('candidate still exists; refusing reconciliation')
                # Confirm no Btrfs subvolume by this path and match parent on
                # both source and receiver, including its independently held receipt.
                verify_disposable_source()
                parent_receipt = STATE / (PARENT + '.json')
                if parent_receipt.is_symlink() or not parent_receipt.is_file():
                    raise RuntimeError('protected-parent receipt missing')
                parent_data = json.loads(parent_receipt.read_text(encoding='utf-8'))
                if (parent_data.get('source_uuid') != PARENT_UUID or
                        parent_data.get('received_uuid') != PARENT_UUID or
                        parent_data.get('destination') != str(RECEIVED / PARENT) or
                        parent_data.get('read_only_verified') is not True):
                    raise RuntimeError('protected-parent receipt mismatch')
                # A full receiver inventory MUST fail during this interrupted
                # transaction: the deleted candidate still has a receipt and
                # the journal is pending. Validate the actual surviving parent
                # via Btrfs+receipt checks above, then apply the manager's own
                # strict checkpoint-hold validation to that verified parent.
                # The complete inventory is checked after reconciliation.
                from datetime import datetime, timezone
                verified_parent = (PARENT, datetime.now(timezone.utc), RECEIVED / PARENT)
                held = module.receiver_verified_checkpoint_holds(config, [verified_parent])
                if held != {PARENT}:
                    raise RuntimeError('protected parent not independently held')
                print('PHASE: journal, receipt, parent and hold verified', flush=True)
                # Remove and sync receipt before invoking the EXISTING journal
                # completion primitive. An unexpected failure leaves the journal.
                directory_fd = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                try:
                    os.unlink(receipt.name, dir_fd=directory_fd)
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
                print('PHASE: candidate receipt unlinked and directory synced', flush=True)
                module.receiver_journal_finish(STATE, snapshot=INTERRUPT_CANDIDATE)
                print('PHASE: pending journal finished', flush=True)
                clean = module.receiver_recovery_plan(config)
                if clean != {'state': 'CLEAN', 'authorizes_repair': False}:
                    raise RuntimeError('post-reconciliation journal not clean')
                if receipt.exists() or pending.exists() or target.exists():
                    raise RuntimeError('unexpected reconciliation residue')
                entries = module.receiver_inventory(config)
                if len(entries) != 1 or entries[0][0] != PARENT:
                    raise RuntimeError('final verified receiver inventory is not parent-only')
                verify_disposable_source()
                print('PASS: operator-directed AFTER_DELETE reconciliation; journal and receipt cleared; parent preserved')
            else:
                raise RuntimeError('unknown scenario')
        finally:
            writer_lock.close()
    finally:
        manager_lock.close()


def run_bounded(argv, *, input_bytes=None, timeout_seconds=90, display_stdout=True):
    """Bound local SSH and its process group; no remote deletion on deadline.

    Source retrieval may suppress successful stdout while retaining it as bytes.

    Timeout causes a FAILED command, never permission to retry a mutation.
    """
    child = subprocess.Popen(argv, stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        stdout, stderr = child.communicate(input=input_bytes, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        # SSH may have reached the remote operation already. Never claim the
        # remote state was rolled back; inspect remotely before any retry.
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate()
        if stdout:
            print(stdout.decode('utf-8', 'replace'), end='', flush=True)
        if stderr:
            print(stderr.decode('utf-8', 'replace'), end='', file=sys.stderr, flush=True)
        raise RuntimeError(f'SSH deadline ({timeout_seconds}s); remote state UNKNOWN; inspect, do not retry mutation') from exc
    if stdout and (display_stdout or child.returncode != 0):
        print(stdout.decode('utf-8', 'replace'), end='', flush=True)
    if stderr:
        print(stderr.decode('utf-8', 'replace'), end='', file=sys.stderr, flush=True)
    if child.returncode != 0:
        raise RuntimeError(f'SSH exited {child.returncode}; remote state must be inspected before retry')
    return stdout


def run_from_cygwin(scenario):
    print('PHASE: retrieving manager source from mango', flush=True)
    source = run_bounded(['ssh', 'mango', 'cat', MANAGER],
                         timeout_seconds=45, display_stdout=False)
    if b'def receiver_delete_one_locked(' not in source or b'def receiver_recovery_plan(' not in source:
        raise RuntimeError('mango source lacks transaction/recovery functions')
    # Embed manager source in an in-memory execution script, never remote /tmp.
    this = Path(__file__).read_bytes()
    header = ('MANAGER_SOURCE_B64 = ' + repr(base64.b64encode(source).decode('ascii')) + '\n').encode()
    payload = header + this
    print(f'PHASE: running {scenario} on mars (bounded SSH)', flush=True)
    run_bounded(['ssh', 'mars', 'sudo', 'python3', '-u', '/dev/stdin',
                 '--remote', scenario], input_bytes=payload,
                timeout_seconds=90 if scenario in ('verify-final', 'check', 'inspect') else 180)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('scenario', choices=['check', 'success', 'interrupt-before', 'inspect', 'reset-before', 'interrupt-after', 'reconcile-after', 'verify-final'])
    parser.add_argument('--remote', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.remote:
        execute_remote(args.scenario)
    else:
        run_from_cygwin(args.scenario)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        sys.exit(1)
