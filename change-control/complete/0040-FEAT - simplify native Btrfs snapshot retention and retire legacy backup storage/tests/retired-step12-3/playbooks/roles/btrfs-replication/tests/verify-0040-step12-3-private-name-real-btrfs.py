#!/usr/bin/env python3
"""0040 Step 12.3: disposable real-Btrfs test of production private-name stream and publication helpers."""
import argparse
import importlib.util
import io
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

STAMP_A = '20261103-000000Z'
STAMP_B = '20261103-010000Z'
NONCE = 'c' * 64
PRIVATE_B = '.receive-' + NONCE
FILES = Path(__file__).resolve().parents[1] / 'files'
def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, FILES / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
STREAM = load_module('stream_runtime', 'btrfs-agreed-parent-stream-name.py')
STORAGE = load_module('storage_runtime', 'btrfs-agreed-parent-staging-storage.py')


def run(*args, input=None):
    result = subprocess.run(args, input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(f'{args!r} exited {result.returncode}: {result.stderr.decode(errors="replace")}')
    return result.stdout


def btrfs_fields(path):
    result = {}
    for line in run('btrfs', 'subvolume', 'show', str(path)).decode().splitlines():
        if ':' in line:
            key, value = line.strip().split(':', 1)
            result[key] = value.strip()
    return result


def real_btrfs_test():
    if os.geteuid() != 0:
        raise RuntimeError('real Btrfs image test must run as root')
    for executable in ('btrfs', 'mkfs.btrfs', 'mount', 'umount'):
        if not shutil.which(executable):
            raise RuntimeError('missing utility: ' + executable)
    work = Path(tempfile.mkdtemp(prefix='0040-private-stream-isolated-'))
    mounted = []
    try:
        src, dst = work / 'source', work / 'receiver'
        for root in (src, dst):
            root.mkdir(mode=0o700)
            image = work / (root.name + '.img')
            with open(image, 'xb') as handle:
                handle.truncate(512 * 1024 * 1024)
            run('mkfs.btrfs', '-q', '-f', str(image))
            run('mount', '-t', 'btrfs', '-o', 'loop', str(image), str(root))
            mounted.append(root)
        run('btrfs', 'subvolume', 'create', str(src / 'working'))
        (src / 'working' / 'payload.txt').write_text('test A\n')
        a = src / STAMP_A
        run('btrfs', 'subvolume', 'snapshot', '-r', str(src / 'working'), str(a))
        final = dst / '@data'
        final.mkdir(mode=0o700)
        run('btrfs', 'receive', str(final), input=run('btrfs', 'send', str(a)))
        (src / 'working' / 'payload.txt').write_text('test B\n')
        b = src / STAMP_B
        run('btrfs', 'subvolume', 'snapshot', '-r', str(src / 'working'), str(b))
        original_stream = run('btrfs', 'send', '-p', str(a), str(b))
        input_stream = io.BytesIO(original_stream)
        private_stream = STREAM.rewrite_first(input_stream, STAMP_B, NONCE)
        output = io.BytesIO()
        STREAM.forward_rest(input_stream, output)
        private_stream += output.getvalue()
        # Prove the name is changed BEFORE any receive operation can expose it.
        if STAMP_B.encode() in private_stream[:128] or PRIVATE_B.encode() not in private_stream[:128]:
            raise RuntimeError('rewritten first command not as expected')
        assert not (final / STAMP_B).exists()
        old_root, old_final = STORAGE.ROOT, STORAGE.FINAL
        STORAGE.ROOT, STORAGE.FINAL = dst, final
        try:
            binding = STORAGE.reserve(STAMP_B, NONCE, locks_held=True)
            run('btrfs', 'receive', str(final), input=private_stream)
        finally:
            STORAGE.ROOT, STORAGE.FINAL = old_root, old_final
        private = final / PRIVATE_B
        if (final / STAMP_B).exists():
            raise RuntimeError('final publication name was exposed by btrfs receive')
        if not private.is_dir():
            raise RuntimeError('private received name was not created')
        before = btrfs_fields(private)
        expected_uuid = btrfs_fields(b).get('UUID')
        if before.get('Received UUID') != expected_uuid or before.get('Flags') != 'readonly':
            raise RuntimeError(f'wrong received snapshot UUID/flags: {before!r}')
        if (private / 'payload.txt').read_text() != 'test B\n':
            raise RuntimeError('incremental content differs')
        old_root, old_final = STORAGE.ROOT, STORAGE.FINAL
        STORAGE.ROOT, STORAGE.FINAL = dst, final
        try:
            STORAGE.publish(STAMP_B, NONCE,
                directory_dev=binding['directory_dev'],
                directory_ino=binding['directory_ino'], locks_held=True,
                verified_receive=True, sender_authenticated=True,
                btrfs_identity_verified=True)
        finally:
            STORAGE.ROOT, STORAGE.FINAL = old_root, old_final
        after = btrfs_fields(final / STAMP_B)
        if after.get('Received UUID') != expected_uuid or after.get('UUID') != before.get('UUID') or after.get('Flags') != 'readonly':
            raise RuntimeError('publication altered read-only or snapshot identity')
        print('PASS: incremental stream received only under private same-parent name')
        print('PASS: received UUID and read-only state survive no-replace publication')
        print('NOTE: TEST ONLY; stream rewriting is not authorised for deployment')
    finally:
        problems = []
        for root in reversed(mounted):
            result = subprocess.run(['umount', str(root)], capture_output=True, text=True)
            if result.returncode:
                problems.append(f'{root}: {result.stderr.strip()}')
        if problems:
            print('PRESERVED: disposable images at', work, '\n' + '\n'.join(problems))
            raise RuntimeError('could not unmount disposable Btrfs filesystems')
        shutil.rmtree(work)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='run disposable real-Btrfs test as root')
    args = parser.parse_args()
    if not args.run:
        parser.error('requires explicit --run; creates and removes disposable Btrfs images')
    real_btrfs_test()
