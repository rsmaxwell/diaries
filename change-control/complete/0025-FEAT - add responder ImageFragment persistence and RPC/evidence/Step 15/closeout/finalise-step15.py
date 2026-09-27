"""Validate a PASSED Step 15 deployment run, generate close-out evidence, optionally update feature docs."""
from __future__ import annotations
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import uuid

HERE = Path(__file__).resolve().parent
STEP15 = HERE.parent
FEATURE = STEP15.parent.parent
ROOT = FEATURE.parent.parent.parent

p = argparse.ArgumentParser()
p.add_argument("evidence", help="deployment evidence directory containing result.json")
p.add_argument("--apply-docs", action="store_true", help="update feature README and IMPLEMENTATION-STEPS after a clean pass")
a = p.parse_args()
run = Path(a.evidence).resolve()
result = json.loads((run / "result.json").read_text(encoding="utf-8"))

required = {
    "status": "PASSED",
    "productionModified": False,
    "liveDatabaseUsed": False,
    "nasUsed": False,
    "databaseRowsUnchanged": True,
    "controlledFileAbsent": True,
    "workDirectoryRemoved": True,
}
for key, expected in required.items():
    if result.get(key) != expected:
        raise SystemExit(f"Cannot close Step 15: {key}={result.get(key)!r}, expected {expected!r}")
if any(code != 0 for code in result.get("cleanup", {}).values()):
    raise SystemExit("Cannot close Step 15: one or more owned Docker containers failed cleanup")
if not result.get("step14SourceComparison", {}).get("matchesStep14"):
    raise SystemExit("Cannot close Step 15: source did not match Step 14 inventory")
phases = {x.get("phase"): x for x in result.get("deployments", [])}
if phases.get("disabled", {}).get("imageFragmentWritesEnabled") is not False:
    raise SystemExit("Cannot close Step 15: disabled deployment phase missing")
if phases.get("enabled", {}).get("imageFragmentWritesEnabled") is not True or phases.get("replay", {}).get("imageFragmentWritesEnabled") is not True:
    raise SystemExit("Cannot close Step 15: controlled enabled/replay phases missing")

feature_readme = FEATURE / "README.md"
steps = FEATURE / "IMPLEMENTATION-STEPS-0025.md"
old_readme = feature_readme.read_text(encoding="utf-8")
old_steps = steps.read_text(encoding="utf-8")
new_readme = old_readme
new_steps = old_steps

# Prepare all feature-document transformations before writing anything.
if a.apply_docs:
    new_readme = new_readme.replace("## Status\n\nIn progress", "## Status\n\nComplete")
    old_status = "Step 15.1 development schema readiness is verified; see [15.1 evidence](evidence/Step%2015/15.1/README.md). Step 15.2–15.5 and production migration remain subsequent work."
    new_status = "Step 15 development deployment, controlled validation and close-out is complete; see [Step 15 evidence](evidence/Step%2015/README.md). Production migration/deployment and enabling IMAGE authoring remain separate operational work; the authoring gate stays disabled until the 0026/0027 rollout prerequisites are approved."
    if old_status not in new_readme:
        raise SystemExit("Feature README status marker not found; documentation was not modified")
    new_readme = new_readme.replace(old_status, new_status)
    new_readme = new_readme.replace("- [ ] Add tests proving MARQUEE cannot carry imageId and IMAGE cannot acquire a Marquee through responder operations.", "- [x] Add tests proving MARQUEE cannot carry imageId and IMAGE cannot acquire a Marquee through responder operations.")
    marker = "## Acceptance Criteria"
    start = new_readme.index(marker)
    end = new_readme.index("## Dependencies", start)
    new_readme = new_readme[:start] + new_readme[start:end].replace("- [ ]", "- [x]") + new_readme[end:]

    closeout_section = """
## Implementation close-out (Step 15)

Step 14 was revalidated on 2026-09-28 after the synchronisation source changes: responder 322 discovered / 285 passed / 37 environment-gated skips with zero failures/errors and a successful build; diaries-web 50 passed with build success; diaries-client 132 passed with production build success; six selected real PostgreSQL/MQTT tests passed, including large retained-tree startup replay. Step 15.1 then verified the actual development schema and backup before any candidate start. Step 15.2/15.3 deployed that same source candidate in a controlled environment and passed the disabled-gate MARQUEE smoke flow plus the enabled IMAGE create/edit/reference/delete/restart-replay flow. See `evidence/Step 15`.

The implemented RPC design extends `updateFragment`: omitted `imageId` preserves the reference; explicit null clears it for IMAGE; a positive existing ID attaches/replaces it; MARQUEE cannot acquire a non-null Image reference; type and Page remain immutable. Reference mutation uses the existing caller-owned Fragment lock/version transaction. Attachment takes a pessimistic read lock on the Image row; `DeleteImage` takes a pessimistic write lock on the same row and rechecks Fragment references, so attach/delete races cannot commit a dangling FK. Recoverable 0030 file/database/MQTT deletion remains the sole physical Image deletion path.

Production was not modified by Step 15. `imageFragmentWritesEnabled` remains fail-closed (missing/null/false means disabled). 0026–0029 remain deliberately deferred as documented below; therefore closing 0025 does not enable production IMAGE authoring.

"""
    if "## Implementation close-out (Step 15)" not in new_readme:
        new_readme = new_readme.replace("## Dependencies", closeout_section + "## Dependencies")

    old_intro = "**Completed for development 2026-09-27.** The Step 2 schema was already installed on `diaries-development-db` / `diaries`; fresh preflight/postflight and schema inspection passed. Backup and responder candidate identity are recorded in [15.1 evidence](evidence/Step%2015/15.1/README.md). No reapply or responder start was performed; later Step 15 substeps remain open."
    new_intro = "**Completed for development 2026-09-27.** Step 15.1 verified the installed development schema and restore point before starting the candidate. Step 15.2 then deployed the Step 14-matched responder with ImageFragment writes disabled and passed the normal MARQUEE/upload/deletion smoke flow. Step 15.3 deliberately enabled IMAGE authoring only in a disposable controlled environment and passed create/edit/reference protection/delete plus restart/replay validation. Step 15.4 records the final design/test/migration evidence, and Step 15.5 acceptance is satisfied. See [Step 15 evidence](evidence/Step%2015/README.md). Production was not modified and IMAGE authoring remains disabled pending the later rollout prerequisites."
    if old_intro not in new_steps:
        raise SystemExit("Implementation Steps Step 15 marker not found; documentation was not modified")
    new_steps = new_steps.replace(old_intro, new_intro)
    marker = "## Final acceptance checklist"
    start = new_steps.index(marker)
    end = new_steps.index("## Explicitly deferred work", start)
    new_steps = new_steps[:start] + new_steps[start:end].replace("- [ ]", "- [x]") + new_steps[end:]
    notices = {
        "### 15.2 Deploy responder with production ImageFragment writes disabled\n": "\n**Completed.** Controlled deployment with the gate disabled passed; see `evidence/Step 15/deployment/revalidation-20260928`.\n",
        "### 15.3 Controlled IMAGE validation\n": "\n**Completed.** Controlled gate-enabled create/edit/delete/restart-replay validation passed; see `evidence/Step 15/deployment/revalidation-20260928`.\n",
        "### 15.4 Update change-control records\n": "\n**Completed.** Exact files, test/build totals, migration/integration evidence, `imageId` semantics, locking protocol, gate state and deferrals are recorded under `evidence/Step 15/closeout`.\n",
        "### 15.5 Close only when acceptance criteria are evidenced\n": "\n**Completed.** The final acceptance checklist is evidenced by Steps 2–15; production authoring remains deliberately disabled.\n",
    }
    for heading, notice in notices.items():
        if heading not in new_steps:
            raise SystemExit(f"Missing heading: {heading.strip()}")
        if notice.strip() not in new_steps:
            new_steps = new_steps.replace(heading, heading + notice, 1)

final = HERE / "revalidation-20260928"
if final.exists():
    raise SystemExit(f"Close-out evidence already exists: {final}")
tmp = HERE / (".finalising-" + uuid.uuid4().hex[:10])
tmp.mkdir(parents=True)

try:
    (tmp / "README.before-closeout.md").write_text(old_readme, encoding="utf-8")
    (tmp / "IMPLEMENTATION-STEPS.before-closeout.md").write_text(old_steps, encoding="utf-8")

    if a.apply_docs:
        # Atomic replace within the same filesystem; both transformed texts were validated above.
        rtmp = feature_readme.with_name(feature_readme.name + ".step15.tmp")
        stmp = steps.with_name(steps.name + ".step15.tmp")
        rtmp.write_text(new_readme, encoding="utf-8")
        stmp.write_text(new_steps, encoding="utf-8")
        os.replace(rtmp, feature_readme)
        os.replace(stmp, steps)

    summary = {
        "status": "PASSED",
        "closedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "deploymentEvidence": str(run),
        "jarSha256": result.get("jarSha256"),
        "backupSha256": result.get("backupSha256"),
        "step14SourceMatched": True,
        "productionModified": False,
        "liveDatabaseUsed": False,
        "nasUsed": False,
        "databaseRowsUnchanged": True,
        "controlledFileAbsent": True,
        "ownedContainersCleaned": True,
        "documentationApplied": bool(a.apply_docs),
    }
    (tmp / "result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    readme = f"""# 0025 Step 15 — Development deployment, controlled validation and close-out

**PASSED.** Step 15.1 had already verified the real development schema/backup/candidate readiness. The authoritative Step 15.2/15.3 run is `{run.as_posix()}` and deployed candidate JAR SHA-256 `{result.get('jarSha256')}` against disposable PostgreSQL/Mosquitto and a private filesystem tree.

## 15.2 — gate disabled smoke validation

The candidate started with `imageFragmentWritesEnabled=false`. Evidence proves sign-in and existing retained reads, controlled MARQUEE create/edit/delete, upload/catalogue behavior, generic `DeleteFile` protection, unreferenced `DeleteImage`, and 403 rejection of `addImageFragment`. See `disabled-rpc.json`, `existing-read-summary.json`, `disabled-responder.log` and `result.json` in the deployment run.

## 15.3 — controlled IMAGE validation

With the gate deliberately enabled only for the disposable fixture, evidence preserves the IMAGE Fragment row, Image row, zero Marquees, canonical/date retained Fragment state, retained Image state, 409 reference protection, Image-reference clear/reattach behavior and old-date tombstone. Retained state was then deliberately corrupted, the responder restarted, and startup replay reconstructed it from the database. After deleting the final Fragment reference, `DeleteImage` completed and DB rows, retained topics and the physical fixture file were removed. See `enabled-rpc.json`, `state.json`, `corrupt-rpc.json`, `replay-delete-rpc.json`, `replayed-retained.json` and the responder logs.

## Safety and cleanup

`productionModified=false`, `liveDatabaseUsed=false`, `nasUsed=false`; the original disposable application rows matched before/after fixture cleanup; the private fixture file was absent; all owned Docker containers and the temporary responder work tree were removed. The runner verified the application source still matched the Step 14 SHA-256 inventory before deployment.

## 15.4 — change-control close-out

`../CHANGED-FILES.md`, `../DESIGN-DECISIONS.md` and `../TEST-BUILD-SUMMARY.md` record the exact implementation scope, test/build totals, migration/integration evidence, final `updateFragment.imageId` semantics, attach/delete locking protocol, authoring-gate policy and 0026–0029 deferrals.

## 15.5 — acceptance decision

The responder capability, persistence integrity, retained contract, reference-aware Image deletion, safe authoring gate and controlled deployment/replay lifecycle are all evidenced. 0025 is technically complete. Production migration/deployment and enabling IMAGE authoring are deliberately **not** performed by this step; production authoring remains disabled until the later reader/client rollout prerequisites are approved.
"""
    (tmp / "README.md").write_text(readme, encoding="utf-8")

    def digest(path: Path) -> str:
        h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
    items = [
        STEP15 / "deployment" / "run-container-deployment.py",
        STEP15 / "deployment" / "smoke.cjs",
        HERE / "CHANGED-FILES.md",
        HERE / "DESIGN-DECISIONS.md",
        HERE / "TEST-BUILD-SUMMARY.md",
        run / "result.json",
        feature_readme,
        steps,
    ]
    with (tmp / "source-sha256.csv").open("w", encoding="utf-8", newline="") as f:
        f.write("path,sha256\n")
        for x in items:
            f.write(f'"{x.relative_to(ROOT).as_posix()}",{digest(x)}\n')

    if a.apply_docs:
        (tmp / "documentation-update.json").write_text(json.dumps({
            "status": "APPLIED",
            "featureReadme": str(feature_readme),
            "implementationSteps": str(steps),
            "featureReadmeSha256After": digest(feature_readme),
            "implementationStepsSha256After": digest(steps),
        }, indent=2) + "\n", encoding="utf-8")

    tmp.rename(final)
except Exception:
    # If documents were applied but final evidence generation fails, restore originals.
    if a.apply_docs:
        feature_readme.write_text(old_readme, encoding="utf-8")
        steps.write_text(old_steps, encoding="utf-8")
    if not tmp.resolve().is_relative_to(HERE.resolve()):
        raise RuntimeError("Refusing cleanup outside close-out directory")
    shutil.rmtree(tmp, ignore_errors=True)
    raise

print(json.dumps(json.loads((final / "result.json").read_text(encoding="utf-8")), indent=2))
