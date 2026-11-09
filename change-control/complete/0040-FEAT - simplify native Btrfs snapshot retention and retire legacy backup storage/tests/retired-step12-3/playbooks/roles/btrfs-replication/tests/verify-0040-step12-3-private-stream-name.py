#!/usr/bin/env python3
"""0040 Step 12.3: TEST ONLY. Verify private-name Btrfs receive stream on disposable images.

Never use this stream transformer in production: it is a narrowly bounded probe of
Btrfs send-stream command-name semantics, not an audited network-stream validator.
"""
import argparse
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
MAGIC = b'btrfs-stream\x00'
HEADER = struct.Struct('<IHI')
ATTRIBUTE = struct.Struct('<HH')
POLYNOMIAL = 0x82F63B78


def crc32c(data):
    value = 0
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (POLYNOMIAL if value & 1 else 0)
    return value & 0xFFFFFFFF


def command_crc(length, command, payload):
    return crc32c(HEADER.pack(length, command, 0) + payload)


def rewrite_initial_name(stream, expected, private):
    """Rewrite only first SUBVOL/SNAPSHOT PATH TLV. Reject unsupported framing.

    This deliberately buffers a stream; for bounded real test payloads ONLY.
    A production implementation would need a separately reviewed streaming filter.
    """
    if not stream.startswith(MAGIC) or len(stream) < len(MAGIC) + 4 + HEADER.size:
        raise ValueError('invalid Btrfs stream framing')
    version = struct.unpack_from('<I', stream, len(MAGIC))[0]
    if version not in (1, 2):
        raise ValueError('unsupported Btrfs protocol')
    start = len(MAGIC) + 4
    length, command, checksum = HEADER.unpack_from(stream, start)
    if command not in (1, 2) or length > 65536 or start + HEADER.size + length > len(stream):
        raise ValueError('invalid initial subvolume/snapshot command')
    payload_start = start + HEADER.size
    payload = stream[payload_start:payload_start + length]
    if command_crc(length, command, payload) != checksum:
        raise ValueError('original command checksum invalid')
    found = False
    output = bytearray()
    offset = 0
    while offset < len(payload):
        if offset + ATTRIBUTE.size > len(payload):
            raise ValueError('truncated TLV')
        attr_type, size = ATTRIBUTE.unpack_from(payload, offset)
        offset += ATTRIBUTE.size
        if offset + size > len(payload):
            raise ValueError('invalid TLV length')
        data = payload[offset:offset + size]
        offset += size
        if attr_type == 15:
            if found or data != expected.encode('ascii'):
                raise ValueError('unexpected or duplicate first snapshot path')
            found = True
            data = private.encode('ascii')
        if len(data) > 65535:
            raise ValueError('TLV too large')
        output += ATTRIBUTE.pack(attr_type, len(data)) + data
    if not found:
        raise ValueError('no PATH attribute')
    if not private.startswith('.receive-') or len(private) != 73 or any(c not in '0123456789abcdef' for c in private[9:]):
        raise ValueError('invalid private staging name')
    if '/' in expected or expected.startswith('.'):
        raise ValueError('invalid published name')
    new_payload = bytes(output)
    head = HEADER.pack(len(new_payload), command, command_crc(len(new_payload), command, new_payload))
    return stream[:start] + head + new_payload + stream[payload_start + length:]


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


def rename_noreplace(source, target):
    import ctypes
    libc = ctypes.CDLL(None, use_errno=True)
    operation = libc.renameat2
    operation.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    operation.restype = ctypes.c_int
    fd = os.open(source.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if operation(fd, os.fsencode(source.name), fd, os.fsencode(target.name), 1) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        os.fsync(fd)
    finally:
        os.close(fd)


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
        private_stream = rewrite_initial_name(original_stream, STAMP_B, PRIVATE_B)
        # Prove the name is changed BEFORE any receive operation can expose it.
        if STAMP_B.encode() in private_stream[:128] or PRIVATE_B.encode() not in private_stream[:128]:
            raise RuntimeError('rewritten first command not as expected')
        assert not (final / STAMP_B).exists()
        run('btrfs', 'receive', str(final), input=private_stream)
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
        rename_noreplace(private, final / STAMP_B)
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


class StreamTests(unittest.TestCase):
    def fixture(self, cmd=2, original=b'20261103-010000Z'):
        payload = ATTRIBUTE.pack(15, len(original)) + original + ATTRIBUTE.pack(1, 16) + b'X' * 16
        return MAGIC + struct.pack('<I', 1) + HEADER.pack(len(payload), cmd, command_crc(len(payload), cmd, payload)) + payload + b'FOLLOWING-COMMANDS'

    def test_snapshot_name_and_uuid_preserved(self):
        raw = self.fixture()
        modified = rewrite_initial_name(raw, STAMP_B, PRIVATE_B)
        self.assertNotIn(STAMP_B.encode(), modified)
        self.assertIn(PRIVATE_B.encode(), modified)
        self.assertIn(b'X' * 16, modified)
        self.assertTrue(modified.endswith(b'FOLLOWING-COMMANDS'))
        n, c, check = HEADER.unpack_from(modified, len(MAGIC) + 4)
        body = modified[len(MAGIC) + 4 + HEADER.size:len(MAGIC) + 4 + HEADER.size + n]
        self.assertEqual(check, command_crc(n, c, body))

    def test_full_subvolume_supported(self):
        self.assertIn(PRIVATE_B.encode(), rewrite_initial_name(self.fixture(cmd=1), STAMP_B, PRIVATE_B))

    def test_wrong_original_refused(self):
        with self.assertRaises(ValueError):
            rewrite_initial_name(self.fixture(), STAMP_A, PRIVATE_B)

    def test_corrupt_crc_refused(self):
        sample = bytearray(self.fixture())
        sample[len(MAGIC) + 4 + 7] ^= 2
        with self.assertRaises(ValueError):
            rewrite_initial_name(bytes(sample), STAMP_B, PRIVATE_B)

    def test_invalid_private_name_refused(self):
        with self.assertRaises(ValueError):
            rewrite_initial_name(self.fixture(), STAMP_B, '../../bad')

    def test_truncated_header_refused(self):
        with self.assertRaises(ValueError):
            rewrite_initial_name(MAGIC + b'\x01', STAMP_B, PRIVATE_B)

    def test_non_snapshot_command_refused(self):
        with self.assertRaises(ValueError):
            rewrite_initial_name(self.fixture(cmd=3), STAMP_B, PRIVATE_B)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='also run disposable real-Btrfs test as root')
    args = parser.parse_args()
    if args.run:
        real_btrfs_test()
    else:
        unittest.main(argv=['stream-tests'], verbosity=2)
