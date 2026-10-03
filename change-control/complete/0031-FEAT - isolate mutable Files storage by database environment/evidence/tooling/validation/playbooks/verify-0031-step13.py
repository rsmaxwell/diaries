#!/usr/bin/env python3
"""Portable source verification for 0031-FEAT Step 13 production controls."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "roles/diaries/files/sync/scripts/step13-capture-production-control.sh"
README = ROOT / "roles/diaries/files/sync/scripts/README.md"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> int:
    try:
        text = SCRIPT.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")
        require("Production responder is running" in text and "write freeze" in text,
                "production controls refuse to run with responder writes enabled")
        require("DIARIES_FILES_DIR" in text and '== "files"' in text,
                "production controls are pinned to the production files selector")
        require("SELECT id,version,relative_path" in text and "ORDER BY id" in text,
                "production Image catalogue is captured deterministically")
        require("find /data/files -type f" in text and "sha256sum" in text,
                "production mutable Files bytes are inventoried with SHA-256")
        require(".image-staging" in text,
                "production Files inventory explicitly includes staging state")
        require("cmp -s" in text and "Production Image catalogue changed" in text,
                "after control fails on any production catalogue or Files difference")
        require("0031 Step 13" in readme and "step13-capture-production-control.sh" in readme,
                "production operating documentation covers Step 13")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: 0031-FEAT Step 13 production control tooling verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
