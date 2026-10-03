#!/usr/bin/env python3
"""Static/portable verification for the local dataset-pair guard.

The exact PowerShell guard is exercised by verify-dataset-pair-guard.ps1 on Windows.
This checker verifies the committed topology, launch integration, local Compose
mounts, shared scan path and stable public /files contract without requiring a
Windows shell, Docker, NAS, PostgreSQL or MQTT.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

MODES = {
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
COMMON_PAIR = ("./data/database/common", "files-development-common")
FILES_KEY = "DIARIES_FILES_DIR"
DB_KEY = "DIARIES_DB_DATA_DIR"
FILES_SUBPATH = (
    "${DIARIES_NAS_CONTENT_PATH}/"
    "${DIARIES_FILES_DIR:?DIARIES_FILES_DIR must be set}"
)
SCAN_SUBPATH = "${DIARIES_NAS_CONTENT_PATH}/diaries"


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
    print(f"PASS: {message}")


def effective(mode: str, local: dict[str, str]) -> tuple[str, str]:
    env = parse_dotenv(ROOT / "config" / "environments" / f"{mode}.env")
    env.update(local)
    return env[DB_KEY], env[FILES_KEY]


def check_live_script_policy() -> None:
    guard = ROOT / "scripts/windows/validation/verify-live-script-policy.py"
    result = subprocess.run(
        [sys.executable, str(guard)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0 and result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    require(
        result.returncode == 0,
        "normal local guard regression includes the live-script anti-accumulation policy",
    )


def check_topology() -> None:
    isolated_pairs: list[tuple[str, str]] = []
    for mode, expected in MODES.items():
        actual = effective(mode, {})
        require(actual == expected, f"{mode} isolated default matches frozen database/Files pair")
        isolated_pairs.append(actual)

    require(len({db for db, _ in isolated_pairs}) == 3,
            "isolated defaults use three distinct database directories")
    require(len({files for _, files in isolated_pairs}) == 3,
            "isolated defaults use three distinct mutable Files directories")
    require(all(files != "files" for _, files in isolated_pairs),
            "no local isolated default selects the production Files root")

    common = parse_dotenv(ROOT / "config" / "environments" / "local.env.example")
    require((common.get(DB_KEY), common.get(FILES_KEY)) == COMMON_PAIR,
            "local.env.example contains the approved paired common override")
    common_effective = {effective(mode, common) for mode in MODES}
    require(common_effective == {COMMON_PAIR},
            "all three modes resolve the same database and Files dataset under the common override")


def check_guard_source_and_launch_integration() -> None:
    guard = (ROOT / "scripts" / "windows" / "common" / "validate-dataset-pair.ps1").read_text(encoding="utf-8")
    wrapper = (ROOT / "scripts" / "windows" / "common" / "validate-dataset-pair.bat").read_text(encoding="utf-8")

    require("$databaseOverridden -xor $filesOverridden" in guard,
            "runtime guard rejects one-sided local.env dataset overrides")
    require("DIARIES_FILES_DIR=files is reserved for the production dataset" in guard,
            "runtime guard reserves the production mutable Files root from local modes")
    for db_leaf, files in {
        "development-infrastructure": "files-development-infrastructure",
        "local-docker-build": "files-local-docker-build",
        "local-published-smoke": "files-local-published-smoke",
        "common": "files-development-common",
    }.items():
        require(f"'{db_leaf}' = '{files}'" in guard,
                f"runtime guard contains approved path pairing {db_leaf} <-> {files}")
    # PowerShell parses an unbraced variable immediately followed by ':' as a
    # scoped-variable expression (for example $env:PATH). Guard against the
    # interpolation defect found by the first Windows runtime verification.
    invalid_colon_interpolation = re.compile(
        r"\$(?!env:|global:|script:|local:|private:|using:)[A-Za-z_][A-Za-z0-9_]*:"
    )
    require(not invalid_colon_interpolation.search(guard),
            "PowerShell guard has no unbraced variable immediately followed by a colon")
    require('"Dataset override mismatch in ${LocalEnvironmentFile}:' in guard,
            "dataset-override error uses braced PowerShell interpolation before colon")
    require('"Validated Diaries dataset pair for ${ModeName}:' in guard,
            "success heading uses braced PowerShell interpolation before colon")

    require("validate-dataset-pair.ps1" in wrapper,
            "batch wrapper invokes the shared PowerShell dataset-pair guard")

    launchers = {
        "development-infrastructure start": ROOT / "scripts/windows/development-infrastructure/start.bat",
        "local-docker-build start": ROOT / "scripts/windows/local-docker-build/start.bat",
        "local-published-smoke start": ROOT / "scripts/windows/local-published-smoke/start.bat",
        "direct responder/reconciliation preparation": ROOT / "scripts/windows/development-infrastructure/prepare-responder-config.bat",
    }
    for name, path in launchers.items():
        text = path.read_text(encoding="utf-8")
        require("validate-dataset-pair.bat" in text,
                f"{name} executes the dataset-pair guard before use")

    ps_test = (ROOT / "scripts/windows/validation/verify-dataset-pair-guard.ps1").read_text(encoding="utf-8")
    for case in (
        "isolated defaults:",
        "shared common pair:",
        "reject DB-only local.env override",
        "reject Files-only local.env override",
        "reject local database with production Files root",
        "reject crossed approved local pair",
    ):
        require(case in ps_test, f"Windows regression suite covers: {case}")
    require("$ErrorActionPreference = 'Continue'" in ps_test,
            "Windows regression suite allows expected child-process failures to be captured")
    require("$caseOutput = & powershell" in ps_test and "2>&1" in ps_test,
            "Windows regression suite captures child stdout/stderr before asserting exit code")
    require("$ErrorActionPreference = $previousErrorActionPreference" in ps_test,
            "Windows regression suite restores strict ErrorActionPreference after each guard case")


def check_compose_and_public_contract() -> None:
    for filename in ("compose.local-docker-build.yaml", "compose.local-published-smoke.yaml"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        require(FILES_SUBPATH in text,
                f"{filename} mutable Files mount uses explicit DIARIES_FILES_DIR")
        require(SCAN_SUBPATH in text,
                f"{filename} shared diary scans remain under /diaries")
        require("subpath: ${DIARIES_NAS_CONTENT_PATH}/files" not in text,
                f"{filename} has no implicit production/shared mutable Files subpath")
        pattern = re.compile(r"target:\s*/data/files.*?subpath:\s*" + re.escape(FILES_SUBPATH), re.S)
        require(bool(pattern.search(text)), f"{filename} binds the selected root specifically to /data/files")

    upload = (ROOT / "diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UploadFile.java").read_text(encoding="utf-8")
    upload_test = (ROOT / "diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/UploadStagingTest.java").read_text(encoding="utf-8")
    require('private static final String PUBLIC_FILES_CONTEXT = "/files";' in upload,
            "public file URL remains rooted at /files independently of physical storage")
    require("publicUrlAndPersistedPathDoNotExposePhysicalFilesDirectory" in upload_test,
            "responder regression test protects stable public URL and environment-neutral relativePath")


def main() -> int:
    try:
        check_live_script_policy()
        check_topology()
        check_guard_source_and_launch_integration()
        check_compose_and_public_contract()
    except (AssertionError, OSError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: local dataset-pair regression guard contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
