#!/usr/bin/env python3
"""Verify the local dataset/Files configuration contract.

This check is intentionally static and does not require Docker. It validates the
committed mode defaults, local.env example override precedence, and both Compose
mount expressions. Docker Compose's :? interpolation form is used so an omitted
DIARIES_FILES_DIR fails during Compose interpolation instead of silently using
production/shared 'files'.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]

MODE_EXPECTATIONS = {
    "development-infrastructure": (
        "./data/database/development-infrastructure",
        "files-development-infrastructure",
    ),
    "local-docker-build": (
        "./data/database/local-docker-build",
        "files-local-docker-build",
    ),
    "local-published-smoke": (
        "./data/database/local-published-smoke",
        "files-local-published-smoke",
    ),
}

COMMON_DB = "./data/database/common"
COMMON_FILES = "files-development-common"
REQUIRED_FILES_SUBPATH = (
    "${DIARIES_NAS_CONTENT_PATH}/"
    "${DIARIES_FILES_DIR:?DIARIES_FILES_DIR must be set}"
)
DIARIES_SUBPATH = "${DIARIES_NAS_CONTENT_PATH}/diaries"


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_mode_defaults() -> None:
    for mode, (expected_db, expected_files) in MODE_EXPECTATIONS.items():
        path = PROJECT / "config" / "environments" / f"{mode}.env"
        env = parse_dotenv(path)
        require(
            env.get("DIARIES_DB_DATA_DIR") == expected_db,
            f"{mode}: unexpected DIARIES_DB_DATA_DIR",
        )
        require(
            env.get("DIARIES_FILES_DIR") == expected_files,
            f"{mode}: missing/unexpected DIARIES_FILES_DIR",
        )
        print(f"PASS mode default: {mode}: {expected_db} <-> {expected_files}")


def check_common_override() -> None:
    local = parse_dotenv(PROJECT / "config" / "environments" / "local.env.example")
    require(
        local.get("DIARIES_DB_DATA_DIR") == COMMON_DB,
        "local.env.example: common database override is missing/unexpected",
    )
    require(
        local.get("DIARIES_FILES_DIR") == COMMON_FILES,
        "local.env.example: matching common Files override is missing/unexpected",
    )

    # Reproduce the documented precedence: committed mode first, local.env second.
    for mode in MODE_EXPECTATIONS:
        effective = parse_dotenv(
            PROJECT / "config" / "environments" / f"{mode}.env"
        )
        effective.update(local)
        require(
            effective.get("DIARIES_DB_DATA_DIR") == COMMON_DB,
            f"{mode}: local override did not win for database directory",
        )
        require(
            effective.get("DIARIES_FILES_DIR") == COMMON_FILES,
            f"{mode}: local override did not win for Files directory",
        )
        print(
            f"PASS common override: {mode}: "
            f"{COMMON_DB} <-> {COMMON_FILES}"
        )


def check_compose(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    require(
        REQUIRED_FILES_SUBPATH in text,
        f"{path.name}: mutable /data/files mount does not use required DIARIES_FILES_DIR",
    )
    require(
        DIARIES_SUBPATH in text,
        f"{path.name}: shared read-only diaries mount changed unexpectedly",
    )
    require(
        "subpath: ${DIARIES_NAS_CONTENT_PATH}/files" not in text,
        f"{path.name}: implicit shared mutable Files path is still present",
    )

    # Confirm the required selector belongs to the volume targeting /data/files.
    block_pattern = re.compile(
        r"target:\s*/data/files.*?subpath:\s*"
        + re.escape(REQUIRED_FILES_SUBPATH),
        re.DOTALL,
    )
    require(
        bool(block_pattern.search(text)),
        f"{path.name}: required Files selector is not attached to /data/files",
    )
    print(
        f"PASS compose: {path.name}: /data/files -> "
        f"{REQUIRED_FILES_SUBPATH}"
    )
    print(
        f"PASS compose guard: {path.name}: missing DIARIES_FILES_DIR uses Compose :? failure"
    )


def main() -> int:
    try:
        check_mode_defaults()
        check_common_override()
        check_compose(PROJECT / "compose.local-docker-build.yaml")
        check_compose(PROJECT / "compose.local-published-smoke.yaml")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: local dataset/Files configuration contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
