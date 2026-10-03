#!/usr/bin/env python3
"""Portable source verification for 0031-FEAT Step 9 local reconciliation tooling."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
STEP9 = ROOT / "scripts/windows/0031-step9"
FEATURE = ROOT / "change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment"

def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")

def main() -> int:
    try:
        script = (STEP9 / "reconcile-local-shared-files.ps1").read_text(encoding="utf-8")
        readme = (STEP9 / "README.md").read_text(encoding="utf-8")
        implementation = (FEATURE / "IMPLEMENTATION-STEPS.md").read_text(encoding="utf-8")
        require("diaries-local-responder" in script and "diaries-published-smoke-responder" in script,
                "Step 9 preserves the local responder write freeze")
        require("GetActiveTcpListeners()" in script and "TCP/8081 is listening" in script,
                "Step 9 rejects a running direct Windows responder")
        for container in ("diaries-development-db", "diaries-local-db", "diaries-published-smoke-db"):
            require(container in script, f"Step 9 can identify local database mode {container}")
        require("Exactly one local Diaries database container must be running" in script,
                "Step 9 refuses ambiguous concurrent local database datasets")
        require("prepare-responder-config.bat" in script and "responder.effective.json" in script,
                "Step 9 starts from the Step 4 generated/effective responder configuration")
        require("-FilesDir $SharedFilesDir" in script and "$SharedFilesDir -ne 'files'" in script,
                "Step 9 uses a temporary pre-split Files override without changing normal configuration")
        require("-PmigrationMode=dry-run" in script and "migration0024ImageCatalogue" in script,
                "Step 9 invokes the existing 0024 reconciliation in dry-run mode")
        require("-PmigrationMode=apply" not in script and "migrationMode=apply" not in script,
                "Step 9 local tooling contains no apply path")
        require("STAGING-INVENTORY.tsv" in script and "Get-FileHash" in script,
                "Step 9 separately inventories and hashes .image-staging recovery content")
        for field in ("imageRowCount", "matchingPhysicalFiles", "missingPhysicalFiles",
                      "untrackedPhysicalFiles", "untrackedSupportedImageFiles", "metadataOrChecksumConflicts",
                      "requiresExplicitDisposition", "step10Ready"):
            require(field in script, f"Step 9 report records {field}")
        require("If `local.env` selects `./data/database/common`" in readme,
                "documentation treats the three normal local modes as one effective dataset")
        require("## Step 9 — Reconcile each independent effective database against the existing shared Files tree" in implementation,
                "Step 9 contract remains present in the implementation plan")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: 0031-FEAT Step 9 local reconciliation tooling verified")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
