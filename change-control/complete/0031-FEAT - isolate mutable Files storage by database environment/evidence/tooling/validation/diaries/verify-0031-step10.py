#!/usr/bin/env python3
"""Portable source verification for 0031-FEAT Step 10 Files-root seeding tooling."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
STEP10 = ROOT / "scripts/windows/0031-step10"
FEATURE = ROOT / "change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> int:
    try:
        script = (STEP10 / "seed-local-files-root.ps1").read_text(encoding="utf-8")
        readme = (STEP10 / "README.md").read_text(encoding="utf-8")
        implementation = (FEATURE / "IMPLEMENTATION-STEPS.md").read_text(encoding="utf-8")

        require("ProductionWriteFreezeConfirmed" in script,
                "Step 10 requires explicit confirmation that the production write freeze remains active")
        require("diaries-local-responder" in script and "diaries-published-smoke-responder" in script,
                "Step 10 checks the known local responder containers")
        require("GetActiveTcpListeners()" in script and "TCP/8081" in script,
                "Step 10 rejects a running direct Windows responder")

        for database_leaf, files_leaf in (
            ("development-infrastructure", "files-development-infrastructure"),
            ("local-docker-build", "files-local-docker-build"),
            ("local-published-smoke", "files-local-published-smoke"),
            ("common", "files-development-common"),
        ):
            require(f"'{database_leaf}' = '{files_leaf}'" in script,
                    f"Step 10 enforces frozen dataset pair {database_leaf} -> {files_leaf}")

        require("$filesDir -eq 'files'" in script and "must not seed or select the production Files root" in script,
                "Step 10 cannot target the production files leaf for a local dataset")
        require("Target Files root already exists; refusing to merge or overwrite" in script,
                "Step 10 refuses to merge into an existing candidate root")
        require("SOURCE-SHA256.tsv" in script and "Compare-Object" in script,
                "Step 10 re-verifies the shared source against the Step 8 SHA-256 baseline")
        require("catalogue.lock" in script and "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" in script,
                "Step 10 enforces the reviewed Step 9 staging disposition")
        require("-ExcludeImageStaging" in script and "'/XD'" in script and ".image-staging" in script,
                "Step 10 deliberately excludes .image-staging from the new dataset seed")
        require("'/COPY:DAT'" in script and "'/DCOPY:DAT'" in script and "'/XJ'" in script,
                "Step 10 uses the approved attribute-preserving robocopy semantics")
        require(".0031-step10-seed-" in script and "Rename-Item" in script,
                "Step 10 verifies a temporary sibling copy before promoting it to the configured target")
        require("TARGET-POST-PROBE-SHA256.tsv" in script and "writeReadDeleteProbe = 'PASS'" in script,
                "Step 10 verifies target mutation permissions and proves the probe leaves no data change")
        require("SOURCE-ACL.txt" in script and "TARGET-ACL.txt" in script and "aclReviewRequiredBeforeStep10CloseOut" in script,
                "Step 10 captures ACL evidence and keeps permission review as an explicit close-out gate")
        require("files-development-common" in readme and "one" in readme.lower(),
                "documentation explains that the normal common local dataset receives one Files root")
        require("## Step 10 — Create one Files root per independent non-production database dataset" in implementation,
                "Step 10 contract remains present in the implementation plan")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: 0031-FEAT Step 10 Files-root seeding tooling verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
