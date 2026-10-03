#!/usr/bin/env python3
"""Portable source verification for 0031-FEAT Step 8 production tooling."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "roles/diaries/files/sync/scripts"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> int:
    try:
        freeze = (SCRIPTS / "step8-freeze-writes.sh").read_text(encoding="utf-8")
        capture = (SCRIPTS / "step8-capture-production-database-backup.sh").read_text(encoding="utf-8")
        existing = (SCRIPTS / "backup-db-to-binary.sh").read_text(encoding="utf-8")

        require('stop "${RESPONDER_SERVICE}"' in freeze,
                "production freeze stops only the responder write path")
        require("database remains running" in freeze,
                "production freeze keeps PostgreSQL available for pg_dump")
        require("data/0031-step8" in freeze,
                "production freeze writes durable runtime evidence outside source sync content")

        require("Run ${SCRIPT_DIR}/step8-freeze-writes.sh first" in capture,
                "production capture refuses to run while responder writes are enabled")
        require('PRODUCTION_FILES_DIR' in capture and 'expected frozen Step-2 value \'files\'' in capture,
                "production capture asserts that the pre-split production Files selector is files")
        require('"${BACKUP_SCRIPT}"' in capture,
                "production Step 8 capture reuses the Step 7 binary backup helper")
        require("sha256sum" in capture and "databaseBackupSha256" in capture,
                "production database backup and sidecar are checksummed and recorded")
        require("runtimeImages" in capture,
                "production Step 8 manifest records runtime image identity")
        require("database-only" in existing.lower(),
                "underlying production backup helper still declares database-only semantics")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: 0031-FEAT Step 8 production migration-safety tooling verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
