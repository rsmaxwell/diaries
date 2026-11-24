# 0028-FEAT — Controlled production maintenance, release and rollback handoff

Prepared 24 November 2026. Based on uploaded `diaries-sources-20261124-090430.zip`, `playbook-sources-20261124-084655.zip`, accepted terminal receipts through 15:14 UTC and the pinned responder migration build. **This is an operator runbook, not permission to operate on production.** Nothing in this package stops services, changes backup state or runs migration. Formal 0028 steps remain OPEN until the owner accepts evidence.

## Accepted results: do not repeat expensive testing

- Reviewed **71** in-place IMAGE conversions; **Fragment 1564 DEFER**; preserve **30 links**, **22 same-identity Marquees**, page associations and chronology.
- Step 2 isolated migration, journal, rollback-injection, MQTT replay and Reader/Editor GUI tests passed; the Editor lock-return bug belongs to **0053-DEF**.
- Step 3 source freshness on `pluto` passed 24 November 09:53 UTC, **not** a replacement for a final writer-stopped freshness check.
- `mars` and `backup` retain identical `production/20261124-003112Z` logical backup identities and component metadata; custom PostgreSQL dump was successfully restored to an isolated PostgreSQL 18 DB with **2,331 Fragments; 2,270 Marquees; 85 Images; 683 Pages**. **Three** Files payloads were hashed; a complete Files restore was **not** tested.
- One-off migration fat JAR built from responder commit `7aa6296...`; exact 40-character SHA and JAR digest are in `ARTIFACT-IDENTITY.txt`, not inferred from the abbreviated display. Release-candidate assessment passed, but never authorised production apply.

## Critical deployment facts: names matter

| Component | Docker container | Compose service |
|---|---|---|
| PostgreSQL | `diaries-postgres` | `diaries-db` |
| Mosquitto | `diaries-mosquitto` | `diaries-mqtt` |
| Responder | `diaries-responder` | `diaries-responder` |

- Source Dockerfile uses **Eclipse Temurin Java 25**; today's production runtime read-only probe confirms Java 25 before a handoff passes. It does **not** test starting the migration main class in production.
- Production PostgreSQL **publishes a host port**. Stopping the responder alone does not exclude another host or direct database client. The writer survey observed two client sessions; their types, sources and permitted maintenance exceptions need to be reviewed at the actual cutover.
- `diaries-compose.service` runs the broad `stop.sh` on stop: the script removes the shared Nginx Diaries route and calls `docker compose down --remove-orphans`. **Do not use `systemctl stop diaries-compose` as a responder-only isolation primitive**; it would also affect PostgreSQL and MQTT.
- `diaries-complete-backup-publish.service` can invoke `fixed-capture-preflight` + `fixed-capture`, or legacy `publish-preflight` + `publish`, depending on deployed settings. Both may stop/restart the responder depending on its entry state. Coordinate **both timer and active service**, preserve original unit states, and do not allow unexpected restarts.
- The current 0036 fixed capture writes a **mutable `diaries-backup/` working copy on pluto**, uses `rsync --delete` and writes a verified marker only on success. The immutable rollback candidate exists only after the independently verified `mars` pull, Btrfs snapshot and successful replication to `backup` (plus retention/pin safeguards).
- The complete database+Files backup excludes MQTT retained broker state, credentials, original scanned diary tree and application images. Rollback must coordinate retained MQTT reconciliation with the restored DB; do not describe the dataset alone as a full broker restore.

## Stage 0 — NOW: read-only compatibility and evidence handoff

**Windows PC, Cygwin**, from the Diaries parent root, after applying the ZIP with Beyond Compare 4:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/prepare-0028-step3-operator-handoff.sh'
```

The script reads the newest private Step 3 release-artifact, live-runtime and final-candidate receipts, binds their hashes to the accepted recovery receipt, verifies the fat JAR class and SQL resource and tests the **current responder's Java version on pluto read-only** (`docker exec diaries-responder java -version`). It records the **parent-pinned** and **working** responder submodule revisions without changing Git. The result always says `PRODUCTION APPLY NOT AUTHORISED`. On failure, inspect the private evidence, not production.

Before an actual release, reconcile/pin the new `diaries-responder` submodule commit in the parent repository after reviewing unrelated parent changes. **Do not reset or discard local changes and do not pull/synchronise mango blindly.** Temporary migration source remains committed and will be removed in a later cleanup commit after accepted rollback window closes.

## Stage 1 — FUTURE: owner review before starting maintenance

No commands in stages 1–5 below are approved by running Stage 0.

**Explicit owner acceptance is required** for (a) Step 1 exact manifest/71 conversions/1 defer, (b) Step 2 accepted rehearsal, (c) outage/writer exclusion plan, (d) acceptable fresh recovery point and rollback window, and (e) separate exact production apply after the live dry-run. Record signer, UTC time, Git/JAR/manifest hashes and scope in *private 0028 feature evidence*. No generic `YES` or automatically created JSON substitutes for owner approval.

**Windows PC, Cygwin — optional read-only live checks before the window:**

```bash
ssh pluto 'systemctl show diaries-compose.service diaries-complete-backup-publish.timer diaries-complete-backup-publish.service --property=LoadState,ActiveState,SubState,UnitFileState,Result --no-pager'
ssh pluto 'systemctl cat diaries-complete-backup-publish.service'
ssh pluto 'docker ps --format "{{.Names}} | {{.Image}} | {{.Status}}"'
ssh mars 'sudo -n diaries-backup-status --limit 5'
ssh backup 'sudo -n diaries-backup-status --limit 5'
```

**Do not display or upload the production `.env`, `responder.json`, DB password, NAS credentials or source HTML/URL manifest**. These are already confined to private feature evidence or deployment configuration.

## Stage 2 — FUTURE: positive writer exclusion (approved maintenance only)

This is a runbook sequence, **not an automatic script**. Do not proceed without a reviewed control for **every** write path.

1. Revalidate current Compose services, shared Nginx Diaries-only routes and runtime image IDs. Announce the editor outage. Prevent new Editor/MQTT RPC writes and safely drain/evict active editor sessions; ensure outstanding Fragment locks are understood. If this cannot be achieved without affecting shared Nginx applications, stop and revisit the method.
2. Record and coordinate current `diaries-complete-backup-publish.timer` state and confirm `.service` is **not running**. Under explicit maintenance approval, stop the timer and establish that no scheduled capture can restart the responder. Retain the exact original enabled/active state and means of restoration.
3. Quiesce `diaries-responder` through the exact **Compose service** while leaving `diaries-db` and `diaries-mqtt` available. Check container absent/stopped; inspect restart policy and other supervisors. Never infer isolation from a single `docker stop` when restarts are possible. Do **not** bring down the entire Compose project or `diaries-compose.service` to isolate the responder.
4. Independently contain direct PostgreSQL writes through the published host port and any Docker/internal peers. Choose and review an environment-appropriate **reversible** access control, record allowed maintenance connection(s) and verify new unauthorised connection attempts are rejected. Read `pg_stat_activity` from a privileged session and account for each connection. Do not invent a generic firewall rule or revoke a DB role without reviewing live ingress and operational dependencies.
5. Exclude any separate Files-root/NAS writers for the maintenance window. Check `.image-staging` and all 72 reviewed legacy source occurrences on this **stopped-writer** dataset. Confirm no active Fragment locks and no drift from the approved reviewed text/versions. If drift exists, stop, review and regenerate production dry-run plan: **never reuse the old rehearsal plan**.

Do not call this step PASS based on the previous runtime survey: it showed live writers and an exposed port.

## Stage 3 — FUTURE: fresh matched, durable recovery point (approved maintenance only)

**On pluto (existing SSH terminal)**, use its *deployed* project `scripts/backup-dataset.sh` only after checking the active `.service` is inactive and its actual `ExecStart` contract. For the configured 0036 fixed-capture mode the relevant subcommands are `fixed-capture-preflight` and then `fixed-capture`. No bare `publish` substitution. Capture **only with responder already stopped**, and verify it **remains stopped** after the capture; the backup tool otherwise preserves/reinstates its entry state. Verify the fixed marker and schema-2 manifest; `fixed-capture` will overwrite the mutable working `diaries-backup/` and may delete obsolete files there, so it is not itself an immutable rollback point.

**On mars (existing SSH terminal)**, after successful pluto capture, arrange the installed guarded `diaries-pull` receive, verify the snapshot-eligibility marker, and create a **new** native read-only Btrfs snapshot of the verified dataset. Do not use the old `20261124-003112Z` ID as proof the new point is current. Verify the new backup ID, manifest hash, DB custom+SQL and Files contents, and protect the required snapshot against retention pruning. The source `btrfs-snapshot-manager create` is available but **requires explicit maintenance approval**, as it creates snapshots.

**On backup (existing SSH terminal)**, after successful native Btrfs transfer, verify receipt of the **same new backup ID and manifest identity** and confirm the rollback snapshot is retained/pinned as needed. Both `mars` and `backup` must agree on the new ID, and the rollback instructions must identify an actual immutable snapshot **path**, not the mutable pluto working copy. The older accepted full DB restore and 3 Files sample hashes need not be repeated, but new point integrity and availability must be evidenced.

Never run a source pull, snapshot creation, native push, prune, restore or delete under the label 'read-only'. Never modify existing snapshots or backup datasets as a shortcut to establishing recovery.

## Stage 4 — FUTURE: validated one-shot migration, only after recovery point

1. Stage the *pinned, hashed* disposable fat JAR and the approved reviewed private manifest securely; use the **same JAR** for dry-run, apply and postflight. Source JAR's default main is the responder; migration must be invoked as:

   ```text
   java -cp <pinned-fat-JAR> com.rsmaxwell.diaries.responder.migration.migration0028.Migration0028ReviewedFragments ...
   ```

   **Never** use `java -jar` and never restart/upgrade the permanent responder simply to obtain the migration CLI. The one-shot runner needs Java 25, production DB connectivity, `/config/responder.json`, `/data/files`, a new private output directory and **no** automatic service restart. The actual `docker compose run --no-deps` contract, volume bindings, output paths and restrictions need an explicitly reviewed production-ready command after Stage 0 and Stage 2 evidence; no routine service or image deployment.

2. Run `--mode validate-manifest` and the production `--mode dry-run` on the **writer-stopped** dataset. The CLI's `dry-run` writes only a private plan/receipt output, not database rows. Review the exact **71 conversions + one defer**, plan SHA-256, database identity, Files root, Marquee preservation and links. The plan must be generated from current production: the rehearsal plan is not transferable.
3. Independently review and install `migration0028/001-create-journal.sql` **only when separately approved**; its schema is a persistent database change, not a read-only CLI requirement. Do not skip the journal merely because `dry-run` succeeded.
4. Build the explicit `0028-apply-approval-v1` JSON containing the exact plan digest, reviewed input identity, production database+Files identities, owner/time, scope `PRODUCTION`, `writer_state=OFFLINE_WRITERS_STOPPED`, and accepted backup/rehearsal receipt hashes. **This file must be owner-approved**; CLI syntax and fields are not proof of actual isolation. `--mode apply` also requires `--permit-production-apply YES`.
5. After separate production-apply authorisation, invoke the one-shot CLI once, capture per-date transaction/journal evidence and run independent `--mode postflight`. The journal is the authority on an interrupted/resumed apply; inspect before retry, never blindly rerun. Keep writers stopped until complete validation and MQTT replay.

## Stage 5 — FUTURE: retained MQTT, client acceptance, rollback/reopen

- Reconcile the relevant **71 Fragment and 22 Marquee** retained MQTT objects with the committed DB state using the tested replay path and require independent retained-state comparison. Check three accepted representative UI examples and protected external links. The separate 0053-DEF editor-lock issue remains tracked.
- **Failure before DB mutation:** retain the fresh recovery snapshot and logs; restore original service/access state only after diagnosing the failed preflight.
- **Failure during/after apply:** stop; inspect SQL journal and last committed date. If rollback required, use the supported verified DB+Files restore path with the **new pinned immutable** snapshot. The existing `restore-dataset.sh` implements `preflight`, `prepare`, `apply`, `rollback`, `postflight` with separate confirmation tokens; those commands **mutate live data** and must be separately approved, and MQTT reconciliation must follow. Do not restore just the DB without considering matching Files and retained MQTT.
- Reopen ingress, direct SQL clients, backup timers and responder only after postflight accepted. Confirm original state precisely; observe runtime, Editor and Reader health; keep rollback point protected for the agreed period.
- Formal Step 3 and Step 4 closure **require accepted evidence and explicit feature closure**. Preserve the original JAR/checksum and source commit until the rollback window closes; then separately remove the disposable Java CLI/Gradle task in a reviewed responder commit. Keep DB journals and historical evidence until separately approved for removal.

## Operational execution gates

| Gate | Current state |
|---|---|
| Pinned Java source and fat JAR | PASS (prior accepted evidence) |
| Retained PostgreSQL restore | PASS (older point) |
| Java runtime contract | Checked by Stage 0, not yet accepted here |
| Exact current writer isolation | **OPEN** |
| New matching immutable DB+Files rollback snapshot on both hosts | **OPEN** |
| Owner acceptance of Steps 1 and 2 | **OPEN** |
| Final live production `dry-run` / source lock check | **OPEN** |
| Explicit separate approval for journal creation and `apply` | **OPEN** |
| Retained MQTT / GUI postflight | **OPEN** |
| Formal feature closure | **OPEN** |

**No part of this document, or success of the accompanying check, authorises a production apply.**
