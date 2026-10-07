#!/usr/bin/env python3
"""Permanent Step-5 regression for local complete-dataset restore preparation."""
from __future__ import annotations

import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
COMMON = ROOT / "scripts" / "windows" / "common"
RESTORE = COMMON / "restore-dataset.ps1"
MANIFEST = COMMON / "complete-dataset-manifest.py"
VERIFY = COMMON / "complete-dataset-verification.py"
STAGE = COMMON / "complete-dataset-restore-stage.py"
MODES = ("development-infrastructure", "local-docker-build", "local-published-smoke")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(*args: str, ok: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(args, text=True, capture_output=True)
    if ok and cp.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
    if not ok and cp.returncode == 0:
        raise AssertionError(f"command unexpectedly succeeded: {' '.join(args)}")
    return cp


def build_synthetic_backup(root: Path) -> Path:
    backup = root / "20261007-120000Z"
    source = root / "source-files"
    (backup / "database").mkdir(parents=True)
    (backup / "files" / "nested").mkdir(parents=True)
    (source / "nested").mkdir(parents=True)
    (backup / "database" / "diaries.dump").write_bytes(b"synthetic custom archive bytes\n")
    sql = "--\n-- PostgreSQL database dump\n--\nCREATE TABLE example(id integer);\n--\n-- PostgreSQL database dump complete\n--\n"
    (backup / "database" / "diaries.sql").write_text(sql, encoding="utf-8")
    files = {"one.txt": b"one\n", "nested/two.bin": b"two-two\n"}
    for rel, data in files.items():
        (backup / "files" / rel).parent.mkdir(parents=True, exist_ok=True)
        (source / rel).parent.mkdir(parents=True, exist_ok=True)
        (backup / "files" / rel).write_bytes(data)
        (source / rel).write_bytes(data)

    run(sys.executable, str(VERIFY), "--backup-dir", str(backup), "--source-files-root", str(source))
    identity = base64.b64encode(json.dumps({"gitCommit": "synthetic"}).encode()).decode()
    run(
        sys.executable,
        str(MANIFEST),
        "write",
        "--backup-dir", str(backup),
        "--logical-dataset", "common",
        "--launch-mode", "local-docker-build",
        "--known-consumer", "development-infrastructure",
        "--known-consumer", "local-docker-build",
        "--known-consumer", "local-published-smoke",
        "--database-storage-identity", "C:/example/data/database/common",
        "--database-name", "diaries",
        "--files-selector", "files-development-common",
        "--files-root", "//nas/example/files-development-common",
        "--application-identity-base64", identity,
        "--writer-method", "synthetic",
        "--writer", "diaries-responder",
        "--writer-evidence", "synthetic stopped writer",
        "--image-row-count", "2",
        "--catalogued-file-count", "2",
        "--staging-disposition", "empty",
        "--staging-entry-count", "0",
        "--staging-note", "synthetic empty staging",
        "--started-at", "2026-10-07T11:59:00+00:00",
        "--completed-at", "2026-10-07T12:00:00+00:00",
    )
    run(sys.executable, str(MANIFEST), "verify", "--backup-dir", str(backup))
    return backup


def main() -> int:
    text = RESTORE.read_text(encoding="utf-8")
    required_fragments = (
        "Invoke-DatasetPairValidation",
        "complete-dataset-manifest.py",
        "'verify','--backup-dir'",
        "Assert-ManifestMatchesTarget",
        "DATABASE-ONLY dump/SQL/.dataset.json inputs are not accepted",
        "pg_restore','--list'",
        "Get-StagingInspection",
        "Read-Host 'Type RESTORE",
        "Stop-Writers",
        "backup-dataset.ps1",
        "Creating mandatory pre-restore COMPLETE DATASET safety backup",
        "$backupOutput = & powershell.exe",
        "foreach ($line in @($backupOutput)) { Write-Host ([string]$line) }",
        "$safetyBackupPath = Join-Path",
        "Invoke-SafetyBackup -SafetyBackupId $safetyBackupId",
        "Copy-BackupFilesToStage",
        "complete-dataset-restore-stage.py",
        "prepared-awaiting-step6",
        "Live database:         UNCHANGED",
        "Live Files root:       UNCHANGED",
        "Writers remain intentionally stopped",
    )
    for fragment in required_fragments:
        require(fragment in text, f"restore engine is missing required Step-5 contract fragment: {fragment}")

    # The safety-backup path must be derived independently. Child-command stdout is
    # console evidence, not return data that can contaminate restore-state.json.
    require("$safetyBackupPath = Invoke-SafetyBackup" not in text, "safety-backup path must not capture nested backup stdout")

    # Step 5 and Step 6 now share one permanent engine. Protect the Step-5 branch
    # itself from crossing the destructive boundary rather than forbidding Step-6
    # mechanics elsewhere in the same file.
    step5_start = text.index("    $currentDurableBytes = Get-DurableTargetBytes")
    step5_end = text.index("catch {", step5_start)
    step5_branch = text[step5_start:step5_end]
    for forbidden in ("Invoke-DatabaseRestoreFromCompleteBackup", "Invoke-FilesApplySwap", "dropdb", "createdb"):
        require(forbidden not in step5_branch, f"Step-5 preflight/prepare branch unexpectedly crosses destructive boundary: {forbidden}")
    require("Live database:         UNCHANGED" in step5_branch and "Live Files root:       UNCHANGED" in step5_branch,
            "Step-5 branch must continue to declare the non-destructive hand-off boundary")

    for mode in MODES:
        wrapper = ROOT / "scripts" / "windows" / mode / "restore-dataset.bat"
        require(wrapper.is_file(), f"missing thin restore wrapper for {mode}")
        wrapper_text = wrapper.read_text(encoding="utf-8")
        require(f'-ModeName "{mode}"' in wrapper_text, f"{mode} wrapper does not select its mode")
        require("-PreflightOnly" in wrapper_text and "-PrepareOnly" in wrapper_text, f"{mode} wrapper must expose preflight and prepare")
        require("restore-dataset.ps1" in wrapper_text, f"{mode} wrapper must delegate to common restore engine")

    with tempfile.TemporaryDirectory(prefix="diaries-0033-step5-") as td:
        root = Path(td)
        backup = build_synthetic_backup(root)
        stage = root / "staged"
        shutil.copytree(backup / "files", stage)

        passed = run(sys.executable, str(STAGE), "--backup-dir", str(backup), "--staged-files-root", str(stage))
        require("exact paths/sizes/SHA-256" in passed.stdout, "staged Files verifier did not report exact inventory verification")

        (stage / "one.txt").write_text("changed\n", encoding="utf-8")
        run(sys.executable, str(STAGE), "--backup-dir", str(backup), "--staged-files-root", str(stage), ok=False)
        shutil.copy2(backup / "files" / "one.txt", stage / "one.txt")
        (stage / "extra.txt").write_text("extra\n", encoding="utf-8")
        run(sys.executable, str(STAGE), "--backup-dir", str(backup), "--staged-files-root", str(stage), ok=False)
        (stage / "extra.txt").unlink()
        (stage / "nested" / "two.bin").unlink()
        run(sys.executable, str(STAGE), "--backup-dir", str(backup), "--staged-files-root", str(stage), ok=False)
        shutil.copy2(backup / "files" / "nested" / "two.bin", stage / "nested" / "two.bin")
        (stage / ".image-staging").mkdir()
        run(sys.executable, str(STAGE), "--backup-dir", str(backup), "--staged-files-root", str(stage), ok=False)

    print("PASS: local complete-dataset Step-5 restore preparation contract verified")
    print("  wrappers: all three local modes delegate to one common restore engine")
    print("  preflight: completed schema-2 backup + target identity + pg_restore/list + staging/space/writer inspection")
    print("  safety: explicit RESTORE confirmation, writer quiescence, mandatory verified complete safety backup")
    print("  Files: sibling stage copy is independently reverified by exact paths/sizes/SHA-256; corruption/extra/missing/staging rejected")
    print("  boundary: Step 5 contains no live PostgreSQL restore or live Files-root replacement")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
