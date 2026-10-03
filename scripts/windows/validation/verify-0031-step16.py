#!/usr/bin/env python3
"""Portable source/contract verification for 0031-FEAT Step 16.

This is the final static gate for the Diaries repository. Runtime proof remains
separate: run-final-regression.bat and rehearse-common-restore.bat.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment"

MODES = {
    "development-infrastructure": ("./data/database/development-infrastructure", "files-development-infrastructure"),
    "local-docker-build": ("./data/database/local-docker-build", "files-local-docker-build"),
    "local-published-smoke": ("./data/database/local-published-smoke", "files-local-published-smoke"),
}
COMMON = ("./data/database/common", "files-development-common")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def dotenv(relative: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text(relative).splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def main() -> int:
    try:
        example = dotenv("config/environments/local.env.example")
        require(example.get("DIARIES_DB_DATA_DIR") == COMMON[0] and example.get("DIARIES_FILES_DIR") == COMMON[1],
                "local.env.example selects the approved common database/Files pair")

        for mode, expected in MODES.items():
            env = dotenv(f"config/environments/{mode}.env")
            require((env.get("DIARIES_DB_DATA_DIR"), env.get("DIARIES_FILES_DIR")) == expected,
                    f"{mode} retains its independent committed database/Files defaults")
            effective = dict(env)
            effective.update(example)
            require((effective.get("DIARIES_DB_DATA_DIR"), effective.get("DIARIES_FILES_DIR")) == COMMON,
                    f"{mode} resolves the paired common override when local.env is applied second")

        validator = text("scripts/windows/common/validate-dataset-pair.ps1")
        require("$databaseOverridden -xor $filesOverridden" in validator and
                "Dataset override mismatch" in validator,
                "one-sided database/Files overrides fail clearly")
        require("DIARIES_FILES_DIR=files is reserved for the production dataset" in validator,
                "local validation rejects the production mutable Files root")
        for db_leaf, files_leaf in (
            ("development-infrastructure", "files-development-infrastructure"),
            ("local-docker-build", "files-local-docker-build"),
            ("local-published-smoke", "files-local-published-smoke"),
            ("common", "files-development-common"),
        ):
            require(db_leaf in validator and files_leaf in validator,
                    f"pair validator contains frozen mapping {db_leaf} <-> {files_leaf}")

        required_mount = "${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR:?DIARIES_FILES_DIR must be set}"
        for compose_name in ("compose.local-docker-build.yaml", "compose.local-published-smoke.yaml"):
            compose = text(compose_name)
            require(required_mount in compose,
                    f"{compose_name} selects mutable /data/files through explicit DIARIES_FILES_DIR")
            require("${DIARIES_NAS_CONTENT_PATH}/diaries" in compose and "target: /data/diaries" in compose,
                    f"{compose_name} keeps the original diary scan tree separate")
            require("subpath: ${DIARIES_NAS_CONTENT_PATH}/files\n" not in compose,
                    f"{compose_name} does not reintroduce an implicit shared mutable files path")

        prepare_bat = text("scripts/windows/development-infrastructure/prepare-responder-config.bat")
        mode_pos = prepare_bat.find('call "%LOAD_DOTENV%" "%ENV_FILE%"')
        local_pos = prepare_bat.find('call "%LOAD_DOTENV%" "%LOCAL_ENV_FILE%"')
        require(mode_pos >= 0 and local_pos > mode_pos,
                "direct-development responder config loads mode env before local.env")
        for script in (
            "diaries-responder/scripts/windows/run-responder.bat",
            "diaries-responder/scripts/windows/migration0024ImageCatalogue.bat",
        ):
            require("prepare-responder-config.bat" in text(script),
                    f"{script} consumes the shared effective responder configuration")
        step9 = text("scripts/windows/0031-step9/reconcile-local-shared-files.ps1")
        require(r"config\environments\$mode.env" in step9 and r"config\environments\local.env" in step9 and
                "Merge-DotEnv $modeEnv $localEnv" in step9,
                "Step 9 reconciliation derives its local dataset from the selected mode + local override")
        step12 = text("scripts/windows/0031-step12/reconcile-common-pair.ps1")
        require("development-infrastructure.env" in step12 and r"config\environments\local.env" in step12 and
                "Read-EnvFile $localEnv $effective" in step12,
                "Step 12 reconciliation derives the common pair from development-infrastructure.env + local.env")

        upload = text("diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UploadFile.java")
        listing = text("diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/ListFiles.java")
        upload_test = text("diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/UploadStagingTest.java")
        require('PUBLIC_FILES_CONTEXT = "/files"' in upload and 'PUBLIC_FILES_CONTEXT + "/" + upload.relativePath()' in upload,
                "UploadFile public URL is independent of the physical Files directory")
        require('filesContext = "/files"' in listing,
                "ListFiles uses the same stable /files public contract")
        require('files-development-common' in upload_test and 'assertEquals("/files/image.txt"' in upload_test,
                "responder regression covers stable /files URL with a non-default physical directory")

        backup_verifier = text("scripts/windows/common/verify-db-backup-manifest.ps1")
        require("DATABASE-ONLY restore" in backup_verifier and "matching mutable Files root" in backup_verifier,
                "database-only restore tooling warns that Files reconciliation may be required")
        for mode in MODES:
            restore = text(f"scripts/windows/{mode}/restore-db-from-binary.bat")
            require("NO - mutable Files bytes will not be restored" in restore,
                    f"{mode} binary restore never claims to restore a complete durable dataset")

        runner = text("scripts/windows/0031-step16/run-final-regression.ps1")
        rehearsal = text("scripts/windows/0031-step16/rehearse-common-restore.ps1")
        require("verify-0031-step16.py" in runner and "verify-0031-step14.py" in runner,
                "Step 16 final runner gates both Diaries and Playbooks exact candidates")
        require("local-common.env" in runner and "local-db-only.env" in runner and "one-sided-rejected" in runner,
                "Step 16 final runner explicitly tests common precedence, isolated defaults and mismatch rejection")
        require("gradlew.bat" in runner and "Arguments @('test','--console=plain')" in runner,
                "Step 16 runner executes the full Java responder/web test suite")
        require("npm" in runner and "@('run','build')" in runner,
                "Step 16 runner builds the Angular client candidate")
        require("SOURCE-SHA256SUMS-DIARIES.txt" in runner and "SOURCE-SHA256SUMS-PLAYBOOKS.txt" in runner,
                "Step 16 runner seals final cross-repository source identities")

        require("d1af825c12ea21084d6dd240af15dfb22be96ee33db6f36ad0368f0bf67afcb7" in rehearsal,
                "restore rehearsal pins the frozen Step 8 local backup checksum")
        require("postgres:18-alpine" in rehearsal and "127.0.0.1::5432" in rehearsal,
                "restore rehearsal uses a disposable localhost PostgreSQL instance")
        require("pg_restore" in rehearsal and "step8.dump" in rehearsal,
                "restore rehearsal restores the preserved Step 8 dump into the disposable database")
        require("files-development-common" in rehearsal and "migration0024ImageCatalogue" in rehearsal and "-PmigrationMode=dry-run" in rehearsal,
                "restore rehearsal reconciles the restored common database read-only against its intended Files root")
        require("ExpectedImageCount = 85" in rehearsal and "CATALOGUED_MATCH" in rehearsal and "0024-conflicts.csv" in rehearsal,
                "restore rehearsal requires the frozen 85-image catalogue to reconcile without conflicts")
        require("Remove-Item -LiteralPath $configFile" in rehearsal and "docker" in rehearsal and "'rm','-f',$container" in rehearsal,
                "restore rehearsal removes temporary config and disposable database resources")
        require("TCP/8081 is listening" in rehearsal and "local responder container" in rehearsal,
                "restore rehearsal refuses to scan while a local responder may mutate the Files root")

        for step in ("Step 8", "Step 9", "Step 10", "Step 11", "Step 12", "Step 13", "Step 14", "Step 15"):
            close = FEATURE / "evidence" / step / "CLOSE-OUT.md"
            require(close.is_file(), f"{step} close-out evidence exists for final acceptance mapping")
        step13 = (FEATURE / "evidence/Step 13/CLOSE-OUT.md").read_text(encoding="utf-8")
        step14 = (FEATURE / "evidence/Step 14/CLOSE-OUT.md").read_text(encoding="utf-8")
        require("Image 88" in step13 and "production" in step13.lower() and "unchanged" in step13.lower(),
                "Step 13 close-out preserves local common lifecycle plus production-isolation proof")
        require("healthy and non-destructive" in step14 and "DIARIES_FILES_DIR=files" in step14,
                "Step 14 close-out preserves explicit non-destructive production deployment proof")

        acceptance = (FEATURE / "evidence/Step 16/ACCEPTANCE-MATRIX.md").read_text(encoding="utf-8")
        rollback = (FEATURE / "evidence/Step 16/ROLLBACK.md").read_text(encoding="utf-8")
        require("Production and development no longer use the same physical mutable Files root" in acceptance and
                "Existing responder/client/web Image behaviour" in acceptance,
                "Step 16 acceptance matrix covers the feature README acceptance criteria")
        require("Step 8" in rollback and "never merge divergent roots automatically" in rollback.lower() and
                "DIARIES_DB_DATA_DIR" in rollback and "DIARIES_FILES_DIR" in rollback,
                "Step 16 rollback instructions preserve matched-pair recovery and no-auto-merge rules")

    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: 0031-FEAT Step 16 final Diaries source/contract gate verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
