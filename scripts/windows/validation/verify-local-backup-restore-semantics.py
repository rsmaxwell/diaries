#!/usr/bin/env python3
"""Portable source verification for local backup/restore dataset semantics."""
from __future__ import annotations
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
MODES = ("development-infrastructure", "local-docker-build", "local-published-smoke")
OPS = ("backup-db-to-binary.bat", "backup-db-to-sql.bat", "restore-db-from-binary.bat", "restore-db-from-sql.bat")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> int:
    try:
        resolver = (ROOT / "scripts/windows/common/resolve-effective-dataset.ps1").read_text(encoding="utf-8")
        writer = (ROOT / "scripts/windows/common/write-db-backup-manifest.ps1").read_text(encoding="utf-8")
        verifier = (ROOT / "scripts/windows/common/verify-db-backup-manifest.ps1").read_text(encoding="utf-8")
        require("$datasetName = Split-Path -Leaf $dbPath" in resolver,
                "dataset identity is derived from the effective database directory, not launch mode")
        require("files-development-common" in resolver and "shared by all three local launch modes" in resolver,
                "common local dataset is explicitly identified as cross-mode sharing")
        require("backupType = 'database-only'" in writer and "completeDatasetBackup = $false" in writer,
                "database backup manifest explicitly says it is not a complete dataset backup")
        for field in ("logicalDataset", "effectiveDatabaseDataDir", "databaseBackupFile", "effectiveFilesDir",
                      "resolvedPhysicalFilesRoot", "applicationSourceIdentity", "imageRowCount", "cataloguedFileCount"):
            require(field in writer, f"sidecar manifest records {field}")
        require("Refusing restore" in verifier and "physical Files root" in verifier,
                "manifest verification rejects a restore against a different database/Files pair")
        require("No Step-7 dataset manifest exists" in verifier,
                "legacy database backups remain usable with an explicit database-only warning")

        for mode in MODES:
            for op in OPS:
                path = ROOT / "scripts/windows" / mode / op
                text = path.read_text(encoding="utf-8")
                require("validate-dataset-pair.bat" in text, f"{mode}/{op} validates the paired selectors")
                require("resolve-effective-dataset.ps1" in text, f"{mode}/{op} resolves effective dataset identity")
                require(r"data\database-backups\%DIARIES_DATASET_NAME%" in text,
                        f"{mode}/{op} uses effective-dataset backup directory")
                require("%DIARIES_EFFECTIVE_FILES_ROOT%" in text,
                        f"{mode}/{op} reports the matching physical Files root")
                require("DATABASE-ONLY" in text,
                        f"{mode}/{op} labels its operation as database-only")
                if op.startswith("backup"):
                    require("diaries-%DIARIES_DATASET_NAME%-%TIMESTAMP%" in text,
                            f"{mode}/{op} names default backups from effective dataset identity")
                    require("write-db-backup-manifest.ps1" in text,
                            f"{mode}/{op} writes the dataset sidecar manifest")
                    require("SELECT count(*) FROM public.image;" in text,
                            f"{mode}/{op} captures Image catalogue row count")
                else:
                    require("verify-db-backup-manifest.ps1" in text,
                            f"{mode}/{op} checks sidecar identity before destructive restore")
                    require("NO - mutable Files bytes will not be restored" in text,
                            f"{mode}/{op} does not claim to restore a complete dataset")

        # Guard against accidental reintroduction of mode-labelled default patterns.
        joined = "\n".join((ROOT / "scripts/windows" / m / o).read_text(encoding="utf-8") for m in MODES for o in OPS)
        require(not re.search(r'set "BACKUP_DIR=.*database-backups\\(?:development-infrastructure|local-docker-build|local-published-smoke)"', joined),
                "no local database script selects a backup directory solely from launch mode")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: local matched backup/restore semantics verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
