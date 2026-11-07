#!/usr/bin/env python3
"""Disposable real-Btrfs receiver retention verification for 0040 Step 12.

Requires --run and root. Creates temporary loop-backed Btrfs filesystems;
never refers to mars/backup's live mount paths. Does not set a live timer.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

STAMPS=['20261001-010000Z','20261002-010000Z','20261003-010000Z','20261004-010000Z']


def run(*cmd):
    return subprocess.run([str(x) for x in cmd],check=True,capture_output=True,text=True,timeout=180)


def fs_uuid(path):
    m=re.search(r'\buuid:\s*([0-9a-f-]{36})\b',run('btrfs','filesystem','show',path).stdout,re.I)
    if not m: raise RuntimeError('Missing temporary filesystem identity')
    return m.group(1)


def snapshot_uuid(path):
    m=re.search(r'^\s*UUID:\s*([0-9a-f-]{36})\s*$',run('btrfs','subvolume','show',path).stdout,re.M)
    if not m: raise RuntimeError('Missing temporary subvolume identity')
    return m.group(1)


def verify(disposable, manager_source):
    src=disposable/'src';dst=disposable/'dst'
    src.mkdir();dst.mkdir()
    for label in ('src','dst'):
        image=disposable/(label+'.img')
        with image.open('wb') as stream: stream.truncate(512*1024*1024)
        run('mkfs.btrfs','-q','-f',image)
    mounted=[]
    try:
        for mount in (src,dst):
            run('mount','-o','loop',disposable/(mount.name+'.img'),mount)
            mounted.append(mount)
        live=src/'live';run('btrfs','subvolume','create',live)
        receiver=dst/'@data';receiver.mkdir()
        state=dst/'.replication-state';state.mkdir(mode=0o700)
        identities={}
        for index,stamp in enumerate(STAMPS):
            (live/'sample.txt').write_text(f'disposable generation {index}\n')
            run('btrfs','subvolume','snapshot','-r',live,src/stamp)
            identities[stamp]=snapshot_uuid(src/stamp)
            # A full receive for each timestamp suffices for retention testing;
            # the incremental receive transport has its own accepted test.
            p1=subprocess.Popen(['btrfs','send',str(src/stamp)],stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
            p2=subprocess.Popen(['btrfs','receive',str(receiver)],stdin=p1.stdout,
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            p1.stdout.close()
            output,error=p2.communicate(timeout=120)
            p1.wait(timeout=30)
            send_error=p1.stderr.read()
            if p1.returncode or p2.returncode:
                raise RuntimeError('Disposable Btrfs send/receive failed: '+repr((send_error,error)))
        simple={'schema':1,'parent':{'timestamp':STAMPS[3],'uuid':identities[STAMPS[3]]},
                'prior':{'timestamp':STAMPS[2],'uuid':identities[STAMPS[2]]}}
        parent=state/'.simple-agreed-parent.json';parent.write_text(json.dumps(simple)+'\n');parent.chmod(0o600)
        holds=dst/'holds.json'
        holds.write_text(json.dumps({'schema':1,'holds':{
            STAMPS[0]:{'reason':'disposable historical checkpoint',
                       'source_uuids':{'@data':identities[STAMPS[0]]}}}})+'\n')
        holds.chmod(0o600)
        # Incompatible historical receipt metadata is preserved but never
        # trusted as proof of an accepted receive.
        receipt=state/(STAMPS[0]+'.json');receipt.write_text('{"source_filesystem_uuid":"HISTORICAL"}\n')
        receipt_bytes=receipt.read_bytes()
        # The unheld candidate carries a legacy receipt too: a real Btrfs
        # deletion must leave these historical evidence bytes untouched.
        prunable_receipt=state/(STAMPS[1]+'.json')
        prunable_receipt.write_bytes(b'{"legacy":"untrusted, preserved after prune"}\n')
        prunable_receipt_bytes=prunable_receipt.read_bytes()
        spec=importlib.util.spec_from_file_location('disposable_shared_manager',manager_source)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        module._SIMPLE_RECEIVER_ROOT=dst
        module._SIMPLE_RECEIVED=receiver
        module._SIMPLE_STATE=state
        module._SIMPLE_RECEIVER_MOUNT=dst
        module._SIMPLE_RECEIVER_FS=fs_uuid(dst)
        module._SIMPLE_MANAGER_LOCK=disposable/'manager.lock'
        config=module.Config(snapshot_root=dst,lock_path=module._SIMPLE_MANAGER_LOCK,
            writer_lock_path=state/'writer.lock',
            sources=(module.SnapshotSource('@data',None,snapshot_directory=receiver),),
            retention=module.RetentionPolicy(hourly=0,daily=0,weekly=0,monthly=0,yearly=0,minimum_age_minutes=30),
            verification=module.VerificationPolicy(False,'','','',None),
            checkpoint_holds_file=holds,checkpoint_holds_required=True,
            mode='receiver',receiver_state_dir=state,receiver_prune_enabled=False)
        with module.with_lock(config.lock_path):
            plan=module.receiver_simple_plan(config,now=datetime(2026,11,7,tzinfo=timezone.utc))
            assert plan['candidates']==[STAMPS[1]],plan['candidates']
            assert STAMPS[1] in plan['historical_receipts_on_candidates']
            try:
                module.receiver_simple_prune(config,max_delete=1)
                raise AssertionError('Deletion unexpectedly enabled')
            except module.SnapshotError as exc:
                assert 'disabled' in str(exc)
            assert all((receiver/stamp).exists() for stamp in STAMPS)
            # Disposable destruction is deliberately isolated; never copy
            # this enabled configuration onto backup before approval.
            config=__import__('dataclasses').replace(config,receiver_prune_enabled=True)
            assert module.receiver_simple_prune(config,max_delete=1)==1
            assert not (receiver/STAMPS[1]).exists()
            assert all((receiver/s).exists() for s in (STAMPS[0],STAMPS[2],STAMPS[3]))
            assert receipt.read_bytes()==receipt_bytes
            assert prunable_receipt.read_bytes()==prunable_receipt_bytes
            assert not (state/'.simple-prune-pending.json').exists()
            after=module.receiver_simple_plan(config)
            assert STAMPS[1] in after['historical_receipts_orphaned']
            assert module.receiver_simple_prune(config,max_delete=1)==0
        print('PASS: disposable received Btrfs prune incl. receipt-backed candidate, forensic receipt bytes preserved, holds, two parent pins, disabled gate and idempotence')
    finally:
        for mount in reversed(mounted):
            subprocess.run(['umount',str(mount)],check=False,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true',help='Explicitly allow isolated destructive disposable Btrfs fixture')
    parser.add_argument('--playbooks',type=Path,default=Path('/home/richard/playbooks'))
    args=parser.parse_args()
    if not args.run:
        print('PREVIEW ONLY. Use --run to create/dispose temporary loop-backed Btrfs test filesystems.')
        return
    if os.geteuid()!=0: raise SystemExit('FAIL: requires sudo/root')
    manager=args.playbooks/'roles/snapshots/files/btrfs-snapshot-manager.py'
    if not manager.is_file(): raise SystemExit('FAIL: manager source missing')
    for tool in ('btrfs','mkfs.btrfs','mount','umount'):
        if not shutil.which(tool):raise SystemExit(f'FAIL: missing {tool}')
    with tempfile.TemporaryDirectory(prefix='0040-receiver-retention-') as base:
        verify(Path(base),manager)

if __name__=='__main__':main()
