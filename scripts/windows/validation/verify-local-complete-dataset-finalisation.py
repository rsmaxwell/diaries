#!/usr/bin/env python3
"""Focused regression for local complete-dataset verification/finalisation semantics."""
from __future__ import annotations

import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
ENGINE = ROOT / "scripts/windows/common/backup-dataset.ps1"
VERIFY_TOOL = ROOT / "scripts/windows/common/complete-dataset-verification.py"
MANIFEST_TOOL = ROOT / "scripts/windows/common/complete-dataset-manifest.py"
MODES = ("development-infrastructure", "local-docker-build", "local-published-smoke")
BACKUP_ID = "20261007-105033Z"
failures = 0


def check(condition: bool, message: str) -> None:
    global failures
    if condition:
        print(f"PASS: {message}")
    else:
        failures += 1
        print(f"FAIL: {message}")


def run(tool: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(tool), *args], text=True, capture_output=True)


def make_fixture(base: Path) -> tuple[Path, Path]:
    partial = base / f".{BACKUP_ID}.partial"
    source = base / "source-files"
    (partial / "database").mkdir(parents=True)
    (partial / "files/nested").mkdir(parents=True)
    (source / "nested").mkdir(parents=True)
    (source / ".image-staging").mkdir(parents=True)
    (source / ".image-staging/catalogue.lock").write_bytes(b"")
    (partial / "database/diaries.dump").write_bytes(b"PGDMP synthetic custom archive for Step-4 helper tests\n")
    (partial / "database/diaries.sql").write_text(
        "--\n-- PostgreSQL database dump\n--\nSELECT 1;\n--\n-- PostgreSQL database dump complete\n--\n",
        encoding="utf-8",
    )
    files = {"a.txt": b"alpha\n", "nested/b.bin": bytes(range(64))}
    for rel, payload in files.items():
        (partial / "files" / rel).write_bytes(payload)
        (source / rel).write_bytes(payload)
    return partial, source


def write_manifest(partial: Path) -> subprocess.CompletedProcess[str]:
    return run(
        MANIFEST_TOOL,
        "write", "--backup-dir", str(partial),
        "--logical-dataset", "common",
        "--launch-mode", "development-infrastructure",
        "--known-consumer", "development-infrastructure",
        "--known-consumer", "local-docker-build",
        "--known-consumer", "local-published-smoke",
        "--database-storage-identity", "./data/database/common",
        "--database-name", "diaries",
        "--files-selector", "files-development-common",
        "--files-root", "//nas/photo/content/files-development-common",
        "--application-identity-json", '{"gitCommit":"synthetic-step4"}',
        "--writer-method", "synthetic quiescence",
        "--writer", "windows:direct-diaries-responder wasRunning=False",
        "--writer-evidence", "synthetic writer state",
        "--image-row-count", "85",
        "--catalogued-file-count", "85",
        "--staging-disposition", "excluded-benign",
        "--staging-entry-count", "1",
        "--staging-note", "expected zero-byte catalogue.lock excluded",
        "--started-at", "2026-10-07T10:50:33+00:00",
        "--completed-at", "2026-10-07T10:55:00+00:00",
    )


def main() -> int:
    text = ENGINE.read_text(encoding="utf-8")
    finaliser = text[text.index("function Invoke-CompleteBackupFinalisation"):text.index("function Get-GitCommit")]
    check("pg_restore', '--list'" in text and "Test-CustomDumpWithPgRestore" in finaliser,
          "custom PostgreSQL dump is structurally validated with pg_restore --list")
    check("complete-dataset-verification.py" in finaliser,
          "finalisation prepares SHA-256 and exact Files/source verification through the permanent common helper")
    check("complete-dataset-manifest.py" in finaliser and "'write', '--backup-dir'" in finaliser,
          "schema-2 manifest is generated only during Step-4 finalisation")
    check("--allow-partial-workspace" in finaliser,
          "schema-2 manifest validator verifies the candidate before promotion")
    check("[System.IO.Directory]::Move($Workspace, $FinalBackup)" in finaliser,
          "verified candidates are promoted by same-parent directory rename")
    check("[System.IO.Directory]::Move($FinalBackup, $Workspace)" in finaliser,
          "a failed post-promotion validation is demoted back to the non-restorable partial name")
    check(finaliser.index("--allow-partial-workspace") < finaliser.index("[System.IO.Directory]::Move($Workspace, $FinalBackup)") < finaliser.index("Restore-PriorWriterState"),
          "writer state is restored only after candidate validation and atomic promotion")
    check("Wait-ForWriterStop" in finaliser and finaliser.count("Wait-ForWriterStop") >= 2,
          "writer quiescence is re-proved during verification and immediately before promotion")
    check("finalisation-failed-incomplete" in text and "complete-writer-restore-failed" in finaliser,
          "verification failures remain incomplete while post-promotion writer-restart failures preserve a valid backup")
    check("FinaliseBackupId" in text and "Assert-CaptureStateMatchesCurrentDataset" in text,
          "an existing Step-3 partial capture can be safely finalised only against the same effective dataset")
    check("proceeding directly to Step 4 verification/finalisation" in text,
          "normal backup command now captures and finalises in one operation")
    check("COMPLETE DATASET BACKUP COMPLETE." in finaliser and "Operation:           COMPLETE DATASET backup" in finaliser,
          "successful finalisation reports the required complete-backup operator summary")
    check("--application-identity-base64" in finaliser and "ToBase64String" in finaliser,
          "PowerShell passes application identity through Windows-safe Base64 rather than quote-sensitive raw JSON")
    check("--application-identity-json" not in finaliser,
          "Step-4 PowerShell no longer sends raw JSON through the Windows native-command argument boundary")

    for mode in MODES:
        wrapper = (ROOT / f"scripts/windows/{mode}/backup-dataset.bat").read_text(encoding="utf-8")
        check("finalise YYYYMMDD-HHmmssZ" in wrapper and "-FinaliseBackupId %~2" in wrapper,
              f"{mode} wrapper can finalise an existing Step-3 candidate without recapture")
        check(len(wrapper.splitlines()) < 45, f"{mode} wrapper remains thin after Step 4")

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        partial, source = make_fixture(base)
        prepared = run(VERIFY_TOOL, "--backup-dir", str(partial), "--source-files-root", str(source))
        check(prepared.returncode == 0 and "Source match:  exact" in prepared.stdout,
              "verification helper generates artifacts only when captured Files exactly match the quiesced source")
        inv = json.loads((partial / "verification/inventory.json").read_text(encoding="utf-8"))
        check(inv["fileCount"] == 2 and inv["totalBytes"] == 70,
              "verification inventory records complete file count and byte total")
        check((partial / "verification/database.sha256").is_file() and (partial / "verification/files.sha256").is_file(),
              "verification helper writes both required SHA-256 lists")

        # A changed/extra source durable file must prevent finalisation.
        (source / "extra.txt").write_text("unexpected\n", encoding="utf-8")
        mismatch = run(VERIFY_TOOL, "--backup-dir", str(partial), "--source-files-root", str(source))
        check(mismatch.returncode != 0 and "does not exactly match" in mismatch.stderr,
              "source/snapshot path-size-hash drift is rejected")
        (source / "extra.txt").unlink()
        prepared = run(VERIFY_TOOL, "--backup-dir", str(partial), "--source-files-root", str(source))
        check(prepared.returncode == 0, "candidate returns to verifiable state after controlled mismatch is removed")

        sql = partial / "database/diaries.sql"
        sql_original = sql.read_bytes()
        sql.write_text("SELECT 1;\n", encoding="utf-8")
        bad_sql = run(VERIFY_TOOL, "--backup-dir", str(partial), "--source-files-root", str(source))
        check(bad_sql.returncode != 0 and "pg_dump header" in bad_sql.stderr,
              "plain SQL dump without pg_dump readability markers is rejected")
        sql.write_bytes(sql_original)
        check(run(VERIFY_TOOL, "--backup-dir", str(partial), "--source-files-root", str(source)).returncode == 0,
              "SQL dump readability succeeds again after restoring valid fixture")

        manifest = write_manifest(partial)
        check(manifest.returncode == 0, "verified candidate can generate the schema-2 manifest")
        normal_partial = run(MANIFEST_TOOL, "verify", "--backup-dir", str(partial))
        check(normal_partial.returncode != 0 and "non-restorable" in normal_partial.stderr,
              "partial candidate cannot be selected as a normal complete backup")
        candidate = run(MANIFEST_TOOL, "verify", "--backup-dir", str(partial), "--allow-partial-workspace")
        check(candidate.returncode == 0, "fully verified partial candidate passes only the explicit finalisation validator mode")

        final = base / BACKUP_ID
        partial.rename(final)
        check(run(MANIFEST_TOOL, "verify", "--backup-dir", str(final)).returncode == 0,
              "same-filesystem promotion produces a normally valid complete backup")
        victim = final / "files/a.txt"
        original = victim.read_bytes()
        victim.write_bytes(original + b"corrupt")
        corrupt = run(MANIFEST_TOOL, "verify", "--backup-dir", str(final))
        check(corrupt.returncode != 0 and "inventory" in corrupt.stderr.lower(),
              "post-promotion byte corruption is rejected by independent manifest validation")
        victim.write_bytes(original)
        check(run(MANIFEST_TOOL, "verify", "--backup-dir", str(final)).returncode == 0,
              "completed fixture is independently verifiable after controlled corruption is removed")

    if failures:
        print(f"FAIL: {failures} Step-4 regression check(s) failed", file=sys.stderr)
        return 1
    print("PASS: local complete-dataset Step-4 finalisation contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
