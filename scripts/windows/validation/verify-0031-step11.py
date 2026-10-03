#!/usr/bin/env python3
"""Portable source verification for 0031-FEAT Step 11 runtime-path tooling."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment"
STEP11 = ROOT / "scripts/windows/0031-step11"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    try:
        reporter = text(ROOT / "scripts/windows/common/report-effective-dataset.bat")
        require("DIARIES_DB_DATA_DIR" in reporter and "DIARIES_FILES_DIR" in reporter,
                "common diagnostics report both halves of the durable dataset pair")
        require("Docker Files path: /data/files" in reporter,
                "Docker diagnostics keep the responder runtime Files path stable at /data/files")
        require("%DIARIES_NAS_CONTENT_PATH%/%DIARIES_FILES_DIR%" in reporter,
                "Docker diagnostics show the selected NAS Files subpath")
        require("%DIARIES_NAS_CONTENT_PATH%/diaries" in reporter and "read-only" in reporter,
                "Docker diagnostics retain the shared read-only diary subpath")

        for mode in ("development-infrastructure", "local-docker-build", "local-published-smoke"):
            base = ROOT / "scripts/windows" / mode
            for command in ("start.bat", "status.bat"):
                source = text(base / command)
                require("report-effective-dataset.bat" in source,
                        f"{mode} {command} prints effective database/Files diagnostics")
            status = text(base / "status.bat")
            require("validate-dataset-pair.bat" in status,
                    f"{mode} status path enforces the same database/Files pair guard as startup")

        wrapper = text(STEP11 / "capture-local-mode.bat")
        collector = text(STEP11 / "capture-local-mode.ps1")
        comparer = text(STEP11 / "compare-local-mode-evidence.ps1")
        readme = text(STEP11 / "README.md")

        require("validate-dataset-pair.bat" in wrapper,
                "Step 11 capture validates the dataset pair before evidence collection")
        require("-ProductionWriteFreezeConfirmed" in wrapper,
                "Step 11 capture requires explicit confirmation that the production write freeze remains active")
        require("local-docker-build" in collector and "local-published-smoke" in collector and "development-infrastructure" in collector,
                "Step 11 collector covers all three local runtime modes")
        require("config', '--format', 'json'" in collector,
                "Docker modes capture fully resolved Compose configuration")
        require("target -eq '/var/lib/postgresql'" in collector and
                "rendered Compose database mount matches the effective database data directory" in collector,
                "resolved Compose evidence verifies the database mount after overrides")
        require("COMPOSE-RENDERED-REDACTED.json" in collector and "Convert-ToRedactedValue" in collector,
                "rendered Compose evidence is redacted before it is persisted")
        require("RESPONDER-EFFECTIVE-REDACTED.json" in collector,
                "direct-development generated responder configuration is persisted only in redacted form")
        require("function Redact-Text" in collector and "Redact-Text $logs.Stdout" in collector,
                "responder/runtime text evidence is scrubbed for configured secrets before persistence")
        require("Destination -eq '/data/files'" in collector and "Destination -eq '/data/diaries'" in collector,
                "runtime mount inspection checks /data/files and /data/diaries")
        require("SELECT relative_path FROM public.image ORDER BY id LIMIT 1" in collector,
                "database verification is a read-only SELECT")
        require("-Method Head" in collector and "publicFilesContext = '/files'" in collector,
                "static verification uses HTTP HEAD and keeps the public /files route stable")
        require("Get-ChildItem" in collector and "find /data/files -type f" in collector,
                "Files verification includes non-destructive list checks")
        require("docker', '-Arguments @(\n            'logs'" in collector or "'logs', '--tail'" in collector,
                "Docker runtime capture includes responder logs")
        require("files-development-common" in comparer,
                "cross-mode comparison recognises the intended common local Files root")
        require("effectiveDatabaseDataDir" in comparer and "Select-Object -Unique" in comparer,
                "cross-mode comparison verifies common override database identity")
        require("publicFilesContext" in comparer and "responderLogCaptured" in comparer,
                "cross-mode comparison requires stable public route and responder logs")
        for name, script in (("capture-local-mode.ps1", collector), ("compare-local-mode-evidence.ps1", comparer)):
            require(script.isascii(),
                    f"{name} remains ASCII-only for Windows PowerShell 5.1 BOM-less source compatibility")

        prohibited = (
            r"\bRemove-Item\b",
            r"\bMove-Item\b",
            r"\bRename-Item\b",
            r"\bDELETE\s+FROM\b",
            r"\bINSERT\s+INTO\b",
            r"\bUPDATE\s+public\.",
            r"\bdocker\s+exec\b.*\brm\b",
        )
        for pattern in prohibited:
            require(re.search(pattern, collector, re.IGNORECASE | re.DOTALL) is None,
                    f"collector contains no mutating operation matching {pattern}")

        compose_build = text(ROOT / "compose.local-docker-build.yaml")
        compose_smoke = text(ROOT / "compose.local-published-smoke.yaml")
        for name, source in (("local-docker-build", compose_build), ("local-published-smoke", compose_smoke)):
            require("target: /data/files" in source and "${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR:?DIARIES_FILES_DIR must be set}" in source,
                    f"{name} still maps the selected physical root to stable /data/files")
            require("target: /data/diaries" in source and "read_only: true" in source,
                    f"{name} retains the shared diary mount as read-only")
        require("POSTGRES_DB: ${DIARIES_DB_NAME:-diaries}" in compose_smoke and
                "POSTGRES_USER: ${DIARIES_DB_USERNAME:-diaries}" in compose_smoke and
                "POSTGRES_PASSWORD: ${DIARIES_DB_PASSWORD:-diaries}" in compose_smoke,
                "local-published-smoke uses the same safe local PostgreSQL defaults as the other local modes")

        upload = text(ROOT / "diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UploadFile.java")
        responder = text(ROOT / "diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/Responder.java")
        require('PUBLIC_FILES_CONTEXT = "/files"' in upload,
                "UploadFile keeps the public Files URL independent of the physical Files selector")
        require('String filesContextName = "/files"' in responder,
                "static responder Files context remains /files")

        implementation = text(FEATURE / "IMPLEMENTATION-STEPS.md")
        require("## Step 11 — Repoint local modes and verify resolved runtime paths after overrides" in implementation,
                "Step 11 contract remains present in the implementation plan")
        require("**Complete — 2026-10-02.**" in implementation and
                "STEP11-RUNTIME-SUMMARY.json" in implementation,
                "implementation plan records the reviewed Step 11 runtime completion")
        require("production must remain" in readme.lower() and "write freeze" in readme.lower(),
                "Step 11 runbook keeps production frozen during the local cut-over checks")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: 0031-FEAT Step 11 source/runtime-path tooling verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
