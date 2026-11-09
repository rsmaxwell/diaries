#!/usr/bin/env python3
"""0040-FEAT: disposable real-Btrfs acceptance for simplified replication.

Runs ONLY with --run and root. Creates two loopback Btrfs images under a
unique temporary directory; never references live mars/backup mount paths.
Exercises the actual simplified receiver CLI in a subprocess, including
its scoped-to-test lock, native receive, cleanup, state update and readback.
The sender-ahead correction is exercised in process without SSH.
"""
import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT_NAME = 'roles/btrfs-replication/files/btrfs-simplified-replication.py'
A = '20261104-010000Z'
B = '20261104-020000Z'
RUNNER = '''\
import importlib.util
import sys
from pathlib import Path
script, target, state, mount, fsuuid, lock = sys.argv[1:7]
spec = importlib.util.spec_from_file_location('isolated_simplified_receiver', script)
mod = __import__('importlib.machinery', fromlist=['SourceFileLoader']).SourceFileLoader('isolated_simplified_receiver', script)
module = type(sys)('isolated_simplified_receiver')
mod.exec_module(module)
module.RECEIVED = Path(target)
module.RECEIVER_STATE = Path(state)
module.RECEIVER_MOUNT = Path(mount)
module.RECEIVER_FS = fsuuid
module.MANAGER_LOCK = Path(lock)
# Isolated fixture has no legacy transactions. Do not probe any host datasets.
module.legacy_blocks = lambda: False
sys.exit(module.main(['receiver', *sys.argv[7:]]))
'''


def require(ok, text):
    if not ok:
        raise AssertionError(text)


def run(args, *, input=None, timeout=180, check=True):
    result = subprocess.run([str(a) for a in args], input=input, capture_output=True,
                            timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} returned {result.returncode}: '
                           f'{result.stderr.decode(errors="replace")[-2500:]}')
    return result


def btrfs_uuid(mount):
    output = run(['btrfs', 'filesystem', 'show', mount]).stdout.decode()
    match = re.search(r'\buuid:\s*([0-9a-f-]{36})\b', output, re.I)
    require(match is not None, 'Missing Btrfs filesystem identity')
    return match.group(1).lower()


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as source:
        for block in iter(lambda: source.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def check_prerequisites(script):
    require(os.geteuid() == 0, 'Must be run as root (sudo -n)')
    for program in ('btrfs', 'mkfs.btrfs', 'mount', 'umount'):
        require(shutil.which(program) is not None, 'Missing executable: ' + program)
    require(script.is_file(), 'Missing simplified replication implementation: ' + str(script))


def load_module(script):
    loader = __import__('importlib.machinery', fromlist=['SourceFileLoader']).SourceFileLoader(
        'simplified_real_fixture', str(script))
    module = type(sys)('simplified_real_fixture')
    loader.exec_module(module)
    return module


def test(root, script):
    m = load_module(script)
    src_mount, dst_mount = root / 'source-mount', root / 'receiver-mount'
    src_mount.mkdir(); dst_mount.mkdir()
    src_img, dst_img = root / 'source.img', root / 'receiver.img'
    for img in (src_img, dst_img):
        with open(img, 'wb') as f:
            f.truncate(512 * 1024 * 1024)
        run(['mkfs.btrfs', '-q', '-f', img], timeout=90)
    mounted = []
    try:
        for image, mountpoint in ((src_img, src_mount), (dst_img, dst_mount)):
            run(['mount', '-t', 'btrfs', '-o', 'loop', image, mountpoint], timeout=90)
            mounted.append(mountpoint)
            require(os.path.ismount(mountpoint), 'Loopback Btrfs not mounted: ' + str(mountpoint))
        source, received = src_mount / '@snapshots' / '@data', dst_mount / '@data' / 'mars-received' / '@data'
        source.mkdir(parents=True); received.mkdir(parents=True)
        src_state, dst_state = src_mount / 'state' / '.simple-agreed-parent.json', dst_mount / 'state' / '.simple-agreed-parent.json'
        src_state.parent.mkdir(); dst_state.parent.mkdir()
        local_lock = root / 'manager.lock'
        runner = root / 'isolated-receiver.py'
        runner.write_text(RUNNER, encoding='utf-8')
        destination_fs = btrfs_uuid(dst_mount)
        source_fs = btrfs_uuid(src_mount)
        base = src_mount / 'live'
        run(['btrfs', 'subvolume', 'create', base])
        with open(base / 'payload.bin', 'wb') as payload:
            payload.write(os.urandom(2 * 1024 * 1024))
        run(['btrfs', 'subvolume', 'snapshot', '-r', base, source / A])
        with open(base / 'payload.bin', 'ab') as payload:
            payload.write(os.urandom(8 * 1024 * 1024))
        run(['btrfs', 'subvolume', 'snapshot', '-r', base, source / B])
        parent_uuid, new_uuid = m.subvolume_info(source, A)['UUID'], m.subvolume_info(source, B)['UUID']
        # Transfer the agreed parent in the fixture. Never bootstrap against the live hosts.
        full_stream, incremental_stream, truncated_stream = root / 'full.stream', root / 'incremental.stream', root / 'truncated.stream'
        run(['btrfs', 'send', '-f', full_stream, source / A])
        run(['btrfs', 'receive', '-f', full_stream, received])
        require(m.verified(m.subvolume_info(received, A), parent_uuid, received=True), 'Baseline received UUID incorrect')
        m.save_state(src_state, m.initial_state(A, parent_uuid), create=True)
        m.save_state(dst_state, m.initial_state(A, parent_uuid), create=True)
        run(['btrfs', 'send', '-p', source / A, '-f', incremental_stream, source / B])
        length = incremental_stream.stat().st_size
        require(length > 262144, 'Incremental stream too small for meaningful interruption')
        with open(incremental_stream, 'rb') as stream, open(truncated_stream, 'wb') as target:
            target.write(stream.read(min(length // 3, 131072)))
        stopped = run(['btrfs', 'receive', '-f', truncated_stream, received], check=False)
        require(stopped.returncode != 0, 'Truncated stream must fail receive')
        residue = m.subvolume_info(received, B)
        if residue is None:
            print('OBSERVE: truncated Btrfs receive removed its incomplete subvolume')
            # Model the power-loss window where a previously created writable
            # receiver subvolume remains, using a real Btrfs subvolume.
            run(['btrfs', 'subvolume', 'create', received / B])
            print('OBSERVE: created disposable writable Btrfs crash residue for cleanup test')
        else:
            print('OBSERVE: truncated receive left real incomplete Btrfs subvolume')
        residue = m.subvolume_info(received, B)
        require(residue is not None and residue['Flags'] != 'readonly' and
                residue['Received UUID'] == '-', 'Unexpected incomplete Btrfs residue identity')
        require(m.load_state(dst_state)['parent']['timestamp'] == A,
                'Interrupted transfer unexpectedly advanced receiver')

        receiver_cmd = [sys.executable, '-B', runner, script, received, dst_state,
                        dst_mount, destination_fs, local_lock]
        # The actual receiver CLI must defer while the shared local lock is busy.
        held_fd = m.take_lock(local_lock)
        try:
            busy = run([*receiver_cmd, 'status'], check=False)
            require(busy.returncode == 75, 'Receiver did not back off on lock collision')
        finally:
            os.close(held_fd)
        print('PASS: non-blocking receiver lock backs off without changing snapshots')

        with open(incremental_stream, 'rb') as stream:
            response = subprocess.run([*receiver_cmd, 'receive', '--snapshot', B,
                                       '--uuid', new_uuid, '--parent', A,
                                       '--parent-uuid', parent_uuid],
                                      stdin=stream, capture_output=True, timeout=180)
        require(response.returncode == 0,
                'Native receiver cleanup/retry failed: ' + response.stderr.decode(errors='replace')[-2500:])
        require(b'cleaned one incomplete candidate' in response.stderr,
                'Recovery did not exercise actual incomplete-subvolume cleanup')
        require(m.verified(m.subvolume_info(received, B), new_uuid, received=True),
                'Retried receive failed Btrfs identity validation')
        require(digest(source / B / 'payload.bin') == digest(received / B / 'payload.bin'),
                'Retried receive payload differs')
        receiver_state = m.advance(m.initial_state(A, parent_uuid), B, new_uuid)
        require(m.load_state(dst_state) == receiver_state, 'Receiver state not advanced')
        require(m.load_state(src_state)['parent']['timestamp'] == A,
                'Sender state must remain old after simulated lost acknowledgement')
        print('PASS: real incomplete-subvolume cleanup and native incremental retry')

        # The source missed the receiver acknowledgement. The next cycle must
        # adopt the receiver's verified parent, never retransmit the same stream.
        def peer(op, *arguments):
            require(op == 'status' and not arguments, 'Lost-ack recovery must only query status')
            return {'state': m.load_state(dst_state)}
        with patch.object(m, 'SOURCE', source), patch.object(m, 'SOURCE_STATE', src_state), \
             patch.object(m, 'SOURCE_MOUNT', src_mount), patch.object(m, 'SOURCE_FS', source_fs), \
             patch.object(m, 'MANAGER_LOCK', local_lock), patch.object(m, 'peer', side_effect=peer), \
             patch.object(m, 'stream_send', side_effect=AssertionError('No retransmission permitted')):
            m.sender_main(SimpleNamespace(operation='cycle'))
        require(m.load_state(src_state) == receiver_state, 'Sender failed to reconcile lost acknowledgement')
        require(m.protected_stamps(receiver_state) == {A, B}, 'Current and prior parent not protected')
        print('PASS: receiver-ahead acknowledgement recovery without retransmission')
        print('PASS: source and receiver parent/prior state agree; both retained generations protected')
    finally:
        unmount_failures = []
        for mountpoint in reversed(mounted):
            umount = run(['umount', mountpoint], check=False)
            if umount.returncode or os.path.ismount(mountpoint):
                unmount_failures.append(str(mountpoint))
        if unmount_failures:
            raise RuntimeError('Could not unmount disposable Btrfs mounts; PRESERVE images at '
                               + str(root) + '; mounts=' + ', '.join(unmount_failures))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Explicit opt-in to disposable loopback Btrfs filesystem operations')
    parser.add_argument('--playbooks', type=Path, default=Path('/home/richard/playbooks'),
                        help='Path to Playbooks checkout supplying the simplified replication code')
    args = parser.parse_args()
    if not args.run:
        parser.error('No filesystem actions without explicit --run')
    directory = None
    try:
        script = (args.playbooks / SCRIPT_NAME).resolve()
        check_prerequisites(script)
        directory = Path(tempfile.mkdtemp(prefix='0040-simplified-real-btrfs-', dir='/var/tmp'))
        test(directory, script)
        shutil.rmtree(directory)
        print('PASS: disposable simplified real-Btrfs interrupted-receive integration')
        return 0
    except Exception as exc:
        print('FAIL: disposable simplified real-Btrfs: ' + str(exc), file=sys.stderr)
        if directory is not None:
            print('NOTE: preserved disposable fixture for diagnosis at ' + str(directory), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
