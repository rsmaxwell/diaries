#!/usr/bin/env python3
"""Portable source verification for 0031-FEAT Step 8 migration-safety tooling."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
STEP8 = ROOT / "scripts/windows/0031-step8"
FEATURE = ROOT / "change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> int:
    try:
        freeze = (STEP8 / "freeze-local-writes.ps1").read_text(encoding="utf-8")
        db = (STEP8 / "capture-local-database-backup.ps1").read_text(encoding="utf-8")
        files = (STEP8 / "capture-shared-files-snapshot.ps1").read_text(encoding="utf-8")

        require("diaries-local-responder" in freeze and "diaries-published-smoke-responder" in freeze,
                "local freeze stops both Docker responder variants")
        require("GetActiveTcpListeners()" in freeze and "Get-NetTCPConnection" not in freeze,
                "local freeze checks TCP/8081 without the privileged Get-NetTCPConnection CIM query")
        require("GetActiveTcpListeners()" in db and "GetActiveTcpListeners()" in files,
                "database backup and Files snapshot reuse the non-privileged TCP listener check")
        require("Leave the responder stopped" in freeze,
                "local freeze explicitly preserves the write freeze for later migration steps")

        for container in ("diaries-development-db", "diaries-local-db", "diaries-published-smoke-db"):
            require(container in db, f"local backup can identify running database mode {container}")
        require("Exactly one local Diaries database container must be running" in db,
                "local backup refuses ambiguous simultaneous local database writers")
        require("backup-db-to-binary.bat" in db and "step8-premigration" in db,
                "local Step 8 capture reuses the Step 7 binary database backup path with an explicit pre-migration name")
        require("preMigrationSharedFilesDir = 'files'" in db,
                "local Step 8 manifest records the old shared source tree separately from the configured target Files selector")
        require("configuredTargetFilesDir" in db and "databaseBackupSha256" in db,
                "local Step 8 manifest records target selector and database backup checksum")

        require("ProductionWriteFreezeConfirmed" in files,
                "shared Files snapshot requires explicit production write-freeze confirmation")
        require("Assert-LocalWriteFreeze" in files,
                "shared Files snapshot re-verifies the local write freeze")
        require(".image-staging" in files and "seedIntoNewRootsWithoutReview = $false" in files,
                "shared Files snapshot reviews staging and forbids blind propagation to new roots")
        require("robocopy" in files and "/COPY:DAT" in files and "/DCOPY:DAT" in files,
                "shared Files tree is copied with deterministic Windows/NAS copy tooling")
        require("Get-FileHash" in files and "Compare-Object" in files,
                "source and snapshot are verified using complete SHA-256 inventories")
        require("includedInRollbackSnapshot = $true" in files,
                "staging content is retained in the rollback snapshot even when excluded from future seeding")
        require("Do not restart production/local responders yet" in files,
                "snapshot tooling keeps the migration write freeze in force for Step 9")

        implementation = (FEATURE / "IMPLEMENTATION-STEPS.md").read_text(encoding="utf-8")
        require("## Step 8 — Freeze mutable writes and take pre-migration backups" in implementation,
                "Step 8 remains defined in the implementation plan")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: 0031-FEAT Step 8 local migration-safety tooling verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
