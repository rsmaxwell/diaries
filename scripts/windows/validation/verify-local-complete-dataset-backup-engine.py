#!/usr/bin/env python3
"""Static/focused regression for 0033 Step 3 local complete-dataset capture."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
ENGINE = ROOT / "scripts/windows/common/backup-dataset.ps1"
MODES = ("development-infrastructure", "local-docker-build", "local-published-smoke")

failures = 0

def check(condition: bool, message: str) -> None:
    global failures
    if condition:
        print(f"PASS: {message}")
    else:
        failures += 1
        print(f"FAIL: {message}")

def dotenv(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        result[key.strip()] = value.strip()
    return result

def effective(mode: str, local: dict[str, str]) -> tuple[str, str]:
    values = dotenv(ROOT / f"config/environments/{mode}.env")
    values.update(local)
    db = values["DIARIES_DB_DATA_DIR"].replace("\\", "/").rstrip("/")
    return db.split("/")[-1], values["DIARIES_FILES_DIR"]


def main() -> int:
    text = ENGINE.read_text(encoding="utf-8")
    check("validate-dataset-pair.ps1" in text and "Invoke-DatasetPairValidation" in text,
          "common engine invokes the existing dataset-pair validator")
    check("Read-DotEnvFile -Path $ModeEnvironmentFile" in text and
          "Read-DotEnvFile -Path $LocalEnvironmentFile" in text and
          text.index("Import-DotEnvValues -Values $modeEnv.Values") < text.index("Import-DotEnvValues -Values $localEnv.Values"),
          "mode environment is loaded before local.env")
    check("resolve-effective-dataset.ps1" in text and "DIARIES_DATASET_NAME" in text and "DIARIES_EFFECTIVE_FILES_ROOT" in text,
          "engine resolves logical dataset, effective database identity and Files root")
    check("data\\dataset-backups" in text and '\\".$BackupId.partial\\"' not in text and '".$BackupId.partial"' in text,
          "capture namespace is data/dataset-backups/<logical-dataset>/.<UTC-id>.partial")
    check("[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssZ')" in text,
          "backup IDs use the Step-2 UTC naming contract")
    check("Selected Files root is unavailable" in text and "Get-ChildItem -LiteralPath $filesRoot" in text,
          "unavailable Files roots fail before writer quiescence")
    check(".image-staging" in text and "catalogue.lock" in text and "excluded-benign" in text and
          "Only an empty directory or the expected zero-byte catalogue.lock is permitted" in text,
          "expected zero-byte catalogue.lock is accepted while unexplained .image-staging content is rejected")
    check("[int64]$entry.Length -eq 0" in text and "$entries.Count -eq 1" in text,
          "benign staging exception is limited to one zero-byte catalogue.lock entry")
    check(text.count("Get-StagingInspection -FilesRoot $filesRoot") >= 2 and
          "Close the preflight/quiescence race" in text,
          "staging is inspected before quiescence and re-inspected after all writers stop")
    check("Get-CimInstance Win32_Process" in text and "com.rsmaxwell.diaries.responder.Responder" in text,
          "direct-development responder writer state is identified")
    check("PotentialDirectWriterMains" in text and "Migration0024ImageCatalogue" in text and "Migration0022Inventory" in text,
          "known migration/maintenance Java writers cause conservative refusal")
    check("Stop-DockerResponder" in text and "Stop-Process" in text and "Wait-ForWriterStop" in text,
          "Docker and direct responders are stopped and writer quiescence is re-proved")
    check("diaries-db" in text and "The selected $ModeName diaries-db service is not running" in text,
          "selected PostgreSQL service/container is identified and must remain available")
    check("--format=$Format" in text and "database\\diaries.dump" in text and "database\\diaries.sql" in text,
          "custom and plain PostgreSQL dumps are captured into the same workspace")
    check("robocopy.exe" in text and "'/COPY:DAT'" in text and "'/DCOPY:DAT'" in text and "'/XD', $stagingPath" in text,
          "durable Files copy preserves data/attributes/timestamps and excludes staging")
    check("capture-state.json" in text and "priorWriterStateMustBeRestoredOnlyAfterSuccess" in text and
          "captured-awaiting-step4-finalisation" in text,
          "prior writer state is retained for Step-4-only restoration after successful finalisation")
    check("failed-incomplete" in text and "Any writer stopped by this operation is intentionally left stopped after failure" in text,
          "failed captures remain explicit incomplete artifacts without silently resuming writers")
    check("PREFLIGHT OK" in text and "PreflightOnly" in text,
          "non-mutating preflight mode is available")

    # Model the committed isolated defaults and the documented paired common override.
    isolated = {mode: effective(mode, {}) for mode in MODES}
    check(len(set(isolated.values())) == 3 and all(name == mode for mode, (name, _files) in isolated.items()),
          "committed local defaults resolve to three isolated dataset namespaces")
    for mode, pair in isolated.items():
        print(f"PREFLIGHT MODEL isolated {mode}: dataset={pair[0]} files={pair[1]}")

    common_override = {
        "DIARIES_DB_DATA_DIR": "./data/database/common",
        "DIARIES_FILES_DIR": "files-development-common",
    }
    common = {mode: effective(mode, common_override) for mode in MODES}
    check(set(common.values()) == {("common", "files-development-common")},
          "paired local.env common override resolves all three launch modes to one common backup namespace")
    for mode, pair in common.items():
        print(f"PREFLIGHT MODEL shared {mode}: dataset={pair[0]} files={pair[1]}")

    for mode in MODES:
        wrapper = ROOT / f"scripts/windows/{mode}/backup-dataset.bat"
        wrapper_text = wrapper.read_text(encoding="utf-8")
        check(f'-ModeName "{mode}"' in wrapper_text and "backup-dataset.ps1" in wrapper_text,
              f"{mode} has a thin wrapper over the common engine")
        check("preflight" in wrapper_text.lower() and "-PreflightOnly" in wrapper_text,
              f"{mode} wrapper exposes the non-mutating preflight command")
        check(len(wrapper_text.splitlines()) < 45,
              f"{mode} wrapper contains no duplicated backup implementation")

    # Guard the original database-only entry points: Step 3 is additive.
    for mode in MODES:
        for filename in ("backup-db-to-binary.bat", "backup-db-to-sql.bat"):
            legacy = (ROOT / f"scripts/windows/{mode}/{filename}").read_text(encoding="utf-8")
            check("Operation: DATABASE-ONLY backup" in legacy,
                  f"{mode}/{filename} remains explicitly database-only")
            check("backup-dataset.ps1" not in legacy,
                  f"{mode}/{filename} was not silently redirected to complete-dataset semantics")

    if failures:
        print(f"FAIL: {failures} Step-3 regression check(s) failed")
        return 1
    print("PASS: local complete-dataset Step-3 capture engine contract verified")
    return 0

if __name__ == "__main__":
    sys.exit(main())
