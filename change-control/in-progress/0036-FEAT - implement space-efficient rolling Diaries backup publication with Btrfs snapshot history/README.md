# 0036-FEAT — Space-efficient Diaries backup using fixed schema-2 working datasets

**Status:** IN PROGRESS — Steps 1–7 CLOSED; Step 8 Gates A–D CLOSED, Gate E OPEN (2026-10-18).  
**Dependencies:** 0034-FEAT and 0035-FEAT CLOSED; inherit their closure evidence.  
**Source ownership:** Playbooks implements production operations; Diaries holds these change-control records.

## Objective

Avoid copying an entire unchanged photograph collection into fresh full-size backup-generation directories on every cycle. Retain **exactly the existing schema-2 logical dataset layout**, but maintain one current working copy on `pluto` (ext4) and one on `mars` (Btrfs) using incremental `rsync --delete`. 0035 creates frequent read-only timestamped Btrfs snapshots on `mars`; 0034 pushes them from `mars` to `backup` with Btrfs send/receive. Existing progressive pruning on both Btrfs hosts, protected replication ancestry, receipts and restore rules remain intact.

```text
pluto:  current verified schema-2 working dataset
              |
              | mars-initiated rsync pull --delete
              v
mars:   current schema-2 Btrfs working dataset
              |
              | 0035 timestamp snapshots and local pruning
              v
mars:   historical read-only snapshots
              |
              | mars-initiated Btrfs send/receive push
              v
backup: historical received snapshots + independent pruning
```

The logical dataset remains:

```text
diaries-backup/
  database/
  files/
  verification/
  dataset-manifest.json
```

PostgreSQL is captured consistently using the existing logical dump mechanism, **not** by rsyncing a live database directory. Snapshot times and backup IDs are distinct. Frequent snapshots are legitimate because unchanged extents are shared under Btrfs COW; no Btrfs automatic deduplication is assumed.

## Revised design / superseded development

The previous Step 2 decision, preserved in `evidence/Step 2/STEP-2-DESIGN-FREEZE-20261015.md`, specified immutable published generations, hard-link reuse, reflink candidates, receiver acknowledgements and extra Docker maintenance tooling. That design is **superseded** by `DESIGN-DECISIONS.md` (revised 2026-10-15). Experimental 0036 Step 3 work already applied to Playbooks is not approved for production and must be reconciled against the original 0034 implementation before proceeding. Do not remove legacy publication/restore code blindly.

No 0036 production feature flag should be enabled based on the experimental work. No new application Docker images are required at this design stage.

## Compatibility and safety

Retain the existing schema-2 verification, history/status/restore behaviour, protected replication parents, checkpoint holds, receiver receipts, snapshot manager/pruning and established mars-initiated push. Lightweight job overlap prevention and verification-marker gating remain necessary: schedules alone cannot prevent a partial working copy from being consumed.

Use `IMPLEMENTATION-STEPS.md` for the revised eight-step execution plan and `evidence/Step 2/STEP-2-REVISION-20261015.md` for the formal change record. Reuse 0034/0035 closure evidence and test only changed interfaces. Historical backups and legacy generations are retired only with explicit approval after successful migration and rollback acceptance.

## Step 3 — formally closed (2026-10-16)

Step 3's fixed schema-2 capture implementation and pre-cutover evidence are accepted: disposable PostgreSQL dump/restore, real manifest writer/validator, live `pluto` read-only host NAS mount, and guarded disposable `mars → pluto` transfer. Gate-level results and boundaries are in `evidence/Step 3/STEP-3-GATES-1-5-CLOSURE-20261016.md`.

**Operational state is unchanged:** fixed capture is disabled; the legacy `diaries-backup` publication, existing timer and 0034/0035 contracts remain in operation. Step 4 is next and must implement incremental reception into the Btrfs working dataset on `mars`. Step 8 will reconcile temporary 0036-prefixed production configuration and superseded experimental code before cutover/closure.

## Step 4 — formally closed (2026-10-16)

The opt-in `mars` fixed receiver passed source regressions and the complete disposable real-Btrfs rehearsal: guarded initial pull, incremental changed/added/deleted Files, unchanged read-only snapshot, marker refusal on source failure, and accepted retry. Operator manually removed both disposable Btrfs subvolumes and verified no remnants. **No further Step 4 tests required.**

See `evidence/Step 4/STEP-4-RECEIVER-REHEARSAL-AND-CLOSURE-20261016.md` and `STEP-4-CONTROLLED-MIGRATION-PLAN-20261016.md`. The latter is a **future Step 8 migration/rollback procedure**, not an executed cutover. Existing 0034 publication symlink, 0035 snapshots, timer and off-site workflow are retained; fixed production mode stays disabled. Proceed to Step 5.

## Step 5 — formally closed (2026-10-16)

The targeted fixed-working-copy/0035 snapshot-pruning compatibility regression and the existing 0035 snapshot-manager regression both PASSED on `mango`; the latter required a narrow correction to the `scripts/snapshots.sh` host argument contract. Accepted checks cover verification eligibility/manifest identity, receiver-vs-snapshot locking, snapshot namespace and pruning scope. The earlier real-Btrfs Step 4 snapshot immutability result is inherited. **No further Step 5 tests or manager algorithm changes required.**

See `evidence/Step 5/STEP-5-SNAPSHOT-PRUNING-COMPATIBILITY-CLOSURE-20261016.md`. Production snapshot schedules, retention, 0034 publication symlink, off-site flow and cutover remain unchanged. Proceed to Step 6.

## Step 6 — formally closed (2026-10-16)

The targeted 0036 off-site/historical compatibility regression and three inherited 0034/0035 regressions all **PASSED on `mango`** (operator evidence 2026-10-16). Confirmed mixed historical generation-symlink and future fixed-directory snapshot discovery, schema-2 historical references, verified UUID-based incremental parent choice, parent-receipt rejection, protected replication ancestry and history identity/symlink guards. **No production sender, receiver, history or retention algorithm changes are needed.**

See `evidence/Step 6/STEP-6-OFFSITE-HISTORY-COMPATIBILITY-CLOSURE-20261016.md`. This is a targeted **offline** contract closure, not a claim of a new live off-site push, restore or unattended operation. Existing 0034/0035 accepted operational evidence is inherited. Actual revised-workflow integration remains Step 7; production migration, scheduling and legacy retirement remain Step 8. Proceed to Step 7.


**2026-10-16 Step 8 Gate B closure:** read-only rollback inventory of `pluto`, `mars`, `backup` accepted; verified off-site checkpoint `20261016-030037Z`, source/received UUID match, receiver receipt and committed Git baselines documented. **Gate B CLOSED; Gate C subsequently completed and formally CLOSED on 2026-10-16 (see Gate C closure record).** Step 8 and 0036-FEAT remain OPEN. See `evidence/Step 8/STEP-8-GATE-B-ROLLBACK-PREPARATION-20261016.md`. No production cutover authorised.

**Gate B (2026-10-16): CLOSED.** Verified `mars`/`backup` rollback checkpoint `20261016-030037Z`, matching Btrfs received UUID and receiver receipt. Gate C subsequently completed and formally CLOSED on 2026-10-16 (see Gate C closure record).

## Step 8 Gate C — formal closure (2026-10-16)

**Gate C CLOSED — PASS.** Controlled production fixed capture on `pluto`, guarded fixed receive on `mars`, independently verified read-only Btrfs snapshot `20261016-153727Z` containing production backup `20261016-152236Z`, fixed-mode scheduler deployment and controlled activation all accepted. See [`evidence/Step 8/STEP-8-GATE-C-PRODUCTION-CUTOVER-CLOSURE-20261016.md`](evidence/Step%208/STEP-8-GATE-C-PRODUCTION-CUTOVER-CLOSURE-20261016.md) for the evidence and explicit exclusions. **Gate D and Gate E remain OPEN; Step 8 and 0036-FEAT are not closed.** Retain rollback assets.

## Step 8 Gate D — formal closure (2026-10-18)

**Gate D CLOSED — PASS.** Two genuine unattended daily production cycles (17 and 18 October) each completed scheduled `pluto` fixed capture, `mars` guarded verified receive, read-only 0035 Btrfs snapshot and accepted off-site incremental 0034 replication. Evidence reconciles distinct backup IDs, matching source/receiver manifest hashes, snapshot verification, UUID lineage, receiver receipts and successful timers. See [`evidence/Step 8/STEP-8-GATE-D-UNATTENDED-ACCEPTANCE-CLOSURE-20261018.md`](evidence/Step%208/STEP-8-GATE-D-UNATTENDED-ACCEPTANCE-CLOSURE-20261018.md). **Gate E remains OPEN; Step 8 and 0036-FEAT remain IN PROGRESS.** Retain rollback assets; no deletion or retirement authorised.


## Step 8 Gate E — retirement implementation (2026-10-18)

**IN PROGRESS — no runtime retirement or deletion executed.** Read-only inventory tool and approval-controlled sequencing prepared; see [`evidence/Step 8/STEP-8-GATE-E-RETIREMENT-PLAN-20261018.md`](evidence/Step%208/STEP-8-GATE-E-RETIREMENT-PLAN-20261018.md). Gate D CLOSED; Gate E, Step 8 and 0036-FEAT remain OPEN until actual deployment reconciliation, approvals and validation.
