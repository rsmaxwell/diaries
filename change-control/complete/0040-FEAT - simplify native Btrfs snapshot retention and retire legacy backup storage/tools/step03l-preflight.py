#!/usr/bin/env python3
"""0040 Step 3L: read-only safety preflight for a disposable Btrfs rehearsal on mars."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

MOUNT = Path('/media/usb')
REHEARSAL = MOUNT / '@data' / '0040-step03l-rehearsal'
FORBIDDEN = (MOUNT / '@snapshots', MOUNT / '@data' / 'backup', MOUNT / '@data' / 'mars-received')

def cmd(*args):
    p = subprocess.run(args, capture_output=True, text=True, check=False)
    return {'returncode': p.returncode, 'stdout': p.stdout.strip(), 'stderr': p.stderr.strip()}

def inspect(mount=MOUNT, rehearsal=REHEARSAL, *, mount_info=None, which=shutil.which):
    checks = []
    def record(name, ok, detail):
        checks.append({'check':name,'passed':bool(ok),'detail':str(detail)})
    record('platform-linux', sys.platform == 'linux', sys.platform)
    try:
        raw_mounts = mount_info if mount_info is not None else Path('/proc/self/mountinfo').read_text()
        rows = [line.split(' - ',1) for line in raw_mounts.splitlines() if ' - ' in line]
        matches = [r for r in rows if len(r)==2 and len(r[0].split())>4 and r[0].split()[4] == str(mount)]
        is_btrfs = len(matches)==1 and matches[0][1].split()[0]=='btrfs'
        record('dedicated-btrfs-mount',is_btrfs, f'{len(matches)} mountpoint matches; btrfs={is_btrfs}')
    except OSError as e:
        record('dedicated-btrfs-mount',False,e)
    for exe in ('btrfs','findmnt','stat'):
        record('tool-'+exe, bool(which(exe)), which(exe) or 'missing')
    record('rehearsal-location',rehearsal == REHEARSAL if mount == MOUNT else rehearsal == mount/'@data'/'0040-step03l-rehearsal', rehearsal)
    for path in (mount,mount/'@data',rehearsal):
        if path.is_symlink():
            record('no-symlink-'+path.name,False,f'{path} is a symlink')
        else:
            record('no-symlink-'+path.name,True,str(path))
    record('rehearsal-not-present',not rehearsal.exists() and not rehearsal.is_symlink(), 'present: refuses existing directories' if rehearsal.exists() or rehearsal.is_symlink() else 'absent')
    record('data-parent-exists',(mount/'@data').is_dir(),mount/'@data')
    for protected in FORBIDDEN if mount == MOUNT else (mount/'@snapshots',mount/'@data'/'backup',mount/'@data'/'mars-received'):
        record('outside-protected-'+protected.name, rehearsal != protected and protected not in rehearsal.parents,protected)
    return {'schema':1,'mode':'read-only','host':os.uname().nodename if hasattr(os,'uname') else 'unknown', 'mount':str(mount),'rehearsal':str(rehearsal), 'all_passed':all(c['passed'] for c in checks),'checks':checks,'authorizes_creation':False,'authorizes_deletion':False}

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--json',action='store_true')
    opts=a.parse_args()
    result=inspect()
    if opts.json:
        print(json.dumps(result,indent=2))
    else:
        for c in result['checks']:
            print(('PASS' if c['passed'] else 'FAIL')+': '+c['check']+' — '+c['detail'])
        print('STEP03L-PREFLIGHT '+('PASS' if result['all_passed'] else 'BLOCKED')+' authorizes_creation=false authorizes_deletion=false')
    return 0 if result['all_passed'] else 2
if __name__=='__main__':
    sys.exit(main())
