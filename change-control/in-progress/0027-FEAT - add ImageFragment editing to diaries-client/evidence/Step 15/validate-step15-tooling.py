#!/usr/bin/env python3
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
FEATURE = HERE.parents[1]
PROJECT = HERE.parents[4]


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    try:
        required = [
            HERE / "README.md",
            HERE / "RUNBOOK.md",
            HERE / "CHECKLIST.md",
            HERE / "MANUAL-EVIDENCE.md",
            HERE / "tooling/step15-common.ps1",
            HERE / "tooling/step15-begin.ps1",
            HERE / "tooling/step15-preflight.ps1",
            HERE / "tooling/step15-capture-production.ps1",
            HERE / "tooling/step15-finalize.ps1",
        ]
        require(all(p.is_file() for p in required), "all Step 15 evidence/tooling files are present")

        begin = read(HERE / "tooling/step15-begin.ps1")
        common = read(HERE / "tooling/step15-common.ps1")
        preflight = read(HERE / "tooling/step15-preflight.ps1")
        capture = read(HERE / "tooling/step15-capture-production.ps1")
        finalize = read(HERE / "tooling/step15-finalize.ps1")
        runbook = read(HERE / "RUNBOOK.md")

        require("No PASSED Step 14 final summary was found" in common and "Find-PassedStep14Summary" in begin,
                "Step 15 cannot begin without a PASSED Step 14 closure summary")
        require("diaries_image_fragment_writes_enabled" in preflight and "currently false" in preflight,
                "preflight proves the Playbooks gate contract and disabled production state")
        for phase in ("pre-deploy", "post-client-disabled", "pre-enable", "post-enable", "rollback-disabled"):
            require(phase in capture, f"production capture supports {phase}")
        require("orphan_image_references=0" in capture,
                "production capture rejects orphan IMAGE-to-Image database references")
        require("docker compose --file compose.yaml --env-file .env ps --all --quiet" in capture and
                "DB_CONTAINER=" in capture and "RESPONDER_CONTAINER=" in capture,
                "production capture resolves live containers from Compose service names")
        require("production-post-enable.txt" in finalize and "expectedGate=true" in finalize,
                "finalizer requires a successful post-enable capture")
        require("diaries_image_fragment_writes_enabled: false" in runbook and
                "diaries_image_fragment_writes_enabled: true" in runbook,
                "runbook defines explicit enable and non-destructive rollback values")
        require("Do not undo database rows or Files content" in runbook,
                "runbook forbids destructive rollback merely to disable authoring")

        step14 = read(FEATURE / "evidence/Step 14/tooling/step14-rollout-rehearsal.ps1")
        require("fail-closed diaries_image_fragment_writes_enabled default" in step14,
                "Step 14 rehearsal remains compatible with the new fail-closed Playbooks gate")

        implementation = read(FEATURE / "IMPLEMENTATION-STEPS.md")
        require("## Step 15 - Deploy non-destructively and enable production authoring deliberately" in implementation,
                "Step 15 implementation heading is still present")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: Step 15 tooling static validation complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
