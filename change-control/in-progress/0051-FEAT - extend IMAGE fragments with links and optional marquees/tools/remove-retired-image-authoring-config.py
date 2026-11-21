#!/usr/bin/env python3
"""Remove only the two retired IMAGE authoring JSON keys from selected local config files.

Usage (Windows Cygwin):
  python3 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees/tools/remove-retired-image-authoring-config.py' --check /cygdrive/c/Users/Richard/.diaries/responder.json /cygdrive/c/Users/Richard/.diaries/responder.docker.json
  python3 .../remove-retired-image-authoring-config.py --apply <same files>

Creates a local backup alongside each modified file, never under Git change-control.
Do not publish copies of private responder JSON files or their secrets.
"""
import argparse
import json
import os
from pathlib import Path
import stat
import sys

RETIRED = {"imageFragmentWritesEnabled", "imageFragmentExtensionsWritesEnabled"}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.files:
        if not path.is_file():
            print("FAIL: missing file:", path)
            failed = True
            continue
        raw = path.read_bytes()
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Responder JSON root must be an object")
        except (ValueError, UnicodeDecodeError) as exc:
            print("FAIL: invalid JSON:", path, exc)
            failed = True
            continue
        present = sorted(RETIRED.intersection(data))
        if not present:
            print("PASS: no retired keys:", path)
            continue
        if args.check:
            print("NEEDS CLEANUP:", path, ", ".join(present))
            failed = True
            continue
        for name in present:
            data.pop(name)
        backup = path.with_name(path.name + ".before-0051-gate-cleanup.bak")
        if backup.exists():
            print("FAIL: existing backup (refusing overwrite):", backup)
            failed = True
            continue
        # No secrets are printed. Preserve directory, file mode and an untouched backup.
        backup.write_bytes(raw)
        os.chmod(backup, stat.S_IMODE(path.stat().st_mode))
        replacement = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        temp = path.with_name(path.name + ".0051-new")
        if temp.exists():
            print("FAIL: temporary path already exists:", temp)
            failed = True
            continue
        try:
            temp.write_text(replacement, encoding="utf-8")
            os.chmod(temp, stat.S_IMODE(path.stat().st_mode))
            os.replace(temp, path)
            print("PASS: removed", ", ".join(present), "from", path)
        finally:
            if temp.exists():
                temp.unlink()
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
