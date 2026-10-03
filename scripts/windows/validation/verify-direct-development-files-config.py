#!/usr/bin/env python3
"""Static source verification for direct-development Files configuration.

This checker is intentionally runnable without a live NAS, PostgreSQL, MQTT,
PowerShell or Gradle installation. Runtime/unit tests remain separate evidence.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
failures = []
checks = []

def require(condition, message):
    checks.append(message)
    if not condition:
        failures.append(message)

def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

helper_bat = text("scripts/windows/development-infrastructure/prepare-responder-config.bat")
helper_ps1 = text("scripts/windows/development-infrastructure/prepare-responder-config.ps1")
run_bat = text("diaries-responder/scripts/windows/run-responder.bat")
migration_bat = text("diaries-responder/scripts/windows/migration0024ImageCatalogue.bat")
start_bat = text("scripts/windows/development-infrastructure/start.bat")
status_bat = text("scripts/windows/development-infrastructure/status.bat")
runtime_bat = text("scripts/windows/validation/verify-direct-development-files-runtime.bat")
upload = text("diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UploadFile.java")
upload_test = text("diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/UploadStagingTest.java")
gitignore = text(".gitignore")

mode_pos = helper_bat.find('call "%LOAD_DOTENV%" "%ENV_FILE%"')
local_pos = helper_bat.find('call "%LOAD_DOTENV%" "%LOCAL_ENV_FILE%"')
require(mode_pos >= 0 and local_pos > mode_pos,
        "helper loads development-infrastructure.env before local.env")
require("if not defined DIARIES_DB_DATA_DIR" in helper_bat,
        "helper requires DIARIES_DB_DATA_DIR")
require("if not defined DIARIES_FILES_DIR" in helper_bat,
        "helper requires DIARIES_FILES_DIR")
require("%USERPROFILE%\\.diaries\\responder.json" in helper_bat,
        "developer responder.json remains the default base")
require("set \"GENERATED_DIR=%PROJECT_DIR%\\build\\development-infrastructure\"" in helper_bat and
        "set \"GENERATED_CONFIG=%GENERATED_DIR%\\responder.effective.json\"" in helper_bat,
        "effective responder config is generated beneath ignored build/")
require(any(line.strip() == "build/" for line in gitignore.splitlines()),
        "root build/ directory is git-ignored")
require("$config.diaries.files = $FilesDir" in helper_ps1,
        "PowerShell generator replaces diaries.files")
require("ConvertFrom-Json" in helper_ps1 and "ConvertTo-Json" in helper_ps1,
        "PowerShell generator preserves the base JSON object while rewriting the copy")
require("password" not in "\n".join(line.lower() for line in helper_bat.splitlines() if line.lower().startswith("echo")),
        "helper diagnostics do not echo password fields")

shared_helper = "scripts\\windows\\development-infrastructure\\prepare-responder-config.bat"
require(shared_helper.lower() in run_bat.lower(),
        "run-responder.bat uses the shared effective-config helper")
require(shared_helper.lower() in migration_bat.lower(),
        "migration0024ImageCatalogue.bat uses the same helper")
require("-PmigrationConfig=%CONFIG%" in migration_bat,
        "Image reconciliation passes the generated effective config to Gradle")
require("DIARIES_EFFECTIVE_RESPONDER_CONFIG" in run_bat and
        'call "%LAUNCHER%" --config "%CONFIG_FILE%"' in run_bat,
        "direct responder runs with the generated effective config")

require(shared_helper.lower() in runtime_bat.lower(),
        "runtime verifier uses the same effective-config helper")
require("UploadStagingTest.publicUrlAndPersistedPathDoNotExposePhysicalFilesDirectory" in runtime_bat,
        "runtime verifier executes the non-default Files URL regression test")
require("^|" not in runtime_bat and "-Raw | ConvertFrom-Json" in runtime_bat,
        "runtime verifier passes the PowerShell pipeline without a literal CMD caret")

for name, script in (("start", start_bat), ("status", status_bat)):
    require("if not defined DIARIES_DB_DATA_DIR" in script and
            "if not defined DIARIES_FILES_DIR" in script,
            f"development-infrastructure {name}.bat validates both dataset selectors")

require('private static final String PUBLIC_FILES_CONTEXT = "/files";' in upload,
        "UploadFile defines a stable public /files context")
require('PUBLIC_FILES_CONTEXT + "/" + upload.relativePath()' in upload,
        "UploadFile URL no longer derives from the physical files directory")
require('String physicalFilesDirectory = "files-development-common";' in upload_test,
        "responder regression test uses a non-default physical Files directory")
require('assertEquals("/files/image.txt", payload.url());' in upload_test,
        "regression test requires stable /files upload URL")
require('assertEquals("image.txt", rows.values().iterator().next().getRelativePath());' in upload_test,
        "regression test requires environment-neutral persisted Image.relativePath")

print("Direct-development Files configuration static verification")
for item in checks:
    state = "PASS" if item not in failures else "FAIL"
    print(f"{state}: {item}")

if failures:
    print(f"\nFAILED: {len(failures)} check(s)", file=sys.stderr)
    sys.exit(1)
print(f"\nPASS: {len(checks)} checks")
