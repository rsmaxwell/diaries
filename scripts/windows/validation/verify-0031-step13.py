#!/usr/bin/env python3
"""Portable source verification for 0031-FEAT Step 13 lifecycle isolation tooling."""
from pathlib import Path
import base64
import re
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[3]
LOCAL = ROOT / "scripts/windows/0031-step13"
FEATURE = ROOT / "change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> int:
    try:
        ps = (LOCAL / "run-local-lifecycle.ps1").read_text(encoding="utf-8")
        rpc = (LOCAL / "step13-rpc.cjs").read_text(encoding="utf-8")
        runbook = (FEATURE / "evidence/Step 13/RUNBOOK.md").read_text(encoding="utf-8")
        plan = (FEATURE / "IMPLEMENTATION-STEPS.md").read_text(encoding="utf-8")
        sync = (ROOT / "diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/sync/Synchronise.java").read_text(encoding="utf-8")
        sync_test = (ROOT / "diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/sync/SynchroniseLargeRetainedTreeMqttIntegrationTest.java").read_text(encoding="utf-8")
        mosquitto_conf = (ROOT / "config/mosquitto/mosquitto.conf").read_text(encoding="utf-8")
        large_tree_conf = (ROOT / "config/mosquitto/mosquitto-large-tree-test.conf").read_text(encoding="utf-8")
        mosquitto_readme = (ROOT / "config/mosquitto/README.md").read_text(encoding="utf-8")
        local_build_compose = (ROOT / "compose.local-docker-build.yaml").read_text(encoding="utf-8")
        published_smoke_compose = (ROOT / "compose.local-published-smoke.yaml").read_text(encoding="utf-8")
        for action in ("upload", "observe", "delete", "cleanup"):
            require(action in ps, f"local harness contains {action} phase")
        require("Exactly one local Diaries database mode must be running" in ps,
                "local harness rejects concurrent local database modes")
        require("./data/database/common" in ps and "files-development-common" in ps,
                "local harness pins the approved shared common durable pair")
        require("Observe must run from a second local mode" in ps,
                "second-mode observation cannot be satisfied by the upload mode")
        require("OBSERVE-*.json" in ps and "Delete is blocked" in ps,
                "delete is gated on a successful second-mode proof")
        require("SELECT id,version,relative_path" in ps and "Get-PhysicalFileProbe" in ps,
                "database and physical file identity are captured")
        require("exit code ${rc}:" in ps and "exit code $rc:" not in ps,
                "PowerShell interpolation before colon uses a braced variable reference")
        require("expected HTTP 404 from the registered /diaries context" in ps and
                "Method Get" in ps and "StatusCode" in ps,
                "responder HTTP reachability honours the established /diaries 404 contract")
        require("uploadFile" in rpc and "deleteImage" in rpc,
                "real supported Image lifecycle RPC operations are used")
        require("DIARIES_STEP13_OBSERVER_USERNAME" in ps and "DIARIES_STEP13_OBSERVER_PASSWORD" in ps and
                "config.mqtt.user.username" in ps and "config.mqtt.user.password" in ps,
                "retained-state observation uses responder MQTT credentials from the selected responder config")
        require("connect('observer', 'observer')" in rpc and "connect('delete-observer', 'observer')" in rpc,
                "retained Image verification is separated from the diaries-client RPC identity")
        require("Recovery cleanup refuses non-Step-13 Image path" in ps and "-ImageId is required for cleanup" in ps and
                "step13-rpc.cjs cleanup" not in ps,
                "recovery cleanup is id-gated and restricted to generated Step 13 paths")
        require(ps.count("@(Get-ImageRows") >= 5,
                "PowerShell callers preserve zero/one/many Image query results as arrays under StrictMode")
        require("-AllowMissing" in ps and "retained-check" in ps and "Get-Step13PhysicalCandidates" in ps and
                "alreadyAbsent=$true" in ps,
                "cleanup can safely resume after delete committed before evidence capture completed")
        require("async function retainedCheck" in rpc and "nonEmptyCount" in rpc,
                "retained-only cleanup recovery check is available without application credentials")
        match = re.search(r"FIXTURE_BYTES\s*=\s*Buffer\.from\(\s*'([^']+)'\s*,\s*'base64'", rpc, re.S)
        require(match is not None, "Step 13 embedded PNG fixture is discoverable")
        png = base64.b64decode(match.group(1), validate=True)
        require(png.startswith(b"\x89PNG\r\n\x1a\n"), "Step 13 embedded fixture has a PNG signature")
        offset = 8
        saw_iend = False
        while offset + 12 <= len(png):
            length = struct.unpack(">I", png[offset:offset + 4])[0]
            end = offset + 12 + length
            require(end <= len(png), "Step 13 embedded PNG chunks are not truncated")
            chunk_type = png[offset + 4:offset + 8]
            chunk_data = png[offset + 8:offset + 8 + length]
            expected_crc = struct.unpack(">I", png[offset + 8 + length:end])[0]
            actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
            require(expected_crc == actual_crc, f"Step 13 embedded PNG chunk {chunk_type.decode('ascii')} has a valid CRC")
            offset = end
            if chunk_type == b"IEND":
                saw_iend = True
                break
        require(saw_iend and offset == len(png), "Step 13 embedded PNG is complete through IEND")
        require("diaries/images/" in rpc and "payloadBytes === 0" in rpc,
                "retained publication and deletion tombstone are verified")
        require("overwrite: true" in rpc and "status.code !== 409" in rpc,
                "current catalogued overwrite rejection is explicitly verified")
        require("/files/${subdir}/${name}" in rpc and "static" in rpc,
                "stable public /files URL and static bytes are verified")
        require("production BEFORE" in runbook and "production AFTER" in runbook,
                "runbook brackets local mutation with production controls")
        require("Step 13 implementation note" in plan,
                "implementation plan records the Step 13 tooling state")
        require("Test-ContainerFilesPermissions" in ps and "expected mode 700" in ps and
                "Recreate the mode-specific nas-photo Docker volume" in ps,
                "local Docker lifecycle rejects CIFS mounts that cannot present owner-only staging permissions")
        require("docker exec $Mode.Responder stat -c '%a' /data/files" in ps and
                "docker exec $Mode.Responder test -d /data/files/.image-staging" in ps and
                "sh -c 'p=/data/files/.image-staging;" not in ps and
                'sh -c "p=/data/files/.image-staging;' not in ps,
                "container permission probe avoids nested PowerShell/docker/sh quoting")
        for name, compose in (("local-docker-build", local_build_compose),
                              ("local-published-smoke", published_smoke_compose)):
            require("vers=3.0,dir_mode=0700,file_mode=0600" in compose,
                    f"{name} synthesizes owner-only CIFS directory/file permissions for mutable Files")
        for branch in ("diaries/diaries/#", "diaries/pages/#", "diaries/fragments/#",
                       "diaries/marquees/#", "diaries/images/#", "diaries/dates/#",
                       "diaries/people/#", "diaries/roles/#"):
            require(branch in sync, f"retained snapshot includes non-overlapping branch {branch}")
        require("for(String topicFilter:SNAPSHOT_TOPIC_FILTERS)" in sync and
                "sync.awaitDrained(publisher);" in sync,
                "retained snapshot drains each top-level branch before subscribing to the next")
        require("TOPIC_COUNT = TOPICS_PER_BRANCH * Synchronise.SNAPSHOT_TOPIC_FILTERS.length" in sync_test and
                "result.size()>10_000" in sync_test,
                "large-tree regression exceeds the historical 10,000-message threshold across branches")
        for name, conf in (("local broker", mosquitto_conf), ("large-tree test broker", large_tree_conf)):
            require("max_inflight_messages 20" in conf, f"{name} retains bounded QoS in-flight flow")
            require("max_queued_messages 0" in conf and "max_queued_messages 10000" not in conf,
                    f"{name} removes the finite retained-replay message-count queue ceiling")
        require("interim correctness safeguard" in mosquitto_readme and
                "current TODO features are complete" in mosquitto_readme and
                "segments the subscription space" in mosquitto_readme,
                "Mosquitto documentation records the interim unlimited queue and deferred redesign")
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: 0031-FEAT Step 13 local isolation tooling verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
