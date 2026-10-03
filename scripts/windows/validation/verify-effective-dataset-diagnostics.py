#!/usr/bin/env python3
"""Verify effective dataset diagnostics and stable runtime path contracts."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]


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

        compose_build = text(ROOT / "compose.local-docker-build.yaml")
        compose_smoke = text(ROOT / "compose.local-published-smoke.yaml")
        for name, source in (("local-docker-build", compose_build), ("local-published-smoke", compose_smoke)):
            require("target: /data/files" in source and
                    "${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR:?DIARIES_FILES_DIR must be set}" in source,
                    f"{name} maps the selected physical root to stable /data/files")
            require("target: /data/diaries" in source and "read_only: true" in source,
                    f"{name} retains the shared diary mount as read-only")
        require("POSTGRES_DB: ${DIARIES_DB_NAME:-diaries}" in compose_smoke and
                "POSTGRES_USER: ${DIARIES_DB_USERNAME:-diaries}" in compose_smoke and
                "POSTGRES_PASSWORD: ${DIARIES_DB_PASSWORD:-diaries}" in compose_smoke,
                "local-published-smoke uses safe local PostgreSQL defaults")

        upload = text(ROOT / "diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UploadFile.java")
        responder = text(ROOT / "diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/Responder.java")
        require('PUBLIC_FILES_CONTEXT = "/files"' in upload,
                "UploadFile keeps the public Files URL independent of the physical Files selector")
        require('String filesContextName = "/files"' in responder,
                "static responder Files context remains /files")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: effective dataset diagnostics and stable runtime paths verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
