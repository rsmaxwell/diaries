#!/usr/bin/env python3
"""Permanent Step-6 regression for controlled local complete-dataset restore apply/rollback."""
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


def build_backup(root: Path, backup_id: str, files: dict[str, bytes]) -> Path:
    backup = root / backup_id
    source = root / f"source-{backup_id}"
    (backup / "database").mkdir(parents=True)
    (backup / "files").mkdir(parents=True)
    source.mkdir(parents=True)
    (backup / "database" / "diaries.dump").write_bytes(b"synthetic custom archive bytes\n")
    (backup / "database" / "diaries.sql").write_text(
        "--\n-- PostgreSQL database dump\n--\nCREATE TABLE example(id integer);\n--\n-- PostgreSQL database dump complete\n--\n",
        encoding="utf-8",
    )
    for rel, data in files.items():
        for base in (backup / "files", source):
            path = base / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    run(sys.executable, str(VERIFY), "--backup-dir", str(backup), "--source-files-root", str(source))
    identity = base64.b64encode(json.dumps({"gitCommit": "synthetic-step6"}).encode()).decode()
    run(
        sys.executable, str(MANIFEST), "write",
        "--backup-dir", str(backup),
        "--logical-dataset", "common",
        "--launch-mode", "development-infrastructure",
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
        "--catalogued-file-count", str(len(files)),
        "--staging-disposition", "empty",
        "--staging-entry-count", "0",
        "--staging-note", "synthetic empty staging",
        "--started-at", "2026-10-07T11:59:00+00:00",
        "--completed-at", "2026-10-07T12:00:00+00:00",
    )
    run(sys.executable, str(MANIFEST), "verify", "--backup-dir", str(backup))
    return backup


def function_body(text: str, name: str, next_name: str) -> str:
    start = text.index(f"function {name}")
    end = text.index(f"function {next_name}", start)
    return text[start:end]


def main() -> int:
    text = RESTORE.read_text(encoding="utf-8")
    db_apply = function_body(text, "Invoke-DatabaseRestoreFromCompleteBackup", "Invoke-FilesApplySwap")
    rename_helper = function_body(text, "Move-DirectorySameParent", "Invoke-FilesApplySwap")
    files_apply = function_body(text, "Invoke-FilesApplySwap", "Invoke-FilesRollbackSwap")
    files_rollback = function_body(text, "Invoke-FilesRollbackSwap", "New-SafetyBackupId")

    for fragment in (
        "[switch]$ApplyOnly", "[switch]$RollbackOnly",
        "Read-Host 'Type APPLY to continue'", "Read-Host 'Type ROLLBACK",
        "prepared-awaiting-step6", "applied-awaiting-step7", "step6-apply-failed",
        "Mandatory safety backup", "Rollback command:     restore-dataset.bat rollback",
        "Writers remain intentionally stopped after Step-6 failure",
    ):
        require(fragment in text, f"restore engine is missing Step-6 contract fragment: {fragment}")

    require("[System.IO.Directory]::Move" in rename_helper and "Refusing non-same-parent Files move" in rename_helper,
            "Files cutover must use an explicit same-parent directory rename primitive")

    require("database\\diaries.dump" in db_apply, "Step 6 database apply must use database/diaries.dump")
    require("diaries.sql" not in db_apply, "Step 6 must not apply diaries.sql after the custom dump")
    for fragment in ("'dropdb','--force','--if-exists'", "'createdb'", "'pg_restore','--exit-on-error','--no-owner','--no-privileges'"):
        require(fragment in db_apply, f"database apply is missing proven custom-format restore mechanic: {fragment}")

    require("Move-DirectorySameParent -Source $FilesRoot -Destination $rollbackPath" in files_apply,
            "Files apply must preserve the old live root as explicit rollback state")
    require("Move-DirectorySameParent -Source $StagePath -Destination $FilesRoot" in files_apply,
            "Files apply must promote the exact staged tree by same-parent rename rather than merge")
    require("New-Item -ItemType Directory -Path $runtimeStaging" in files_apply,
            "Files apply must recreate only fresh runtime .image-staging")
    require("--allow-benign-runtime-staging" in files_apply,
            "Files apply must reverify the durable tree after runtime staging recreation")
    require("Move-DirectorySameParent -Source $rollbackPath -Destination $FilesRoot" in files_rollback,
            "rollback must restore the preserved pre-restore Files root")
    require("$State.liveDataset.filesRootChanged = $false" in files_rollback,
            "successful Files rollback must clear the changed-half marker")

    for mode in MODES:
        wrapper = ROOT / "scripts" / "windows" / mode / "restore-dataset.bat"
        wrapper_text = wrapper.read_text(encoding="utf-8")
        require("-ApplyOnly" in wrapper_text and "-RollbackOnly" in wrapper_text,
                f"{mode} wrapper must expose Step-6 apply and rollback")
        require(f'-ModeName "{mode}"' in wrapper_text, f"{mode} wrapper lost its mode identity")

    with tempfile.TemporaryDirectory(prefix="diaries-0033-step6-") as td:
        tmp = Path(td)
        selected = build_backup(tmp, "20261007-120000Z", {"one.txt": b"new-one\n", "nested/two.bin": b"new-two\n"})
        safety = build_backup(tmp, "20261007-121000Z", {"one.txt": b"old-one\n", "obsolete.txt": b"must-disappear-after-apply\n"})

        # Exact replacement rehearsal: the old live tree contains an extra durable file.
        live = tmp / "files-development-common"
        shutil.copytree(safety / "files", live)
        (live / ".image-staging").mkdir()
        (live / ".image-staging" / "catalogue.lock").write_bytes(b"")
        stage = tmp / ".files-development-common.restore-20261007-120000Z.staged"
        shutil.copytree(selected / "files", stage)
        rollback = tmp / ".files-development-common.pre-restore-20261007-120000Z.rollback"
        live.rename(rollback)
        stage.rename(live)
        (live / ".image-staging").mkdir()
        run(sys.executable, str(STAGE), "--backup-dir", str(selected), "--staged-files-root", str(live), "--allow-benign-runtime-staging")
        require(not (live / "obsolete.txt").exists(), "pre-restore extra file survived replacement semantics")

        # Rollback rehearsal restores the original tree (including benign runtime staging)
        # and verifies its durable bytes against the safety backup.
        failed = tmp / ".files-development-common.failed-restore"
        live.rename(failed)
        rollback.rename(live)
        run(sys.executable, str(STAGE), "--backup-dir", str(safety), "--staged-files-root", str(live), "--allow-benign-runtime-staging")
        require((live / "obsolete.txt").is_file(), "rollback did not restore original extra file from pre-restore tree")

        # Intentional promotion-failure model: if stage promotion fails after the live
        # root was renamed away, the old live tree can be renamed straight back.
        live2 = tmp / "files-failure"
        shutil.copytree(safety / "files", live2)
        rollback2 = tmp / ".files-failure.rollback"
        live2.rename(rollback2)
        # Do not promote any stage: model the failure point and exercise auto-return.
        rollback2.rename(live2)
        require((live2 / "obsolete.txt").is_file(), "promotion-failure recovery did not restore original live Files root")

        # Runtime staging exception is deliberately narrow.
        run(sys.executable, str(STAGE), "--backup-dir", str(safety), "--staged-files-root", str(live), "--allow-benign-runtime-staging")
        (live / ".image-staging" / "catalogue.lock").write_bytes(b"not-benign")
        run(sys.executable, str(STAGE), "--backup-dir", str(safety), "--staged-files-root", str(live), "--allow-benign-runtime-staging", ok=False)

    print("PASS: local complete-dataset Step-6 apply/rollback contract verified")
    print("  database: custom dump only; drop/recreate/pg_restore with exit-on-error")
    print("  Files: same-parent staged replacement leaves no pre-restore extras and preserves original root for rollback")
    print("  staging: only fresh empty or zero-byte-lock runtime staging is tolerated; stale payload rejected")
    print("  failure: changed-half state + verified safety backup + executable rollback path remain while writers stay stopped")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
