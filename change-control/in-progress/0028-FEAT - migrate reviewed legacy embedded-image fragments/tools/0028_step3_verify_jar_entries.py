#!/usr/bin/env python3
"""Verify 0028 one-shot CLI and journal SQL inside a built fat JAR (read-only).

ZIP entries are examined directly, avoiding CRLF/newline differences from
Windows JDK `jar tf` output in Cygwin. The helper never runs Java or migration.
"""
import sys
from pathlib import Path
from zipfile import ZipFile, BadZipFile

REQUIRED = (
    'com/rsmaxwell/diaries/responder/migration/migration0028/Migration0028ReviewedFragments.class',
    'migration0028/001-create-journal.sql',
)


def verify_jar(path):
    """Return the required entries' uncompressed sizes, or raise ValueError."""
    path = Path(path)
    if not path.is_file():
        raise ValueError('built fat JAR does not exist: ' + str(path))
    try:
        with ZipFile(path, 'r') as archive:
            names = archive.namelist()
            checked = {}
            for name in REQUIRED:
                if names.count(name) != 1:
                    related = [s for s in names if 'migration0028' in s and
                               (s.endswith('.class') or s.endswith('.sql'))][:12]
                    raise ValueError('built fat JAR contains ' + str(names.count(name)) +
                                     ' copies of required entry ' + name +
                                     '; related entries: ' + repr(related))
                entry = archive.getinfo(name)
                if entry.is_dir() or entry.file_size == 0:
                    raise ValueError('required JAR entry is empty: ' + name)
                # Reading the entry also validates its CRC; do not load the entire JAR.
                with archive.open(name) as stream:
                    while stream.read(1024 * 1024):
                        pass
                checked[name] = entry.file_size
            return checked
    except (BadZipFile, OSError, EOFError, RuntimeError) as exc:
        raise ValueError('built fat JAR is invalid or required contents unreadable: ' + str(exc)) from exc


def main(argv):
    if len(argv) != 2:
        print('Usage: 0028_step3_verify_jar_entries.py <fat-jar>', file=sys.stderr)
        return 2
    try:
        found = verify_jar(argv[1])
    except ValueError as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        return 2
    print('PASS: required 0028 migration class and SQL journal resource are present and readable')
    for name, size in found.items():
        print('  ' + name + ' (' + str(size) + ' bytes)')
    print('One-shot invocation requires java -cp <fat-jar> <migration-main-class>; NOT java -jar')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
