#!/usr/bin/env python3
"""Final portable Playbooks source gate for 0031-FEAT Step 16."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROLE = ROOT / "roles/diaries"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def read(relative: str) -> str:
    return (ROLE / relative).read_text(encoding="utf-8")


def main() -> int:
    try:
        env = read("templates/.env.j2")
        compose = read("templates/compose.yaml.j2")
        tasks = read("tasks/main.yaml")
        defaults = read("defaults/main.yaml")
        readme = read("README.md")
        scripts_readme = read("files/sync/scripts/README.md")

        require("DIARIES_FILES_DIR={{ diaries_files_dir }}" in env,
                "production .env renders the explicit diaries_files_dir selector")
        require("${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}" in compose and "target: /data/files" in compose,
                "production responder mounts the explicit selector at stable /data/files")
        require("${DIARIES_NAS_CONTENT_PATH}/diaries" in compose and "target: /data/diaries" in compose and "read_only: true" in compose,
                "production keeps the original diary scan tree shared/read-only")
        require("subpath: ${DIARIES_NAS_CONTENT_PATH}/files\n" not in compose,
                "production Compose template contains no implicit hard-coded mutable files subpath")
        require("diaries_files_dir is defined" in tasks and "leaf directory" in tasks and "explicitly supplied" in tasks,
                "Ansible fails fast when the production Files selector is missing/invalid")
        require("diaries_files_dir:" not in defaults,
                "production Files selector has no unsafe role default")
        require("one effective database dataset <-> one effective mutable Files root" in readme,
                "role documentation records the durable database/Files pairing invariant")
        require("database-only" in readme.lower() and "matching Files snapshot" in readme,
                "role documentation defines complete matched backup/restore semantics")
        require("database-only" in scripts_readme.lower() and "reconciliation" in scripts_readme.lower(),
                "installed production operating notes warn about database-only restore/reconciliation")

        step14 = read("tests/verify-0031-step14.py")
        storage = read("tests/verify-0031-storage-isolation.py")
        require("max_queued_messages 0" in step14,
                "Step 14 production validation still protects the deployed retained-snapshot policy")
        require("DIARIES_FILES_DIR" in storage and "/data/files" in storage,
                "production storage-isolation regression remains present")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: 0031-FEAT Step 16 final Playbooks source gate verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
