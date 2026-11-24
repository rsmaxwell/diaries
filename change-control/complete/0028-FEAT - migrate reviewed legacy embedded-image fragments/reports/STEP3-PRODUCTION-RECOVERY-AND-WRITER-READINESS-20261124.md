# 0028-FEAT — Step 3 production recovery and writer-isolation readiness

**Prepared:** 2026-11-24 UTC  
**Status:** read-only collection tool delivered; live verification, formal gate decisions and production apply remain **OPEN**.

## Accepted prior evidence (do not repeat)

- Step 1: reviewed manifest with 72 occurrences, 71 approved `CONVERT_TO_IMAGE` and Fragment 1564 `DEFER`; 30 links and 22 existing Marquees preserved. Technical checks passed, but formal Step 1 acceptance is not yet recorded.
- Step 2: real Gradle/JUnit; isolated PostgreSQL 18 migration and date rollback/idempotence; 71+71 journals; MQTT replay 71/71, 22 Marquees; Reader and original scans; Editor sign-in, navigation, captions and three representative images; an original image hyperlink clicked successfully. The link destination requires an extra Google Street View navigation step, a content-quality observation rather than source drift.
- 0053-DEF tracks undo-to-original leaving the editor lock held; fragment-switch releases the lock. Not a blocker for reviewed IMAGE content, but must be separately scheduled.
- Step 3 source freshness: `20261124T095317Z-production-freshness` passed at 09:53:20 UTC, with 70/70 reviewed Files SHA-256 and zero observed Fragment locks. This is a *point-in-time* result, not a writer-stop confirmation.

## Source grounding and operational constraints

This audit is based on uploaded `diaries-sources-20261124-090430.zip` and `playbook-sources-20261124-084655.zip`, not live Git status or a live inventory dump.

- The permanent production role includes `backup-dataset.sh`, `restore-dataset.sh`, `complete-dataset-publisher.py` and PostgreSQL/Docker tools. `backup-dataset.sh` without parameters **creates** backup media; `backup-dataset.sh publish` captures/publishes backup media. **Neither is executed by this audit.**
- `restore-dataset.sh preflight diaries-backup` checks the recovery source without running a restore, but may hash a complete dataset; reserve this more expensive check for the exact recovery-source acceptance decision. Never run `restore-dataset.sh prepare/apply/rollback` as part of a passive audit.
- The deployed `diaries-backup-status` output on `mars` and `backup` describes *retained manifest identity*, not a proof that full files can still be restored. It can be healthy with an untested restoration path. Snapshot timestamps are not backup capture timestamps.
- The production Compose template exposes PostgreSQL using a host port (default 5433); it also includes browser client, Reader, responder and MQTT services. Stopping only `diaries-responder` for a backup **does not by itself verify absence of all writers**. Do not reuse the general `stop.sh` blindly: it tears down the stack, including the database required by the migration.
- Playbooks role defaults show a responder image tag, but actual production tags and digests can differ due to inventory overrides. Use the runtime `docker inspect` evidence; the 0028 Java CLI exists in the local source checkout, and must be deliberately packaged or run offline against production data. Do not assume the running production responder image includes the migration CLI.

## Read-only inventory package

`tools/audit-0028-step3-recovery-and-writers.sh`, run on **Windows PC — Cygwin from the Diaries parent root**, connects to `pluto`, `mars` and `backup` over SSH. It captures:

- Live production image identities, container states and port bindings, Compose service names, availability of restore/backup tools, published path metadata and backup timer state; PostgreSQL connection-state counts only (no queries or credentials).
- Source and receiver retained-backup manifest status and relevant systemd timer listings.
- Private `PROBE-STATUS.tsv`, per-host logs and `READINESS-RESULT.json` in `evidence/Step 3/private/<timestamp>-recovery-writer-inventory/`.

A successful collection means only **the probes were collected**. It never signifies a verified restore, a fresh production recovery point, writer isolation, approval or compatibility of the currently deployed image. If a host cannot be reached, the tool reports an incomplete collection and exits nonzero. All outputs are in the feature's ignored private evidence directory.

## Remaining release gates (not automatically accepted by this package)

1. **Formal Step 1 acceptance and Step 2 evidence sign-off.** Record owner decision; do not silently infer it from continuation requests.
2. **Verified matching recovery point:** obtain a post-writer-stop backup including PostgreSQL and Files, record the exact backup ID, pair identity, checksums and all locations. Verify source and receiver copies. A database-only dump is insufficient for an image catalogue/Files recovery claim. Use an accepted restore rehearsal if it proves this exact recovery mechanism, otherwise do one isolated full dataset restore test; don't repeat the already accepted migration rehearsal merely to create logs.
3. **Release artefact and runtime compatibility:** record parent/submodule revisions and SHA of approved Java CLI/JAR, exact manifest/plan approval hashes, current production container image digests and JDK/DB compatibility. The migration CLI is not a normal responder-startup path.
4. **Writer isolation:** review a reversible maintenance window that blocks browser sessions, MQTT RPC publishers and database writers. Confirm stopped responder + broker/client routing as appropriate while **PostgreSQL remains running**, and positively measure DB connections and lock state. Record the stop/run/resume sequence and safe rollback point. Do not rely on a 09:53 zero-lock observation alone.
5. **Final preflight:** after writers are stopped, rerun the already validated fresh-source comparator and refuse source drift. Bind the resulting plan hash/approval to the final database and Files identity.
6. **Separate explicit production approval:** require owner acceptance of exact run, manifest, approved recovery point, downtime and rollback procedure before any `apply`. Postflight, responder MQTT replay, Reader/Editor checks and controlled writer reopening are required before declaring success.

## Current decision

**Step 3 remains OPEN.** This inventory does not stop writers, snapshot or prune anything, apply SQL, publish MQTT or touch production application runtime. Do not run a migration based solely on the receipt.
