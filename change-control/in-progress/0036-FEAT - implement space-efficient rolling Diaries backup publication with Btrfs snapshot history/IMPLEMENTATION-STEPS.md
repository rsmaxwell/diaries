# 0036-FEAT — IMPLEMENTATION-STEPS (revised 2026-10-15)

**Status:** IN PROGRESS — Steps 1–7 CLOSED; Step 8 Gates A–D CLOSED, Gate E OPEN (2026-10-18).  
**Authoritative design:** `DESIGN-DECISIONS.md` (revised fixed-working-copy decision). The original Step 2 hard-link/rolling-generation design and the experimental Step 3 increments are **SUPERSEDED**, not accepted for production.  
**Scope:** physical storage and synchronisation efficiency. **Schema-2 remains unchanged.**

| Step | Implementation | Evidence / exit gate |
|---|---|---|
| **1 — CLOSED** | Inherit accepted 0034/0035 baseline | Use existing 0034/0035 closure evidence; do not repeat Git commit, schedule, snapshots, receipts or checkpoint inventory. |
| **2 — REVISED; CLOSED** | Freeze fixed-working-copy design | Replace hard-link generation/transaction plan with one current verified schema-2 dataset on `pluto`, one Btrfs working dataset on `mars`, incremental `rsync --delete`, and existing 0035 snapshot/prune plus `mars`-initiated Btrfs send/receive to `backup`. Preserve original design freeze as superseded evidence. |
| **3 — CLOSED (2026-10-16)** | Implement fixed schema-2 dataset refresh on `pluto` | Reuse existing PostgreSQL logical dump and Files access; remove redundant full Files copies from the routine path. Use incremental rsync into a fixed location; preserve `database/`, `files/`, `verification/`, `dataset-manifest.json`, coherent capture, manifest identity and validation. A concurrent pull must never accept a half-refreshed dataset. Keep existing path available for rollback; do not require a new 0036 maintenance image. Test changed/add/delete and interrupted refresh. |
| **4 — CLOSED (2026-10-16)** | Adapt `mars` pull to reusable Btrfs working dataset | `mars` initiates rsync pull with `--delete` into the existing `@data` snapshot boundary; avoid fresh full-size generation copies. Maintain existing writer interlock, invalidate verified eligibility before mutation, independently verify complete schema-2 backup after transfer, and publish verified marker only after success. An interrupted pull must not create an eligible snapshot. No nested subvolumes outside the 0035 snapshot/send scope. |
| **5 — CLOSED (2026-10-16)** | Targeted 0035 snapshot/pruning compatibility | Confirm frequent scheduled snapshots of accepted working dataset, separate logical backup IDs from snapshot timestamps, and independent progressive pruning on `mars` and `backup`; use the existing snapshot manager without retuning policy. Check history/status/restore discovery for the fixed working location and historical snapshots. |
| **6 — CLOSED (2026-10-16)** | Targeted off-site push and historical compatibility | Preserve `mars → backup` Btrfs send/receive, protected send parents, receiver receipts, held checkpoints and historical schema-2 restore. Test only interfaces affected by the working-copy update; no repeat full 0034/0035 acceptance matrix. |
| **7** | Disposable end-to-end correctness and space-efficiency rehearsal | Two or more schema-2 backups including unchanged/changed/added/deleted files; verify incremental bytes/physical extent reuse without assuming Btrfs auto-deduplication. Exercise interrupted sync, stale marker, overlapping-job refusal, snapshot eligibility, historical restore and safe retry. Avoid altering production state. |
| **8** | Controlled cutover, unattended observation, legacy retirement and close-out | Deploy disabled by default; verify rollback path and known-good checkpoint; explicitly authorise cutover. Observe at least two unattended cycles and a successful off-site receipt. Legacy generation cleanup only by separate explicit approval after accepted restore/replication evidence. Document deployed 0036 Git commits, operations and limitations; mark feature CLOSED. |

## Inherited behaviour — do not reimplement

- 0033/0034: consistent schema-2 logical dataset, manifest and restore validation, historical recovery, mars-initiated verified pull and off-site Btrfs replication.
- 0035: timestamp-named Btrfs snapshot manager, frequent creation, progressive pruning on both hosts, verification eligibility, protected replication ancestry, schedule and retention controls.
- No inbound connectivity to the home network; off-site transfer remains a push initiated by `mars`.
- No new Docker application images or dedicated 0036 maintenance container required by this design; existing PostgreSQL capture may still use its existing container.

## Safety and migration rules

1. `rsync --delete` applies only to specifically scoped working-copy destinations; never to historical snapshots or inherited recovery media.
2. A schedule alone is not a mutual-exclusion guarantee: retain a lightweight existing service/interlock (`flock`/verified-marker protocol) to block overlapping source refresh, pull and snapshot/replication eligibility. Do **not** resurrect the complex generation-lock/acknowledgement architecture.
3. A mutable working copy may be partially updated after interruption: no verified marker, eligible snapshot or replication receipt is created until full schema-2 verification succeeds; last accepted read-only snapshot remains a recovery point.
4. Preserve schema-2 contents and logical dataset identities. The changed **physical layout is not a schema migration**.
5. Do not delete current legacy publication paths, generations or snapshot histories before approved cutover and rollback-window closure.
6. Treat previous experimental 0036 Step 3 code as a separate revert/reconciliation task. In particular, do not blindly overwrite pre-existing 0034 publisher code or remove historical restore helpers.
7. Reuse 0034/0035 closure evidence. Only new 0036 data-efficiency, cutover and changed-interface tests are required.

## Step 3 closure — accepted evidence (2026-10-16)

**Disposition: CLOSED for source implementation, disposable integration and source coordination. NOT production cutover.** See `evidence/Step 3/STEP-3-GATES-1-5-CLOSURE-20261016.md`.

- Gate 1: real PostgreSQL 18 disposable Compose `pg_dump` (custom/plain), `pg_restore --list`, restore into second database and two-row query: PASS on `pluto` (2026-10-15). The corrected rehearsal removed the incompatible PGDATA/tmpfs override.
- Gate 2: real schema-2 fixed-root writer/validator, explicit backup identity, corrupt Files and database detection, marker invalidation/reinstatement and incorrect root refusal: PASS on `mango` (2026-10-15).
- Gate 3: read-only `/mnt/nas-diaries` mounted on `pluto` using scoped Ansible tasks; `richard` directory traversal/enumeration and CIFS `ro,nosuid,nodev,noexec` confirmed: PASS (2026-10-16).
- Gate 4: guard/lock source regressions and existing 0034 pull tests PASS on `mango`; disposable guarded SSH/rsync from `mars` to `pluto`, marker rejection, writer exclusion, independent schema-2 validation and preserved previously received copy: PASS on `mars` (2026-10-16).
- Gate 5: these results reconciled into this change record. Production scheduled fixed capture is **still disabled**; existing publisher/symlink/timers, historical restore and snapshots are not retired or replaced.

**Step 4 dependency:** `mars` still needs its own incremental Btrfs working-copy implementation and controlled migration. The optional guarded source path has only disposable cross-host runtime verification. Do not treat Step 3 closure as approval to enable a production pull/capture or to remove legacy 0034 assets.

**Final cutover hygiene (Step 8):** remove or rename feature-numbered operational variables, services, mounts, deployed scripts and image names. Preserve identifiers in history, change-control evidence and regression tests only.

## Step 4 closure — accepted evidence (2026-10-16)

**Disposition: CLOSED for fixed receiver implementation and disposable verification; NOT production migration.** Source regressions on `mango` and real disposable Btrfs/SSH runtime on `mars` PASS, including initial, changed/added/deleted incremental receive, independent schema-2 verification, read-only historical snapshot, missing source acceptance marker, revoked eligibility and successful retry. The rehearsal exited 0. Manual privileged deletion of test subvolumes 20775 and 20774 succeeded; final subvolume listing under the rehearsal parent was empty. Initial fixture writer overwrite and non-privileged cleanup problems were harness-only and resolved/cleaned up. Accepted without further tests.

Controlled migration from the 0034 symlink to a plain fixed directory is **specified but not executed**; see `evidence/Step 4/STEP-4-CONTROLLED-MIGRATION-PLAN-20261016.md`. Step 8 must verify actual deployed paths, obtain approval, retain legacy generations/checkpoint and reversible symlink, use existing writer/marker contracts, and separately validate unattended cycles and off-site receipts. No production feature switches, published symlink or scheduler changed under Step 4. Proceed to Step 5.

## Step 5 closure — accepted evidence (2026-10-16)

**Disposition: CLOSED for targeted 0035 snapshot/pruning compatibility; NOT production activation.** The 0036 fixed-working snapshot compatibility regression PASSED on `mango`. The existing 0035 snapshot-manager regression also PASSED after correction of the `scripts/snapshots.sh` `mars|backup` launcher argument contract. Accepted coverage includes current/missing/stale/mismatched verification marker gating, backup identity, receiver interlock, read-only snapshot support and pruning scope isolation. Step 4's accepted real Btrfs immutability rehearsal is inherited, not repeated. No retention retuning or production manager algorithm change required.

See `evidence/Step 5/STEP-5-SNAPSHOT-PRUNING-COMPATIBILITY-CLOSURE-20261016.md`. No new production scheduled-pruning, live history/restore or off-site transfer test is claimed; inherited 0035 evidence applies, with changed off-site interfaces assigned to Step 6 and deployment/cutover to Step 8. Proceed to Step 6.

## Step 6 closure — accepted evidence (2026-10-16)

**Disposition: CLOSED for targeted offline 0034/0035 off-site and historical interoperability; NOT live revised-workflow replication or production activation.** Four regressions executed and PASSED on `mango` (2026-10-16): `verify-0036-offsite-history-compatibility.py`, `verify-native-btrfs-push.py`, `verify-replication-protection.py`, and `verify-diaries-backup-history.py`. Evidence establishes coexistence of historical symlink-generation and new fixed-directory schema-2 snapshots, UUID/receipt-based incremental ancestry and mismatch refusal, pin/protection fail-closed operation, and historical discovery conflict/unsafe-link checks.

The new 0036 regression used offline fixtures/mocked endpoint state. The existing 0034/0035 real-replication acceptance evidence remains inherited and is **not** represented as a new 0036 operational trial. No further Step 6 tests are requested. The integrated revised workflow remains Step 7; Step 8 exclusively owns production cutover, unattended observation and retirement. See `evidence/Step 6/STEP-6-OFFSITE-HISTORY-COMPATIBILITY-CLOSURE-20261016.md`.


**2026-10-16 Step 8 Gate B closure:** read-only rollback inventory of `pluto`, `mars`, `backup` accepted; verified off-site checkpoint `20261016-030037Z`, source/received UUID match, receiver receipt and committed Git baselines documented. **Gate B CLOSED; Gate C subsequently completed and formally CLOSED on 2026-10-16 (see Gate C closure record).** Step 8 and 0036-FEAT remain OPEN. See `evidence/Step 8/STEP-8-GATE-B-ROLLBACK-PREPARATION-20261016.md`. No production cutover authorised.

## Step 8 Gate B formal closure — 2026-10-16

**Gate B: CLOSED** for read-only rollback evidence, including current `pluto` and `mars` generation-backed publication symlinks, deployed service/unit hashes, `mars` read-only snapshot `20261016-030037Z`, matching `backup` received UUID, accepted incremental receiver receipt, and both Git committed baselines. See `evidence/Step 8/STEP-8-GATE-B-ROLLBACK-PREPARATION-20261016.md`. **Gate C subsequently CLOSED on 2026-10-16; Gate D/E and Step 8 remain OPEN**. Original symlinks, timers, generation data and replication unchanged.

## Step 8 Gate C — formal closure (2026-10-16)

**Gate C CLOSED — PASS.** Controlled production fixed capture on `pluto`, guarded fixed receive on `mars`, independently verified read-only Btrfs snapshot `20261016-153727Z` containing production backup `20261016-152236Z`, fixed-mode scheduler deployment and controlled activation all accepted. See [`evidence/Step 8/STEP-8-GATE-C-PRODUCTION-CUTOVER-CLOSURE-20261016.md`](evidence/Step%208/STEP-8-GATE-C-PRODUCTION-CUTOVER-CLOSURE-20261016.md) for the evidence and explicit exclusions. **Gate D and Gate E remain OPEN; Step 8 and 0036-FEAT are not closed.** Retain rollback assets.

## Step 8 Gate D — formal closure (2026-10-18)

**Gate D CLOSED — PASS.** Two genuine unattended daily production cycles (17 and 18 October) each completed scheduled `pluto` fixed capture, `mars` guarded verified receive, read-only 0035 Btrfs snapshot and accepted off-site incremental 0034 replication. Evidence reconciles distinct backup IDs, matching source/receiver manifest hashes, snapshot verification, UUID lineage, receiver receipts and successful timers. See [`evidence/Step 8/STEP-8-GATE-D-UNATTENDED-ACCEPTANCE-CLOSURE-20261018.md`](evidence/Step%208/STEP-8-GATE-D-UNATTENDED-ACCEPTANCE-CLOSURE-20261018.md). **Gate E remains OPEN; Step 8 and 0036-FEAT remain IN PROGRESS.** Retain rollback assets; no deletion or retirement authorised.


## Step 8 Gate E — retirement implementation (2026-10-18)

**IN PROGRESS — no runtime retirement or deletion executed.** Read-only inventory tool and approval-controlled sequencing prepared; see [`evidence/Step 8/STEP-8-GATE-E-RETIREMENT-PLAN-20261018.md`](evidence/Step%208/STEP-8-GATE-E-RETIREMENT-PLAN-20261018.md). Gate D CLOSED; Gate E, Step 8 and 0036-FEAT remain OPEN until actual deployment reconciliation, approvals and validation.
