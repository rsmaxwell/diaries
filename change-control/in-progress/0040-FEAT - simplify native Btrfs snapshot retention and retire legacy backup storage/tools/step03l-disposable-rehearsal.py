#!/usr/bin/env python3
"""0040 Step 3L isolated Btrfs deletion/journal rehearsal. NEVER operates on production trees.

Run by streaming from Cygwin: ssh mars 'sudo python3 - --execute' < this-file.
Creates one hard-coded disposable tree; does not remove it automatically.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

MOUNT = Path('/media/usb')
BASE = MOUNT / '@data' / '0040-step03l-rehearsal'
PROTECTED = (MOUNT / '@snapshots', MOUNT / '@data' / 'backup', MOUNT / '@data' / 'mars-received')

def cmd(*argv):
    p = subprocess.run(argv, text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(argv)}\n{p.stdout}\n{p.stderr}")
    return p.stdout.strip()

def atomic_json(path, data):
    tmp = path.with_name(path.name + '.creating')
    with open(tmp, 'x', encoding='utf-8') as f:
        json.dump(data, f, sort_keys=True, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    dfd = os.open(str(path.parent), os.O_DIRECTORY)
    try: os.fsync(dfd)
    finally: os.close(dfd)

def preflight():
    if sys.platform != 'linux': raise RuntimeError('requires Linux')
    if os.geteuid() != 0: raise RuntimeError('requires root for disposable Btrfs operations')
    if MOUNT.is_symlink() or (MOUNT/'@data').is_symlink(): raise RuntimeError('symlink in parent path')
    if not (MOUNT/'@data').is_dir(): raise RuntimeError('missing @data parent')
    mount = cmd('findmnt', '-n', '-o', 'TARGET,FSTYPE', '-T', str(MOUNT)).split()
    if mount != [str(MOUNT), 'btrfs']: raise RuntimeError(f'unexpected mount: {mount}')
    if BASE.exists() or BASE.is_symlink(): raise RuntimeError('rehearsal target already exists: refuses overwrite')
    if any(BASE == p or p in BASE.parents or BASE in p.parents for p in PROTECTED):
        raise RuntimeError('rehearsal overlaps protected tree')
    cmd('btrfs', 'filesystem', 'show', str(MOUNT))
    print('PREFLIGHT PASS: dedicated Btrfs mount, strict fresh rehearsal path, root access')

def run():
    preflight()
    BASE.mkdir(mode=0o700)
    print('CREATED disposable root:', BASE, flush=True)
    source = BASE/'source'
    snapshots = BASE/'received-simulated'
    receipts = BASE/'receipts-simulated'
    journal = BASE/'journal'
    for d in (snapshots, receipts, journal): d.mkdir(mode=0o700)
    cmd('btrfs','subvolume','create',str(source))
    (source/'payload.txt').write_text('Feature 0040 disposable rehearsal only\n', encoding='utf-8')
    stamps = ('20261023-000001Z','20261023-000002Z','20261023-000003Z','20261023-000004Z')
    for stamp in stamps:
        cmd('btrfs','subvolume','snapshot','-r',str(source),str(snapshots/stamp))
        atomic_json(receipts/(stamp+'.json'), {'snapshot':stamp,'simulated':True})
    parent, success, before, after = stamps
    def is_subvol(stamp):
        p = subprocess.run(['btrfs','subvolume','show',str(snapshots/stamp)],capture_output=True)
        return p.returncode == 0
    assert all(is_subvol(s) for s in stamps)
    # Successful case: journal -> real Btrfs deletion -> receipt removal -> journal clear.
    atomic_json(journal/(success+'.json'),{'snapshot':success,'stage':'before-delete'})
    cmd('btrfs','subvolume','delete',str(snapshots/success))
    (receipts/(success+'.json')).unlink()
    (journal/(success+'.json')).unlink()
    # Crash before deletion: journal, snapshot and receipt all remain.
    atomic_json(journal/(before+'.json'),{'snapshot':before,'stage':'before-delete'})
    # Crash after deletion: journal and receipt remain; real subvolume is gone.
    atomic_json(journal/(after+'.json'),{'snapshot':after,'stage':'before-delete'})
    cmd('btrfs','subvolume','delete',str(snapshots/after))
    states = {
      'parent-preserved': is_subvol(parent) and (receipts/(parent+'.json')).is_file(),
      'success-clean': not is_subvol(success) and not (receipts/(success+'.json')).exists() and not (journal/(success+'.json')).exists(),
      'before-delete-recoverable': is_subvol(before) and (receipts/(before+'.json')).is_file() and (journal/(before+'.json')).is_file(),
      'after-delete-recoverable': not is_subvol(after) and (receipts/(after+'.json')).is_file() and (journal/(after+'.json')).is_file(),
    }
    result = {'feature':'0040-FEAT Step 3L','utc':datetime.now(timezone.utc).isoformat(),
              'rehearsal_root':str(BASE),'notes':'simulated receipts; no btrfs send/receive; no production manager invoked',
              'checks':states,'passed':all(states.values()),'automatic_cleanup':False}
    atomic_json(BASE/'result.json',result)
    print(json.dumps(result,indent=2),flush=True)
    if not result['passed']: raise RuntimeError('REHEARSAL FAILED; preserve disposable data for investigation')
    print('STEP03L-REHEARSAL PASS; evidence preserved, no cleanup performed')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        print('READ-ONLY: this command does nothing unless --execute is explicitly supplied')
    else:
        try: run()
        except Exception as e:
            print('STEP03L-REHEARSAL BLOCKED/FAILED:', e, file=sys.stderr)
            sys.exit(1)
