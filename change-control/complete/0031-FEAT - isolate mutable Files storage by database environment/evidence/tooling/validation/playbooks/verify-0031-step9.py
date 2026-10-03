#!/usr/bin/env python3
"""Portable source verification for 0031-FEAT Step 9 production reconciliation tooling."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "roles/diaries/files/sync/scripts"

def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")

def main() -> int:
    try:
        script = (SCRIPTS / "step9-reconcile-production.sh").read_text(encoding="utf-8")
        readme = (SCRIPTS / "README.md").read_text(encoding="utf-8")
        require("Production responder" in script and "Step 8 write freeze" in script,
                "production Step 9 refuses to run with responder writes enabled")
        require("database service" in script and "is not running" in script,
                "production Step 9 requires PostgreSQL to remain available")
        require("FILES_DIR" in script and '== "files"' in script,
                "production Step 9 is pinned to the frozen pre-split files selector")
        require("Migration0024ImageCatalogue" in script and "--mode dry-run" in script,
                "production Step 9 reuses the existing 0024 reconciliation in dry-run mode")
        require("--mode apply" not in script and "migrationMode=apply" not in script,
                "production Step 9 contains no reconciliation apply path")
        require("STAGING-INVENTORY.tsv" in script and "sha256sum" in script,
                "production Step 9 separately inventories and hashes .image-staging")
        for field in ("imageRowCount", "matchingPhysicalFiles", "missingPhysicalFiles",
                      "untrackedPhysicalFiles", "untrackedSupportedImageFiles", "metadataOrChecksumConflicts",
                      "requiresExplicitDisposition", "step10Ready"):
            require(field in script, f"production Step 9 report records {field}")
        require("do **not** rerun the whole" in readme,
                "production documentation protects the live Step 8 freeze from a playbook-triggered restart")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: 0031-FEAT Step 9 production reconciliation tooling verified")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
