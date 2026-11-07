#!/usr/bin/env python3
"""0040 Step 12.3: disposable Btrfs experiment for received read-only rename semantics.

Explicit --run required; creates only new sparse image files; never touches the
production receiver tree. No storage module or replication runtime is changed.
"""
import argparse
import ctypes
import errno
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

STAMP = '20261103-090100Z'
NONCE = 'a' * 64


def run(*cmd, input=None):
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=input)


def fields(path):
    result = run('btrfs', 'subvolume', 'show', str(path)).stdout.decode()
    out = {}
    for line in result.splitlines():
        if ':' in line:
            key, val = line.strip().split(':', 1)
            if key in ('UUID', 'Received UUID', 'Flags'):
                out[key] = val.strip()
    return out


def rename_noreplace(source, target):
    """Use the same kernel renameat2 RENAME_NOREPLACE operation as publication."""
    libc = ctypes.CDLL(None, use_errno=True)
    operation = getattr(libc, 'renameat2', None)
    if operation is None:
        raise RuntimeError('renameat2 unavailable')
    operation.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    operation.restype = ctypes.c_int
    src_fd = os.open(source.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    dst_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if operation(src_fd, os.fsencode(source.name), dst_fd, os.fsencode(target.name), 1):
            err = ctypes.get_errno()
            return err
        os.fsync(src_fd)
        os.fsync(dst_fd)
        return 0
    finally:
        os.close(dst_fd)
        os.close(src_fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='explicitly authorise isolated image test')
    args = parser.parse_args()
    if not args.run:
        parser.error('specify --run to create disposable Btrfs image files and mounts')
    if os.geteuid() != 0:
        raise RuntimeError('root required')
    for cmd in ('btrfs', 'mkfs.btrfs', 'mount', 'umount'):
        if not shutil.which(cmd):
            raise RuntimeError(f'missing tool: {cmd}')
    work = Path(tempfile.mkdtemp(prefix='0040-btrfs-rename-isolated-'))
    mounted = []
    try:
        images = [work / 'source.img', work / 'receiver.img']
        roots = [work / 'source', work / 'receiver']
        for image, root in zip(images, roots):
            root.mkdir(mode=0o700)
            fd = os.open(image, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                os.ftruncate(fd, 512 * 1024 * 1024)
            finally:
                os.close(fd)
            run('mkfs.btrfs', '-q', '-f', str(image))
            run('mount', '-t', 'btrfs', '-o', 'loop', str(image), str(root))
            mounted.append(root)
        source, dest = roots
        run('btrfs', 'subvolume', 'create', str(source / 'working'))
        (source / 'working' / 'payload.txt').write_text('disposable Btrfs received snapshot\n')
        snapshot = source / STAMP
        run('btrfs', 'subvolume', 'snapshot', '-r', str(source / 'working'), str(snapshot))
        final = dest / '@data'
        final.mkdir()
        stream = run('btrfs', 'send', str(snapshot)).stdout
        run('btrfs', 'receive', str(final), input=stream)
        received = final / STAMP
        source_uuid = fields(snapshot)['UUID']
        before = fields(received)
        if before.get('Received UUID') != source_uuid or before.get('Flags') != 'readonly':
            raise RuntimeError('initial received identity or readonly flag differs')

        # Cross-parent: directly test the existing failing architecture; never
        # infer success from Python's ordinary-directory rename behaviour.
        stage_parent = dest / '.receive-staging' / NONCE
        stage_parent.mkdir(parents=True, mode=0o700)
        cross = stage_parent / STAMP
        cross_code = rename_noreplace(received, cross)
        print(f'OBSERVE: cross-parent readonly received-subvolume rename errno={cross_code} '
              f'({os.strerror(cross_code) if cross_code else "success"})')
        if cross_code == 0:
            # A kernel that supports this move may keep the original layout.
            code = rename_noreplace(cross, received)
            if code:
                raise RuntimeError(f'cross-parent restore failed: {os.strerror(code)}')
            print('OBSERVE: cross-parent rename supported by this kernel')
        elif cross_code != errno.EROFS:
            raise RuntimeError(f'unexpected cross-parent failure errno={cross_code}')

        # Same-parent: exact renameat2 operation and readonly/received-UUID
        # preservation. The hidden name is diagnostic only; btrfs receive itself
        # still initially created the visible final name.
        hidden = final / f'.{STAMP}.pending-{NONCE}'
        code = rename_noreplace(received, hidden)
        if code:
            raise RuntimeError(f'same-parent readonly rename failed: {os.strerror(code)}')
        middle = fields(hidden)
        if middle.get('Received UUID') != source_uuid or middle.get('UUID') != before.get('UUID') or middle.get('Flags') != 'readonly':
            raise RuntimeError('received identity changed during same-parent rename')
        code = rename_noreplace(hidden, received)
        if code:
            raise RuntimeError(f'same-parent restore failed: {os.strerror(code)}')
        after = fields(received)
        if after != before:
            raise RuntimeError('received Btrfs metadata changed after roundtrip')
        print('PASS: same-parent renameat2 no-replace preserves readonly and received UUID')
        print('NOTE: this is a boundary experiment, NOT a safe receive/publication protocol: '
              'btrfs receive first created the candidate at the visible final name')
    finally:
        failed = False
        for mount in reversed(mounted):
            result = subprocess.run(['umount', str(mount)], capture_output=True, text=True)
            if result.returncode:
                failed = True
                print(f'FAIL: unmount {mount}: {result.stderr}; preserve {work}', file=sys.stderr)
        if failed:
            raise RuntimeError(f'mounted test images retained at {work}')
        shutil.rmtree(work)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f'FAIL: isolated Btrfs rename boundary: {error}', file=sys.stderr)
        sys.exit(1)
