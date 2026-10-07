#!/usr/bin/env python3
"""Portable source verification for the frozen local database-only backup/restore contract."""
from __future__ import annotations
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
MODES = ("development-infrastructure", "local-docker-build", "local-published-smoke")
BACKUPS = ("backup-db-to-binary.bat", "backup-db-to-sql.bat")
RESTORES = ("restore-db-from-binary.bat", "restore-db-from-sql.bat")
OPS = BACKUPS + RESTORES


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> int:
    try:
        resolver = (ROOT / "scripts/windows/common/resolve-effective-dataset.ps1").read_text(encoding="utf-8")
        pair_guard = (ROOT / "scripts/windows/common/validate-dataset-pair.ps1").read_text(encoding="utf-8")
        writer = (ROOT / "scripts/windows/common/write-db-backup-manifest.ps1").read_text(encoding="utf-8")
        verifier = (ROOT / "scripts/windows/common/verify-db-backup-manifest.ps1").read_text(encoding="utf-8")
        local_example = (ROOT / "config/environments/local.env.example").read_text(encoding="utf-8")

        # Effective dataset identity is deliberately derived after mode env + local.env
        # overrides, so launch mode alone cannot define the backup namespace.
        require("$datasetName = Split-Path -Leaf $dbPath" in resolver,
                "dataset identity is derived from the effective database directory, not launch mode")
        require("files-development-common" in resolver and "shared by all three local launch modes" in resolver,
                "common local dataset is explicitly identified as cross-mode sharing")
        require("'common' = 'files-development-common'" in pair_guard,
                "0031 pair guard freezes common database -> common Files selector")
        require("DIARIES_DB_DATA_DIR=./data/database/common" in local_example and
                "DIARIES_FILES_DIR=files-development-common" in local_example,
                "local.env.example proves the supported shared common database + Files pair")

        # Freeze the database-only sidecar schema and compatibility behaviour.
        for token in (
            "schemaVersion = 1",
            "backupType = 'database-only'",
            "completeDatasetBackup = $false",
            "filesSnapshot = $null",
        ):
            require(token in writer, f"database sidecar freezes {token}")
        for field in ("logicalDataset", "effectiveDatabaseDataDir", "databaseBackupFile", "databaseBackupFormat",
                      "effectiveFilesDir", "resolvedPhysicalFilesRoot", "applicationSourceIdentity",
                      "imageRowCount", "cataloguedFileCount"):
            require(field in writer, f"sidecar manifest records {field}")
        require("Refusing restore" in verifier and "physical Files root" in verifier,
                "manifest verification rejects a restore against a different database/Files pair")
        require("No Step-7 dataset manifest exists" in verifier,
                "legacy database backups remain usable with an explicit database-only warning")

        for mode in MODES:
            texts: dict[str, str] = {}
            for op in OPS:
                path = ROOT / "scripts/windows" / mode / op
                text = path.read_text(encoding="utf-8")
                texts[op] = text
                require("validate-dataset-pair.bat" in text, f"{mode}/{op} validates the paired selectors")
                require("resolve-effective-dataset.ps1" in text, f"{mode}/{op} resolves effective dataset identity")
                require(r"data\database-backups\%DIARIES_DATASET_NAME%" in text,
                        f"{mode}/{op} uses effective-dataset backup directory")
                require("%DIARIES_EFFECTIVE_FILES_ROOT%" in text,
                        f"{mode}/{op} reports the matching physical Files root")
                require("DATABASE-ONLY" in text,
                        f"{mode}/{op} labels its operation as database-only")

                mode_env_load = text.find('load-dotenv.bat" "%ENV_FILE%"')
                local_env_load = text.find('load-dotenv.bat" "%LOCAL_ENV_FILE%"')
                require(mode_env_load >= 0 and local_env_load > mode_env_load,
                        f"{mode}/{op} loads committed mode environment before local.env")

                if op in BACKUPS:
                    require("diaries-%DIARIES_DATASET_NAME%-%TIMESTAMP%" in text,
                            f"{mode}/{op} names default backups from effective dataset identity")
                    require("write-db-backup-manifest.ps1" in text,
                            f"{mode}/{op} writes the database-only dataset sidecar")
                    require("SELECT count(*) FROM public.image;" in text,
                            f"{mode}/{op} captures Image catalogue row count")
                    require("exec -T diaries-db pg_dump" in text,
                            f"{mode}/{op} executes pg_dump in diaries-db")
                else:
                    require("verify-db-backup-manifest.ps1" in text,
                            f"{mode}/{op} checks sidecar identity before destructive restore")
                    require("NO - mutable Files bytes will not be restored" in text,
                            f"{mode}/{op} does not claim to restore a complete dataset")
                    require("Stop any responder that can access this database before continuing." in text,
                            f"{mode}/{op} freezes current manual writer-quiescence responsibility")
                    require("Type RESTORE to continue" in text,
                            f"{mode}/{op} requires explicit destructive confirmation")

            require("--format=custom" in texts["backup-db-to-binary.bat"],
                    f"{mode} binary backup remains PostgreSQL custom format")
            require("--format=plain" in texts["backup-db-to-sql.bat"],
                    f"{mode} SQL backup remains PostgreSQL plain format")
            require("pg_restore --list" in texts["restore-db-from-binary.bat"] and
                    "exec -T diaries-db pg_restore" in texts["restore-db-from-binary.bat"],
                    f"{mode} binary restore validates and restores through pg_restore in diaries-db")
            require('findstr /c:"PostgreSQL database dump"' in texts["restore-db-from-sql.bat"] and
                    "exec -T diaries-db psql" in texts["restore-db-from-sql.bat"],
                    f"{mode} SQL restore validates plain SQL then restores through psql in diaries-db")

        # Guard against accidental reintroduction of mode-labelled default patterns or
        # accidental conversion of these existing commands into complete-dataset operations.
        joined = "\n".join((ROOT / "scripts/windows" / m / o).read_text(encoding="utf-8") for m in MODES for o in OPS)
        require(not re.search(r'set "BACKUP_DIR=.*database-backups\\(?:development-infrastructure|local-docker-build|local-published-smoke)', joined),
                "no local database script selects a backup directory solely from launch mode")
        require("completeDatasetBackup = $true" not in writer and "filesSnapshot = $null" in writer,
                "existing local sidecars cannot silently become complete-dataset manifests")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: local database-only backup/restore and effective-dataset contract frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
