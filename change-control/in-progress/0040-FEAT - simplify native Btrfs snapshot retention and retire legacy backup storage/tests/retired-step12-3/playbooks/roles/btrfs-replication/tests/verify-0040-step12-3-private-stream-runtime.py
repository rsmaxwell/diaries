#!/usr/bin/env python3
"""Source-level safety tests for bounded production first-command rewrite."""
import importlib.util
import io
from pathlib import Path
import struct
import unittest

FILE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-stream-name.py'
spec = importlib.util.spec_from_file_location('private_stream', FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
STAMP = '20261103-010000Z'
NONCE = 'c' * 64

def stream(*, first=STAMP.encode(), command=2, path_twice=False, invalid_checksum=False):
    payload = m.ATTRIBUTE.pack(15, len(first)) + first + m.ATTRIBUTE.pack(1, 16) + b'X' * 16
    if path_twice:
        payload += m.ATTRIBUTE.pack(15, len(first)) + first
    check = m.crc32c(m.HEADER.pack(len(payload), command, 0) + payload)
    if invalid_checksum:
        check ^= 1
    return m.MAGIC + struct.pack('<I', 1) + m.HEADER.pack(len(payload), command, check) + payload + b'remaining-stream'

class PartialRead(io.BytesIO):
    def read(self, n=-1):
        return super().read(min(n, 3) if n > 0 else n)

class Cases(unittest.TestCase):
    def test_rewrites_only_first_and_passes_rest(self):
        original = PartialRead(stream())
        modified = m.rewrite_first(original, STAMP, NONCE)
        out = io.BytesIO()
        m.forward_rest(original, out)
        self.assertEqual(out.getvalue(), b'remaining-stream')
        self.assertNotIn(STAMP.encode(), modified)
        self.assertIn(m.private_name(NONCE).encode(), modified)
        start = len(m.MAGIC) + 4
        length, command, crc = m.HEADER.unpack_from(modified, start)
        payload = modified[start + m.HEADER.size:]
        self.assertEqual(length, len(payload))
        self.assertEqual(crc, m.crc32c(m.HEADER.pack(length, command, 0) + payload))
        self.assertIn(b'X' * 16, payload)
    def test_full_subvolume_supported(self):
        self.assertIn(b'.receive-', m.rewrite_first(io.BytesIO(stream(command=1)), STAMP, NONCE))
    def test_rejects_wrong_original_name(self):
        with self.assertRaises(m.Refused): m.rewrite_first(io.BytesIO(stream()), '20261103-020000Z', NONCE)
    def test_rejects_malformed_nonce(self):
        with self.assertRaises(m.Refused): m.rewrite_first(io.BytesIO(stream()), STAMP, '../' + NONCE)
    def test_rejects_invalid_checksum(self):
        with self.assertRaises(m.Refused): m.rewrite_first(io.BytesIO(stream(invalid_checksum=True)), STAMP, NONCE)
    def test_rejects_duplicate_path(self):
        with self.assertRaises(m.Refused): m.rewrite_first(io.BytesIO(stream(path_twice=True)), STAMP, NONCE)
    def test_rejects_wrong_initial_command(self):
        with self.assertRaises(m.Refused): m.rewrite_first(io.BytesIO(stream(command=3)), STAMP, NONCE)
    def test_rejects_short_stream(self):
        with self.assertRaises(m.Refused): m.rewrite_first(io.BytesIO(stream()[:19]), STAMP, NONCE)
    def test_rejects_oversized_header_without_reading_body(self):
        prefix = m.MAGIC + struct.pack('<I', 1) + m.HEADER.pack(m.MAX_FIRST_COMMAND + 1, 2, 0)
        with self.assertRaises(m.Refused): m.rewrite_first(io.BytesIO(prefix), STAMP, NONCE)
    def test_endpoint_integrated_and_installer(self):
        endpoint = (FILE.parent / 'btrfs-native-endpoint.py').read_text()
        installer = (FILE.parent.parent / 'tasks/agreed-parent-runtime.yaml').read_text()
        self.assertIn('module.rewrite_first(sys.stdin.buffer, snapshot, nonce)', endpoint)
        self.assertIn('module.forward_rest(sys.stdin.buffer, out)', endpoint)
        self.assertIn('    - stream-name', installer)
        self.assertNotIn("root / '.receive-staging' / nonce", endpoint)

if __name__ == '__main__': unittest.main(verbosity=2)
