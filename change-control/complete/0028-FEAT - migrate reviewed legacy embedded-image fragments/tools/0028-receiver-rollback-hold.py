#!/usr/bin/env python3
"""One-off receiver recovery hold, using the installed snapshot-manager primitives.

Run ON backup, as root: python3 - {verify|hold} YYYYMMDD-HHMMSSZ < this-script
Does not prune, delete, replace snapshots, or modify Playbooks roles.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import re
import sys

STAMP = re.compile(r'[0-9]{8}-[0-9]{6}Z\Z')
MANAGER = Path('/usr/local/sbin/btrfs-snapshot-manager')
CONFIG = Path('/etc/btrfs-snapshot-manager.json')
EXPECTED_HOLDS = Path('/etc/btrfs-receiver-checkpoint-holds.json')
EXPECTED_ROOT = Path('/@data/mars-received')
EXPECTED_SNAPSHOTS = EXPECTED_ROOT / '@data'
EXPECTED_STATE = EXPECTED_ROOT / '.replication-state'


def fail(message: str) -> None:
    raise RuntimeError(message)


def runtime():
    if os.geteuid() != 0 or not MANAGER.is_file():
        fail('Expected root and installed receiver snapshot manager')
    loader = importlib.machinery.SourceFileLoader('receiver_snapshot_manager_0028', str(MANAGER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        fail('Cannot load installed snapshot manager')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    loader.exec_module(module)
    config = module.load_config(CONFIG)
    if (config.mode != 'receiver' or config.snapshot_root != EXPECTED_ROOT or
            config.receiver_state_dir != EXPECTED_STATE or
            config.checkpoint_holds_file != EXPECTED_HOLDS or
            not config.checkpoint_holds_required or len(config.sources) != 1 or
            config.sources[0].name != '@data' or
            module.source_directory(config, config.sources[0]) != EXPECTED_SNAPSHOTS or
            config.writer_lock_path != EXPECTED_STATE / 'writer.lock'):
        fail('Receiver configuration differs from reviewed contract')
    return module, config


def operate(action: str, stamp: str) -> None:
    if action not in ('verify', 'hold') or not STAMP.fullmatch(stamp):
        fail('Usage: python3 - {verify|hold} YYYYMMDD-HHMMSSZ')
    module, config = runtime()
    # Both manager and replication writer lock: same order as native replication.
    manager_lock = module.with_lock(config.lock_path, require_existing=True)
    try:
        writer_lock = module.with_lock(config.writer_lock_path, require_existing=True)
        try:
            module.receiver_simple_validate(config)
            target = EXPECTED_SNAPSHOTS / stamp
            identity = module.receiver_simple_identity(target)
            received = identity['Received UUID']
            holds = module.read_checkpoint_holds(config)
            expected = {'reason': '0028-FEAT migration production rollback checkpoint',
                        'source_uuids': {'@data': received}}
            if stamp in holds:
                actual = holds[stamp]
                if actual['source_uuids'] != expected['source_uuids']:
                    fail('Existing hold identity differs from immutable received snapshot')
                print('PASS: receiver rollback hold already exists:', stamp)
            elif action == 'verify':
                fail('Required receiver rollback hold is absent (no change made)')
            else:
                # Fail closed if any historic receive state or hold is invalid.
                module.receiver_simple_plan(config)
                updated = dict(holds)
                updated[stamp] = expected
                module.write_checkpoint_holds(config, updated)
                print('PASS: receiver rollback hold created:', stamp)
            again = module.read_checkpoint_holds(config)
            if again.get(stamp, {}).get('source_uuids', {}).get('@data') != received:
                fail('Receiver hold read-back identity mismatch')
            plan = module.receiver_simple_plan(config)
            if stamp not in plan['holds']:
                fail('Receiver retention plan does not protect rollback checkpoint')
            print('PASS: receiver Received UUID matches held Btrfs read-only snapshot')
            print('PASS: receiver prune plan protects:', stamp)
            print('NO snapshot deleted, no migration apply authorised')
        finally:
            writer_lock.close()
    finally:
        manager_lock.close()


if __name__ == '__main__':
    try:
        if len(sys.argv) != 3:
            fail('Usage: python3 - {verify|hold} YYYYMMDD-HHMMSSZ')
        operate(sys.argv[1], sys.argv[2])
    except Exception as exc:
        print('FAIL:', str(exc), file=sys.stderr)
        sys.exit(2)
