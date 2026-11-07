#!/usr/bin/env python3
"""0040 Step 12.3: isolated real-Btrfs staged receive/publication smoke test.

ONLY creates disposable, freshly allocated image files. Never formats a device,
modifies production mounts, or enables runtime cleanup. Root + btrfs-progs and
CAP_SYS_ADMIN (loopback mount) are required. Work is unmounted on exit; if a
mount cannot be safely unmounted its image and directory are retained.
"""
import argparse
import json
import importlib.util
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

FILES = Path(__file__).resolve().parents[1] / 'files'
STAMP_A = '20261103-090000Z'
STAMP_B = '20261103-090100Z'
NONCE = 'e' * 64
UUID = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z')


def run(*argv, input=None):
    return subprocess.run(argv, input=input, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)


def show(path):
    output = run('btrfs', 'subvolume', 'show', '--', str(path)).stdout.decode()
    fields = {}
    for line in output.splitlines():
        if ':' in line:
            k, v = line.strip().split(':', 1)
            if k in ('UUID', 'Received UUID', 'Flags'):
                if k in fields:
                    raise RuntimeError('duplicate Btrfs show field ' + k)
                fields[k] = v.strip()
    return fields


def assert_received(source, target):
    src = show(source)
    dst = show(target)
    if not UUID.fullmatch(src.get('UUID', '')):
        raise RuntimeError('invalid source UUID')
    if dst.get('Received UUID') != src['UUID'] or dst.get('Flags') != 'readonly':
        raise RuntimeError(f'received Btrfs identity mismatch: {src!r} {dst!r}')
    if not UUID.fullmatch(dst.get('UUID', '')):
        raise RuntimeError('missing destination subvolume UUID')
    return src, dst


def send_receive(source, destination, parent=None):
    command = ['btrfs', 'send']
    if parent is not None:
        command.extend(['-p', str(parent)])
    command.append(str(source))
    send = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        recv = subprocess.Popen(['btrfs', 'receive', str(destination)],
                                stdin=send.stdout, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        send.stdout.close()
        recv_stdout, recv_stderr = recv.communicate()
        send_stderr = send.stderr.read()
        sent = send.wait()
        if sent or recv.returncode:
            raise RuntimeError(f'btrfs send/receive failed: send={sent} receive={recv.returncode} '
                               f'send_stderr={send_stderr.decode(errors="replace")} '
                               f'recv_stderr={recv_stderr.decode(errors="replace")}')
    finally:
        if send.poll() is None:
            send.kill()
            send.wait()
        send.stderr.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='explicitly authorise isolated image test')
    args = parser.parse_args()
    if not args.run:
        parser.error('specify --run to create disposable Btrfs image files and mounts')
    if os.geteuid() != 0:
        raise RuntimeError('root required for disposable loopback filesystem mounts')
    for binary in ('btrfs', 'mkfs.btrfs', 'mount', 'umount'):
        if shutil.which(binary) is None:
            raise RuntimeError(f'{binary} not installed; no live filesystems touched')
    # Dedicated names under a newly created temp directory, never a caller path.
    work = Path(tempfile.mkdtemp(prefix='0040-btrfs-isolated-'))
    mounted = []
    try:
        source_img, receiver_img = work / 'source.img', work / 'receiver.img'
        source_root, receiver_root = work / 'source', work / 'receiver'
        source_root.mkdir(mode=0o700)
        receiver_root.mkdir(mode=0o700)
        for img in (source_img, receiver_img):
            fd = os.open(img, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            try:
                os.ftruncate(fd, 512 * 1024 * 1024)
            finally:
                os.close(fd)
            run('mkfs.btrfs', '-q', '-f', str(img))
        for img, root in ((source_img, source_root), (receiver_img, receiver_root)):
            run('mount', '-t', 'btrfs', '-o', 'loop', str(img), str(root))
            mounted.append(root)
        src = source_root / 'snapshots'
        src.mkdir()
        run('btrfs', 'subvolume', 'create', str(source_root / 'working'))
        (source_root / 'working' / 'payload.txt').write_text('A: baseline\n')
        a = src / STAMP_A
        run('btrfs', 'subvolume', 'snapshot', '-r', str(source_root / 'working'), str(a))
        (source_root / 'working' / 'payload.txt').write_text('B: increment\n')
        b = src / STAMP_B
        run('btrfs', 'subvolume', 'snapshot', '-r', str(source_root / 'working'), str(b))
        # Same layout as receiver's real canonical ROOT: @data, .receive-staging.
        final = receiver_root / '@data'
        final.mkdir()
        # Receive A normally (it is the protected incremental parent on receiver).
        send_receive(a, final)
        assert_received(a, final / STAMP_A)
        spec = importlib.util.spec_from_file_location(
            'staging_storage_test', FILES / 'btrfs-agreed-parent-staging-storage.py')
        storage = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(storage)
        storage.ROOT = receiver_root
        storage.STAGING = receiver_root / '.receive-staging'
        storage.FINAL = final
        binding = storage.reserve(STAMP_B, NONCE, locks_held=True)
        stage = Path(binding['staged_subvolume'])
        # Receive incremental B into the private nonce-specific transaction dir.
        send_receive(b, Path(binding['staging_parent']), parent=a)
        source_b, staged_b = assert_received(b, stage)
        # Also exercise the same receiver-local read-only inspector used by
        # the fixed staged coordinator, with paths confined to this image.
        inspection_spec = importlib.util.spec_from_file_location(
            'receive_core_test', FILES / 'btrfs-agreed-parent-receive-core.py')
        inspector = importlib.util.module_from_spec(inspection_spec)
        inspection_spec.loader.exec_module(inspector)
        state_dir = receiver_root / '.replication-state'
        state_dir.mkdir(mode=0o700)
        journal = state_dir / '.agreed-parent-transfer-pending.json'
        journal.write_text(json.dumps({
            'schema': 1, 'status': 'receiving', 'nonce': NONCE,
            'candidate': {'timestamp': STAMP_B, 'uuid': source_b['UUID']},
            'staging': {'directory_dev': binding['directory_dev'],
                        'directory_ino': binding['directory_ino']}}))
        journal.chmod(0o600)
        inspector.STATE = state_dir
        inspector.RECEIVER_ROOT = receiver_root
        inspection = inspector.inspect_staged_received(
            {'timestamp': STAMP_B, 'uuid': source_b['UUID']}, NONCE,
            state_dir=state_dir)
        if inspection.get('subvolume_uuid') != staged_b['UUID'] or inspection.get('publication_authorized') is not False:
            raise RuntimeError('trusted staged inspection mismatch')
        if (stage / 'payload.txt').read_text() != 'B: increment\n':
            raise RuntimeError('incremental staged payload mismatch')
        if not stage.is_dir() or stat.S_IMODE(stage.parent.stat().st_mode) != 0o700:
            raise RuntimeError('unsafe staged directory')
        # This calls the actual no-overwrite filesystem helper. Its three booleans
        # are local test fixtures, NOT authenticated sender completion evidence.
        receipt = storage.publish(
            STAMP_B, NONCE, directory_dev=binding['directory_dev'],
            directory_ino=binding['directory_ino'], locks_held=True,
            verified_receive=True, sender_authenticated=True,
            btrfs_identity_verified=True)
        if receipt.get('status') != 'published-awaiting-receipt':
            raise RuntimeError('publication status incorrect')
        _, published_b = assert_received(b, final / STAMP_B)
        if staged_b['UUID'] != published_b['UUID'] or stage.exists():
            raise RuntimeError('published subvolume identity changed or staging remains')
        try:
            storage.publish(STAMP_B, NONCE, directory_dev=binding['directory_dev'],
                            directory_ino=binding['directory_ino'], locks_held=True,
                            verified_receive=True, sender_authenticated=True,
                            btrfs_identity_verified=True)
            raise RuntimeError('second publication unexpectedly succeeded')
        except storage.Refused:
            pass
        if (final / STAMP_B / 'payload.txt').read_text() != 'B: increment\n':
            raise RuntimeError('published payload changed')
        print('PASS: isolated real-Btrfs A->B incremental staging, received UUID, readonly, no-overwrite publication')
        print('NOTE: fixed receiver CLI, authenticated finalisation, crash fencing and cleanup are NOT exercised')
    finally:
        # Never delete an image while it is still mounted: that can hide an
        # active filesystem and lose recovery evidence from a failed run.
        unmount_failed = False
        for root in reversed(mounted):
            result = subprocess.run(['umount', str(root)], capture_output=True, text=True)
            if result.returncode != 0:
                unmount_failed = True
                print(f'FAIL: cannot unmount {root}: {result.stderr}; preserve {work}', file=sys.stderr)
        if not unmount_failed:
            shutil.rmtree(work)
        else:
            raise RuntimeError(f'isolated Btrfs test mounts remain; manually inspect {work}')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'FAIL: isolated real Btrfs test: {exc}', file=sys.stderr)
        sys.exit(1)
