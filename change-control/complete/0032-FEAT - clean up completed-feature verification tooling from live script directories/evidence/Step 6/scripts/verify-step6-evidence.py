#!/usr/bin/env python3
"""Verify 0032 Step 6 production cleanup evidence and write DIFF.md."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

STEP6 = Path(__file__).resolve().parents[1]
FEATURE = STEP6.parent.parent
STEP1 = FEATURE / "evidence" / "Step 1"
STEP5 = FEATURE / "evidence" / "Step 5"

RETIRED = {
    "scripts/migration0024ImageCatalogue.sh",
    "scripts/step8-freeze-writes.sh",
    "scripts/step8-capture-production-database-backup.sh",
    "scripts/step9-reconcile-production.sh",
    "scripts/step12-compare-reconciliation.py",
    "scripts/step12-reconcile-production.sh",
    "scripts/step13-capture-production-control.sh",
    "scripts/step14-production-deployment.sh",
}

EXPECTED_POST = {
    "scripts/README.md",
    "scripts/backup-db-to-binary.sh",
    "scripts/backup-db-to-sql.sh",
    "scripts/dataset-backup-manifest.py",
    "scripts/logs.sh",
    "scripts/restore-db-from-binary.sh",
    "scripts/restore-db-from-sql.sh",
    "scripts/shell-prompt-client.sh",
    "scripts/shell-prompt-database.sh",
    "scripts/shell-prompt-mosquitto.sh",
    "scripts/shell-prompt-nginx.sh",
    "scripts/shell-prompt-responder.sh",
    "scripts/start.sh",
    "scripts/status.sh",
    "scripts/stop.sh",
}

EXECUTABLE_REQUIRED = EXPECTED_POST - {"scripts/README.md"}
SYNC_HASH_REQUIRED = {
    "scripts/backup-db-to-binary.sh",
    "scripts/backup-db-to-sql.sh",
    "scripts/dataset-backup-manifest.py",
    "scripts/restore-db-from-binary.sh",
    "scripts/restore-db-from-sql.sh",
}


@dataclass(frozen=True)
class Entry:
    mode: str
    owner: str
    group: str
    size: int
    sha256: str
    path: str


def parse_inventory(path: Path) -> dict[str, Entry]:
    result: dict[str, Entry] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("FILE\t"):
            continue
        parts = line.split("\t")
        if len(parts) != 7:
            raise ValueError(f"Malformed inventory row in {path}: {line}")
        _, mode, owner, group, size, digest, rel = parts
        result[rel] = Entry(mode, owner, group, int(size), digest, rel)
    return result


def parse_config(path: Path) -> tuple[dict[str, str], list[str]]:
    hashes: dict[str, str] = {}
    contracts: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("FILE\t"):
            parts = line.split("\t")
            if len(parts) == 3 and parts[1] != "SHA256":
                hashes[parts[2]] = parts[1]
        elif line.startswith("SELECTOR\t") or line.startswith("CONTRACT\t"):
            contracts.append(line)
    return hashes, contracts


def parse_step5_source_hashes(path: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("FILE\t"):
            continue
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        _, _mode, _size, digest, rel = parts
        name = Path(rel).name
        hashes[f"scripts/{name}"] = digest
    return hashes


def is_owner_executable(mode: str) -> bool:
    try:
        return bool(int(mode, 8) & 0o100)
    except ValueError:
        return False


def main() -> int:
    required = {
        "Step 1 baseline": STEP1 / "PLUTO-SCRIPTS-BEFORE.txt",
        "Step 5 supported source": STEP5 / "PLAYBOOKS-SCRIPTS-AFTER.txt",
        "fresh pre inventory": STEP6 / "PLUTO-SCRIPTS-PRE.txt",
        "playbook output": STEP6 / "PLAYBOOK-OUTPUT.txt",
        "post inventory": STEP6 / "PLUTO-SCRIPTS-POST.txt",
        "pre configuration": STEP6 / "PRODUCTION-CONFIG-PRE.txt",
        "post configuration": STEP6 / "PRODUCTION-CONFIG-POST.txt",
        "production status": STEP6 / "PRODUCTION-STATUS.txt",
    }
    missing = [f"{label}: {path}" for label, path in required.items() if not path.is_file()]
    if missing:
        print("FAIL: missing Step 6 evidence:", file=sys.stderr)
        for item in missing:
            print(f"  {item}", file=sys.stderr)
        return 1

    baseline = parse_inventory(required["Step 1 baseline"])
    pre = parse_inventory(required["fresh pre inventory"])
    post = parse_inventory(required["post inventory"])
    source_hashes = parse_step5_source_hashes(required["Step 5 supported source"])
    pre_cfg, pre_contract = parse_config(required["pre configuration"])
    post_cfg, post_contract = parse_config(required["post configuration"])
    playbook = required["playbook output"].read_text(encoding="utf-8", errors="replace")
    status = required["production status"].read_text(encoding="utf-8", errors="replace")

    failures: list[str] = []
    notes: list[str] = []

    baseline_names = set(baseline)
    pre_names = set(pre)
    if baseline_names != pre_names:
        failures.append(
            "fresh pre-deployment production filenames differ from the Step 1 baseline: "
            f"added={sorted(pre_names - baseline_names)}, removed={sorted(baseline_names - pre_names)}"
        )
    else:
        notes.append("Fresh pre-deployment script filenames exactly match the Step 1 baseline.")

    baseline_hash_drift = []
    for name in sorted(baseline_names & pre_names):
        if baseline[name].sha256 != pre[name].sha256:
            baseline_hash_drift.append(name)
    if baseline_hash_drift:
        failures.append(f"fresh pre-deployment hashes drifted from Step 1: {baseline_hash_drift}")
    else:
        notes.append("Fresh pre-deployment script hashes exactly match the Step 1 baseline.")

    post_names = set(post)
    if post_names != EXPECTED_POST:
        failures.append(
            "post-deployment script set is not the approved permanent set: "
            f"unexpected={sorted(post_names - EXPECTED_POST)}, missing={sorted(EXPECTED_POST - post_names)}"
        )
    else:
        notes.append("Post-deployment script names exactly match the approved permanent production set.")

    survivors = RETIRED & post_names
    if survivors:
        failures.append(f"approved retired helpers survived deployment: {sorted(survivors)}")
    else:
        notes.append("All eight approved retired production helpers are absent after deployment.")

    removed = pre_names - post_names
    if removed != RETIRED:
        failures.append(
            "deployment removal set differs from the eight-file allow-list: "
            f"removed={sorted(removed)}, expected={sorted(RETIRED)}"
        )
    else:
        notes.append("The deployment removed exactly the eight allow-listed obsolete helpers.")

    for name in sorted(EXECUTABLE_REQUIRED & post_names):
        if not is_owner_executable(post[name].mode):
            failures.append(f"retained operational script is not owner-executable: {name} mode={post[name].mode}")
    if not any("not owner-executable" in item for item in failures):
        notes.append("All retained operational scripts are owner-executable.")

    for name in sorted(SYNC_HASH_REQUIRED):
        expected_hash = source_hashes.get(name)
        if not expected_hash:
            failures.append(f"Step 5 source hash unavailable for {name}")
        elif name not in post:
            failures.append(f"retained source script missing after deployment: {name}")
        elif post[name].sha256 != expected_hash:
            failures.append(
                f"retained source/deployment hash mismatch for {name}: "
                f"post={post[name].sha256} source={expected_hash}"
            )
    if not any("source" in item and ("hash" in item or "missing" in item) for item in failures):
        notes.append("All five retained synchronized operational helpers match the approved Step 5 source hashes.")

    if pre_cfg != post_cfg:
        failures.append(f"production configuration file hashes changed: pre={pre_cfg}, post={post_cfg}")
    else:
        notes.append("Production .env, compose.yaml and responder.json fingerprints are unchanged.")

    if pre_contract != post_contract:
        failures.append("non-secret production database/Files contract lines changed between pre and post capture")
    else:
        notes.append("Non-secret production database/Files selectors and contract lines are unchanged.")

    if "Remove obsolete completed-feature production scripts" not in playbook:
        failures.append("playbook output does not show the explicit obsolete-script removal task")
    if not re.search(r"failed=0\b", playbook) or not re.search(r"unreachable=0\b", playbook):
        failures.append("playbook recap does not prove failed=0 and unreachable=0")
    if "exit_code: 0" not in playbook:
        failures.append("Step 6 deployment wrapper did not record exit_code: 0")
    if not any(item.startswith("playbook") for item in failures):
        notes.append("Controlled Playbooks deployment completed successfully with failed=0, unreachable=0 and exit code 0.")

    health_marker = "PASS: Step 6 production health verification completed."
    if health_marker not in status:
        failures.append("production status evidence does not contain the Step 6 health PASS marker")
    required_health = [
        f"PASS: {svc} is running and healthy."
        for svc in ("diaries-db", "diaries-mqtt", "diaries-responder", "diaries-client", "diaries-web")
    ]
    missing_health = [marker for marker in required_health if marker not in status]
    if missing_health:
        failures.append(f"required production service health evidence is incomplete: {missing_health}")
    else:
        notes.append("All five required Diaries services are running and healthy after deployment.")

    diff = STEP6 / "DIFF.md"
    lines = [
        "# 0032 Step 6 production cleanup diff",
        "",
        "## Result",
        "",
        "**PASS**" if not failures else "**FAIL**",
        "",
        "## Verified observations",
        "",
    ]
    lines.extend(f"- {n}" for n in notes)
    lines += ["", "## Removed by deployment", ""]
    lines.extend(f"- `{n}`" for n in sorted(removed))
    lines += ["", "## Post-deployment script set", ""]
    lines.extend(f"- `{n}` — mode `{post[n].mode}`, owner `{post[n].owner}:{post[n].group}`" for n in sorted(post))
    lines += ["", "## Configuration fingerprint", ""]
    for path in sorted(post_cfg):
        lines.append(f"- `{path}` — `{post_cfg[path]}` (unchanged)")
    if failures:
        lines += ["", "## Failures", ""]
        lines.extend(f"- {f}" for f in failures)
    else:
        lines += [
            "",
            "## Conclusion",
            "",
            "The production cleanup removed exactly the approved historical tooling, retained supported operational tooling, preserved the production database/Files/responder configuration fingerprints, and left the Diaries application healthy.",
        ]
    diff.write_text("\n".join(lines) + "\n", encoding="utf-8")

    for note in notes:
        print(f"PASS: {note}")
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    print(f"Wrote: {diff}")
    if failures:
        return 1
    print("PASS: Step 6 production cleanup evidence verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
