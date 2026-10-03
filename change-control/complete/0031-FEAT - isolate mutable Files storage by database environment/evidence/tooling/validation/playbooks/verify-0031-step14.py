#!/usr/bin/env python3
"""Portable source verification for 0031-FEAT Step 14 production deployment tooling."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "roles/diaries/files/sync/scripts/step14-production-deployment.sh"
README = ROOT / "roles/diaries/files/sync/scripts/README.md"
MOSQUITTO = ROOT / "roles/diaries/files/sync/config/mosquitto/mosquitto.conf"
COMPOSE = ROOT / "roles/diaries/templates/compose.yaml.j2"
START = ROOT / "roles/diaries/templates/scripts/start.sh.j2"
COPY_TASKS = ROOT / "roles/diaries/tasks/copy.yaml"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> int:
    try:
        script = SCRIPT.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")
        mosquitto = MOSQUITTO.read_text(encoding="utf-8")
        compose = COMPOSE.read_text(encoding="utf-8")
        start = START.read_text(encoding="utf-8")
        copy_tasks = COPY_TASKS.read_text(encoding="utf-8")

        require("max_inflight_messages 20" in mosquitto and "max_queued_messages 0" in mosquitto,
                "production Diaries broker adopts the Step 13 complete-retained-snapshot flow-control policy")
        require("max_queued_messages 10000" not in mosquitto,
                "production Diaries broker no longer retains the historical 10,000-message truncation ceiling")
        require("Validate retained-snapshot broker flow-control policy" in copy_tasks and
                "max_queued_messages[[:space:]]+0" in copy_tasks,
                "Ansible validates the deployed broker queue policy before the restart handler runs")
        require("preflight" in script and "postflight" in script,
                "Step 14 helper separates frozen pre-deploy controls from post-deploy verification")
        require("require_responder_stopped" in script and "Step 13/14 write freeze" in script,
                "Step 14 preflight preserves the Step 13 responder write freeze")
        require("STEP8-DATABASE-BACKUP-CHECK.txt" in script and "STEP8-FILES-SNAPSHOT-CHECK.txt" in script,
                "Step 14 preflight verifies both Step 8 recovery halves remain available")
        require("REDACTED-CONFIG" in script and "<redacted>" in script,
                "Step 14 records production configuration without exposing secrets")
        require("local.env" in script and "verify_no_local_override_participation" in script,
                "Step 14 rejects local override participation in production startup")
        require("NONPRODUCTION-FILES-INVENTORY.tsv" in script and "files-development-*" in script,
                "Step 14 brackets the deployment with SHA-256 controls for non-production Files roots")
        require("FILES-ROUTE-CHECK" in script and "http://localhost:8081/files/" in script,
                "Step 14 proves an existing /files route object is served after deployment")
        require("synchronise: ok" in script and "require_responder_synchronised" in script,
                "Step 14 waits for the responder retained-tree startup synchronisation to succeed")
        require("stop diaries-responder" in script and "up --detach --no-deps --wait diaries-responder" in script,
                "Step 14 briefly re-freezes only the responder for deterministic read-only verification")
        require("step12-reconcile-production.sh" in script and "--write-freeze-confirmed" in script,
                "Step 14 reuses the existing read-only production reconciliation under a responder write freeze")
        require("cmp -s" in script and "Production Image catalogue changed" in script and
                "Production mutable Files bytes changed" in script,
                "Step 14 fails if production durable Image/File state changes across deployment")
        require("migration0024ImageCatalogue.sh" not in script and "--mode apply" not in script,
                "Step 14 adds no direct reconciliation apply/mutation path")
        require("subpath: ${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}" in compose,
                "production Compose keeps /data/files selected by the explicit Files selector")
        require("local.env" not in compose and "local.env" not in start,
                "production Compose/start templates do not load the local override file")
        require("0031 Step 14" in readme and "step14-production-deployment.sh" in readme,
                "production operating documentation covers Step 14")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: 0031-FEAT Step 14 production deployment tooling verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
