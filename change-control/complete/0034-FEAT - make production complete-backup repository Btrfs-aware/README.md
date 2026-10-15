# 0034-FEAT — Publish a stable production complete-backup dataset for snapshot-backed replication

> **ACTIVE DESIGN DECISION — 2026-10-12: MARS-INITIATED NATIVE BTRFS PUSH**
>
> The previously documented `backup`-initiated native pull is **superseded for future replication** by `mars`-initiated Btrfs send/SSH/receive to `backup`. Historical pull experiments, signed-off steps, existing scripts and acceptance receipts remain evidence; this documentation update changes **no executable code, live SSH settings, systemd timers or transfers**. The currently running full pull of `20261012-100003Z` must complete and be verified as the common baseline before push migration. See `evidence/Step 10/PUSH-ARCHITECTURE-DECISION-20261012.md`.
>

> **ACTIVE DESIGN — 2026-10-11: NATIVE BTRFS REPLICATION SUPERSEDES RSYNC RECEIVER**
>
> This revision supersedes only the unfinished `mars` → `backup` receiving/replication design of 0034 Step 10 and associated 0035 acceptance work. Steps 1–9 of 0034 are historically CLOSED and their evidence remains valid. It does not claim that native replication has been implemented, migrated or tested. The existing in-progress `whole-backup-pull` rsync run is **not** a seed for incremental Btrfs send/receive.

## Current approved topology and scope (2026-10-11)

```text
pluto -- complete schema-2 production backup (fixed published directory)
   | existing verified pull / publication contract, unchanged
   v
mars -- whole-backup tree in /media/usb/@data/backup (as today)
   | native read-only snapshots of the containing Btrfs subvolume
   | btrfs send (full once; later incremental with -p/optional -c)
   | SSH stream from mars to backup, initiated by backup under explicit controls
   v
backup -- btrfs receive into dedicated, isolated receive repository
        native received read-only snapshots, independent verification/retention
        never replace or delete /@data/backup
```

The Btrfs transfer has **no Diaries-specific dataset selector or marker prerequisite**. It replicates the entire chosen source subvolume, which happens to contain the complete backup tree and therefore Diaries backup generations. Diaries schema-2 validation remains the responsibility of backup publication, restore and the *separate* read-only history/verification utility, not the generic replication transport.

**Source unchanged:** Preserve the current `mars` whole-backup source, its `/media/usb/@data/backup` layout, 0034 fixed `pluto` publication, and the 0035 timestamp-named read-only source snapshots. Do **not** silently convert `backup/` to its own subvolume, rename datasets, or discard other contents of `@data`. Because Btrfs send operates on complete subvolumes, the first baseline may include unrelated `@data` content: inventory and capacity-estimate the full sendable source snapshot before running it. If that footprint is unacceptable, defer a topology change to an explicit separate design decision.

**Migration:** The existing rsync-populated `/@data/diaries-mars-replica` directory is not a valid native incremental parent. Retain it as a separately identified, unverified-for-native-receive staging copy until the operator chooses safe removal; do not overlay it with `btrfs receive`, and do not point `--delete` at the historical `/@data/backup`. Create a **fresh, full `btrfs send`/`btrfs receive` baseline** in a dedicated destination, validate it, then send only later read-only snapshots relative to an unchanged common parent. Never alter received snapshots in place or falsify snapshot identity.

**Transfer privilege and safety:** The transport may run SSH as `richard`, but local and remote Btrfs send/receive/subvolume operations normally need privileged, narrowly authorised helpers (not root SSH). Provision a protected receiver destination and stage each receive transaction; fail closed on a partial received subvolume, lost connection, unavailable matching parent, insufficient space, invalid source, or conflicting writer. Preserve immutable source snapshots and the last accepted destination snapshots. Do not reuse the rsync writer-marker contract as if it made a Btrfs stream verified. Define a new receive-completion receipt containing source subvolume/snapshot IDs, parent relation, received UUID, target path, outcome and timestamp, stored outside received read-only subvolumes.

**Scheduling:** Keep both the current rsync transfer and any Btrfs send/receive jobs unscheduled until migration acceptance. On cutover explicitly stop the legacy `mars` push and the new `backup` rsync pull, audit all timers/cron, then activate *one* Btrfs receiver job with rollback. The native snapshot timers on `backup` remain disabled until their independent 0035 acceptance gate.

**Operator utilities:** A read-only Diaries backup locator/history command must be installed on **both `mars` and `pluto`**; it reports each backup ID and the available containing snapshot paths where snapshots exist, and handles the live published dataset where snapshot media are absent. A timestamp snapshot prune/retention utility must also be available on **both `mars` and `pluto`**, but it may prune only validated native timestamp-named snapshots on each host and must refuse unmanaged paths or non-Btrfs filesystems. On ext4 `pluto`, it should clearly report unsupported/no native snapshots rather than attempting to prune directories. `backup` additionally needs native received-snapshot retention and inspection because it is the remote receiver. No utility performs automatic destructive restore.

## Design invariants and acceptance gates (2026-10-11)

- Source and parent snapshots used for incremental sends must be read-only, remain unchanged on both hosts and have a demonstrably valid received-UUID/parent relationship. Record `btrfs subvolume show`, UUIDs, received UUIDs, and source/destination filesystem identifiers.
- Establish a full native baseline; prove subsequent incremental send (`btrfs send -p`) transmits and reconstructs a later source snapshot. Optional clone-source optimization is a separate measured choice.
- Verify receive tree completeness, matching source snapshot data, read-only state, backup-history visibility and a disposable restore of a Diaries schema-2 dataset *as an application-level acceptance test*, without embedding Diaries semantics in the transfer code.
- Demonstrate interrupted full/incremental receive isolation and recovery, missing/retained-parent behavior, lock exclusion, disk-pressure behavior, and retention coordination so no required incremental parent is pruned prematurely.
- Keep `/@data/backup`, existing Snapper snapshots, and already closed feature evidence unchanged; run staged activation with a reversible rollback to the last confirmed backup mechanism.


---

## Earlier design and completed-step record (historical; superseded where inconsistent with 2026-10-11)


## Type / status / origin

Feature — **In progress**. Opened 2026-10-07. Architecture revised 2026-10-08 after confirming the actual `pluto` → `mars` → `backup` replication topology. The original title (“make production complete-backup repository Btrfs-aware”) is retained in the change-control directory for continuity; the revised responsibility is **source publication and safe replication**, not on-`pluto` reflink optimisation.

## Current position (as at design revision)

- **0033** delivered the frozen schema-2 complete-dataset manifest, PostgreSQL custom+SQL dumps, durable Files inventory, quiescence, validation and recoverable restore. Existing timestamp-ID backup directories on `pluto` are valid historical recovery media.
- **0034 Step 1** is closed (baseline frozen). **Step 2** is closed (explicit Playbooks repository/restore root and mode contract, regression and `pluto` preflight). Keep its historical evidence and existing deployed configuration.
- **0034 Step 3** code and six local regression suites passed. Production preflight on `pluto` identified `/` as **ext4**, selected `full-copy` from `auto`, with no workspace or writer interruption. The **original Step 3 acceptance criterion has been met**, but its on-`pluto` Btrfs strategy objective is now **superseded**; keep code and evidence until a deliberate compatibility retirement step, not as the basis of future implementation.
- Original Steps 4–12 (reflink base discovery, recursive cloning, Btrfs provisioning on `pluto`, etc.) are **cancelled/superseded**, not completed. The revised `IMPLEMENTATION-STEPS.md` starts from this exact state.
- Playbooks 0035 already has a prepared shared native timestamp-snapshot manager, **not yet proven on live `mars`/`backup`**. 0034 must not enable new snapshot timers or alter Snapper itself.

## Topology and ownership

```text
pluto (ext4)                         mars (Btrfs)                     backup (Btrfs)
current/diaries-backup/  --rsync-->  writable whole-backup mirror  --> writable whole-backup mirror
  schema-2 dataset                   verified, then 0035 snapshot      verified, then 0035 snapshot
```

- **0034 owns** creating, validating, atomically publishing and exposing the stable `diaries-backup/` dataset on `pluto`, plus a replication-safe source contract and validation tools callable on receivers.
- **0035 owns** Btrfs subvolume boundaries, whole-backup snapshot creation, verified-replication hooks, timed retention, legacy Snapper migration and deduplicated Diaries backup-history discovery on `mars`/`backup`.
- **0033 remains authoritative** for logical backup content and schema-2 validation. No new manifest schema or implicit filesystem-dedup claims.
- Synology NAS remains independent and managed by DSM; it provides the live Files source, **not** the complete-backup repository.

## Fixed published dataset contract

```text
diaries-backup/
├── database/
│   ├── diaries.dump
│   └── diaries.sql
├── files/
├── verification/
└── dataset-manifest.json
```

Exactly one **published current dataset** exists at the fixed name `diaries-backup`. The schema-2 `backupId` and `logicalDataset` stay in `dataset-manifest.json` and remain unique across generations. The manifest, verification artefacts and content retain their frozen 0033 semantics. No timestamp is baked into the published directory name.

A complete dataset must be assembled in a private sibling staging directory, verified end-to-end, then published using a **real atomic generation switch** with an explicitly documented filesystem and reader model. A pair of non-atomic `mv` operations is **not** sufficient. The implementation must establish whether a stable symlink with atomic `rename(2)`, an equivalent generation-pointer strategy, or a coordinated exclusive handover is supported by the receiving rsync setup; a reader must never see half-old/half-new content. The logical stable path presented to the replicator must remain `diaries-backup/`.

## Coordination and durability invariants

1. A source-side backup producer must not mutate or delete the published generation while `rsync` is reading it. Use a common producer/consumer lock **or** immutable generations with explicit lifetime/reader leases. Atomic pointer switching *alone* does not protect a reader that is already traversing the previous tree.
2. Publish only after successful database+Files capture, independent source verification and schema-2 validation. On failure preserve the last known good published generation.
3. The receiver must **not** snapshot a partially synced mirror. Sync to a safe receiving state, verify `dataset-manifest.json`, logical dataset, backup identity, database components and Files contents with schema-2 verification, then hand off a coherent mirror generation to 0035.
4. An rsync run may fail or race with a source generation change; such a run must fail validation and leave the last good receiving snapshot untouched. Receiver-side completion must be signalled explicitly, never inferred merely from a zero rsync exit code.
5. `rsync` should avoid `--inplace` / `--append` for snapshot-backed trees, preserve metadata consistently, and ensure removed Files do not persist. Destination update policy (`--delete` or equivalent) must be restricted to the *managed Diaries mirror subtree*, not other backed-up content.
6. The whole-backup snapshot covers **other important data as well as Diaries**. Cross-dataset logical atomicity is not automatic: 0035 must define a snapshot/backup-job coordination barrier. A snapshot with a repeated Diaries `backupId` is normal.
7. Existing completed timestamp-ID directories remain intact and independently restorable until an explicit migration/retention policy is proved. Do not auto-remove legacy media.
8. Restore from fixed current data and from a historical whole-backup snapshot must continue to use the 0033 validation and explicit destructive-confirmation safeguards. Do not attempt a destructive production restore as a routine acceptance test.

## Configuration and compatibility

Step 2 introduced `DIARIES_COMPLETE_BACKUP_REPOSITORY_ROOT`, `DIARIES_COMPLETE_RESTORE_STATE_ROOT`, and `DIARIES_COMPLETE_BACKUP_STORAGE_MODE` (`auto`, `required-btrfs`, `full-copy`). These are **existing deployed contracts**, not to be silently reinterpreted. The new publication root/path and replication handoff must be explicitly configured through Playbooks with migration checks. On ext4, current `auto` selects `full-copy`. The on-`pluto` `required-btrfs` path must not be used for the new architecture; choose an explicit retirement/deprecation plan and test backward compatibility before removing it. Avoid reusing the existing repository root for a different directory meaning without a deliberate migration.

## Implementation and acceptance

Follow `IMPLEMENTATION-STEPS.md` (revised steps beginning with design freeze / transition). At close-out prove: stable fixed directory, unchanged schema-2 validation, stable backup IDs, safe reader coordination, failure rollback, two successive real backups, verified `pluto` → `mars` replication, unchanged Files sharing through 0035 snapshots, remote `backup` verification and restore rehearsal from a snapshot. The **0034 source-publication portion** can be separately accepted before 0035 is deployed; full end-to-end integration remains a cross-feature gate.

## Evidence handling

Do not rewrite or delete Steps 1–3 evidence. Original pre-redesign README and implementation plan are archived under `evidence/2026-10-08-PRE-REDESIGN/`. Preserve runtime `pluto` Step 3 preflight evidence when formally recording the supersession. This documentation revision **does not deploy code**, close a pending step, migrate stored backup data, or start snapshot timers.

## Step 4 design close-out (2026-10-08)

Step 4 is **closed as a design-contract step**. See `evidence/Step 4/PUBLICATION-AND-REPLICATION-CONTRACT.md` for the chosen immutable-generation, atomically replaced stable symlink, pinned-rsync-reader and shared `flock` model; `evidence/Step 4/STEP-3-SUPERSESSION.md` records the historical Step 3 results without implying Btrfs copying was deployed. The proposed published root is separate from the legacy repository and restore state and is not yet deployed. Actual inter-host rsync configurations remain a mandatory discovery gate. **Step 5 is next.**

## Step 5 isolated publisher status (2026-10-08)

An opt-in publisher of already-completed schema-2 generations and a disposable concurrent-reader regression are implemented in Playbooks source; production capture and rsync are **not yet integrated**. See `evidence/Step 5/README.md`.

## 0034 Step 6 source integration status (2026-10-09)

`mars`-initiated opt-in SSH rsync pull implementation prepared in Playbooks; **disabled by default**, not production-deployed. The receiver verifies schema-2 and publishes only verified generations, reporting `snapshotEligible=false`. Live SSH, fixed-source publication and receiving directory remain verification gates. See `evidence/Step 6/MARS-PULL-INTEGRATION.md`.

## Step 6 close-out — 2026-10-09

The manually invoked `mars`-initiated pull of the verified `pluto` backup `20261007-145013Z` succeeded; 89 durable Files were verified and `mars` published the fixed `diaries-backup` path. **Step 6 closed for the manual pilot, not for scheduled operation.** See `evidence/Step 6/CLOSEOUT.md`. A safety audit of existing `mars` rsync `--delete` scopes and permanent `local-backup` role ownership reconciliation are **required before automatic activation**, and 0035 snapshot eligibility remains false.

## Step 7 — CLOSED (2026-10-09)

Historical restore compatibility is implemented in Playbooks source. `restore-dataset.sh` can now select a legacy `<backup-id>`, the stable `diaries-backup` publication, or an explicit completed schema-2 directory such as a path later returned by 0035 snapshot history. Prepared restores pin the exact resolved source for later apply/rollback/postflight, preventing a moving fixed pointer from changing the selected media. The new disposable compatibility regression and existing recovery-contract suites pass. See `evidence/Step 7/README.md`. **CLOSED:** six `mango` suites passed; `pluto` deployment passed; all three non-destructive production source preflights passed. Negative confirmation and source-pinning guards are covered by disposable tests; no destructive production restore was performed. See `evidence/Step 7/CLOSEOUT.md`.


## Step 8 — CLOSED (2026-10-09)

Playbooks configuration, permanent regression and operator guidance were closed after the eleven-suite `mango` regression passed. The separate stable published-root contract, normal-user opt-in `mars` pull ownership, delete-scope guard and restore compatibility are accepted in source. Production path migration was deliberately deferred to Step 9. See `evidence/Step 8/CLOSEOUT.md`.

## Step 9 — CLOSED (2026-10-09)

Controlled `pluto` deployment, non-destructive predeploy preservation, first full schema-2 stable publication, symlink-preflight regression fix/redeployment, post-publication preservation verification, and real live `rsync` shared-lock/publisher exclusive-lock acceptance all passed. The stable pointer now names `20261009-154847Z`; historical `20261007-145013Z` and first production `20261009-153243Z` remain retained. No cleanup, destructive restore, or Docker image rebuild was required. See `evidence/Step 9/CLOSEOUT.md` and runtime evidence transcripts. **0034-FEAT remains open for Steps 10–11.**


## Step 10 ownership decision — 2026-10-10 (implementation pending)

The `backup` pull/receiving repository ownership model is revised following successful `richard@backup` → `richard@mars` public-key SSH testing. **This records an agreed target design, not a deployed change or Step 10 acceptance.**

- The isolated receiving root `/@data/diaries-mars-replica` and its managed writable children are provisioned by privileged Playbooks tasks but **owned by `richard`** (configurable `backup_pull_user`, default `richard`), with restrictive permissions. Only this isolated tree is in scope; existing `/@data/backup` (about 325 GB of unrelated/historical data) must remain untouched. `rsync --delete` must not escape the isolated managed subtree.
- Run `whole-backup-pull` and its SSH/rsync, lock, schema-2 verification, and verified-marker publication as **`richard`**, not via `sudo`. The SSH connection uses `richard`'s existing `mars` client alias, SSH key and configured port. Do not install or require root's outbound SSH keys/config on `backup`.
- Keep privileged Btrfs subvolume/snapshot creation, retention/pruning, systemd management and privileged provisioning in the 0035 manager/Playbooks (`root`). A root-operated snapshot manager may read the `richard`-owned verified marker but may not infer verification solely from ownership or an rsync exit code.
- The pull and snapshot manager must coordinate through the **same persistent lock inode**, e.g. `/@data/diaries-mars-replica/.btrfs-snapshot-writer.lock`, using compatible `flock` discipline. Provision its ownership/mode explicitly; never truncate, replace, unlink or rsync-delete it. Ensure both identities can open/lock it, and test contention between a `richard` pull and root snapshot creation. If a destination-tree rsync can touch the lock or marker, exclude/protect those receiver-owned control files from sync.
- Adapt non-root rsync flags to preserve required timestamps/content/permissions **without requiring privileged owner/group restoration**; independently verify complete source/destination dataset identities and Files before publishing an eligibility marker. Verify `richard` can create temp files, atomically publish the marker, and replace managed receiving content.
- **Open source-access gate:** `richard@backup` can authenticate to `mars`, but the probe of `/media/usb/@snapshots/@data/20261009-170001Z/backup/.diaries-snapshot-verified.json` did not report readable. Establish existence/path and traversal/read permissions of the pinned immutable snapshot and verify access as `richard`; change only narrowly scoped permissions/ACLs as needed. Do not claim the first pull is ready until this passes.
- Keep `backup` native snapshot timers disabled and historical Snapper jobs untouched until the first independently verified receive, shared-lock test and snapshot-history gate pass. No real pull, ownership migration or timer activation is evidenced by this documentation change.

**Next implementation gate:** update `remote-backup` directory provisioning and `whole-backup-pull` execution/rsync/locking assumptions, validate source readability, deploy safely, run unprivileged preflight then a controlled pull, and only then test 0035 snapshots on `backup`. The original schema-2 contract and `mars`/`pluto` steps remain unchanged.


## 2026-10-12 — Agreed push revision (authoritative for future Step 10 work)

The accepted future data path is `mars` (source/orchestrator, outbound SSH) → `backup` (validated receiver). `mars` connects as the normal SSH identity `richard` to `10.254.22.1` on port `39263`, using the existing tested authentication and host-key verification; the address/port are **observed connectivity**, not yet an installed replication transport configuration. No inbound UniFi firewall port is required. Btrfs streams use narrow privileged endpoints, not remote unrestricted root SSH. The previous `backup`-initiated pull is a historical implementation and rollback option, **not** the target scheduled workflow.

The in-flight full receive of `20261012-100003Z`, source UUID `7ad1f171-d1c7-0545-82a1-52e84adac979`, must run to completion untouched. After receipt, read-only status, UUID and filesystem identities, journal/receipt and protection state are verified, it becomes the first **push-compatible common parent**. Do not assume acceptance while it is still streaming. Subsequent first push is an **incremental** send with `-p` only after explicit common-parent validation; never silently full-reseed on missing parent. Preserve `20261009-170001Z` at receiver as historical data and preserve `/@data/backup` entirely.

The source-side push orchestration holds a single transaction lock and protects the candidate **before** starting the send; holds its accepted parent until verified child acceptance; stages receiver data safely; performs receive-side postchecks/receipt publication; confirms the receipt independently on `mars`; then atomically advances the protected common parent. Any error leaves the old parent pinned, keeps an unaccepted candidate appropriately protected for recovery, and must not record success. Receiver receipt ownership and validation remain receiver-controlled.

Scheduling remains **opt-in/disabled** through testing and cutover. Do not enable `btrfs-snapshot-prune.timer` on `mars` until live parent-preservation and lifecycle testing passes. The legacy rsync destination and its stopped jobs must not be reactivated by this revision. Refer to the Step 10 push decision for complete migration gates.

## 2026-10-13 — Step 10.P9 acceptance (CLOSED)

The narrow `roles/remote-backup/` pull-retirement cleanup passed source regressions, Ansible deploy on `mars`/`backup`, on-host legacy-helper absence and a post-deployment incremental preflight. The pre-cleanup checkpoint `20261013-171228Z` was received on `backup` and remains held independently of replication parent `20261013-180016Z` on `mars`. Evidence: `evidence/Step 10/STEP-10.P9-FINAL-CLEANUP-ACCEPTANCE-20261013.md`. Commit `5d3b2b3` was pushed but includes other ongoing work due to `git add -A`; see the evidence for the precise scope qualification. This **does not** by itself close the whole feature.

## 2026-10-14 — Step 11.3 disposable off-site recovery rehearsal: CLOSED

Gates A–D passed against published schema-2 generation `20261009-154847Z` held in off-site Btrfs snapshot `20261013-171228Z`. Recovery on `mars` used an isolated PostgreSQL 18 container and scratch Files, verified 89 Files and Image catalogue hashes, and removed each disposable container. The `mars` history CLI remains blocked by `verification.required=false`; configuration review is deferred to 0035-FEAT and not misrepresented as a successful history lookup. See `evidence/Step 11/STEP-11.3-OFFSITE-DISPOSABLE-RESTORE-CLOSEOUT-20261014.md`. Step 11 and 0034-FEAT remain OPEN; next Step 11.4 is unattended operating arrangements.

## 2026-10-14 — Step 11.4 unattended arrangements: source implemented, live acceptance pending

Scheduled source-initiated operation is selected as the normal policy. Playbooks now contain default-off systemd schedules for production publication on `pluto`, verified collection on `mars`, and native incremental `mars -> backup` push, plus a read-only live acceptance playbook. The native `--latest` path never silently full-reseeds and timer activation rejects the rendered legacy rsync off-site phase. Applying source alone enables nothing: external inventory opt-in, deployment, successful services and timer evidence are still required. The held `20261013-171228Z` checkpoint remains protected. See `evidence/Step 11/STEP-11.4-UNATTENDED-OPERATING-ARRANGEMENTS-20261014.md`. Step 11.4, Step 11 and 0034-FEAT remain **OPEN**.

## 2026-10-15 — Step 11.4 unattended operating arrangements: CLOSED

The scheduled `pluto → mars → backup` cycle ran automatically on 15 October. `pluto` published schema-2 backup `20261015-003023Z` (89 Files); `mars` pulled and verified it, created the protected `20261015-030004Z` snapshot set, and pushed it incrementally; `backup` accepted a read-only received snapshot with matching received UUID and receipt. The `mango` read-only acceptance playbook passed (`pluto ok=3`, `mars ok=6`, `backup ok=3`, `changed=0`, `failed=0` everywhere). The 02:00 writer-lock collision failed closed and recovered with the 03:00 snapshot; the colliding user backup cron was rescheduled to 01:45 UTC through an isolated, idempotent Playbooks change. Its first unattended post-correction run is follow-up evidence. The held checkpoint `20261013-171228Z` remains protected. See `evidence/Step 11/STEP-11.4-UNATTENDED-ACCEPTANCE-CLOSEOUT-20261015.md`. **Step 11.4 CLOSED; Step 11 and 0034-FEAT remain OPEN pending separate overall reconciliation and closure.**

## 2026-10-15 — Final feature-wide reconciliation (closure gate pending)

See `evidence/Step 11/STEP-11-FINAL-RECONCILIATION-20261015.md` for the traceability matrix, verified unattended `pluto → mars → backup` cycle, off-site disposable restoration, safeguards and explicit qualifications. Step 11.3 and Step 11.4 are CLOSED. Step 11 and feature 0034 remain **OPEN** until Step 11.1's outstanding read-only four-host baseline evidence and final operator sign-off are recorded. Do not infer closure from a successful scheduled cycle alone. The history-tool `verification.required=false` configuration issue remains deferred to 0035, and rolling-copy storage efficiency is tracked by 0036. Retain checkpoint `20261013-171228Z` through final authorisation.

## 2026-10-15 — 0034-FEAT formally CLOSED

**Disposition: CLOSED (operator-authorised close-out, 15 October 2026).** Step 11.1 final four-host captures are present in `0034-step11-3-backup-2.zip` for `mango` (20261015-065850Z), `pluto` (20261015-070022Z), `mars` (20261015-070107Z) and `backup` (20261015-070156Z). Previous captures from 13 October are also retained in that archive. Capture SHA256 manifests were reviewed successfully. The evidence archive is an external operator-held artifact and is not bundled into this documentation-only change.

Step 11.3 disposable off-site recovery Gates A–D and Step 11.4 unattended Gates 6A–6E are **CLOSED**, including read-only acceptance (`pluto` 3 tasks, `mars` 6, `backup` 3; zero changes/failures). Accepted schema-2 publication `20261015-003023Z` and Btrfs incremental received snapshot `20261015-030004Z` establish the production workflow. Playbooks on `mango` were clean and synchronized at commit `2fb96e60ea75f55882b91a230d271e9e7fdbc635`; Diaries prior Step 11.4 source documentation commit `89d113ea25a4fef207fa5f2ef5452b32d1838fd2` was clean and synchronized. A future commit will record this final archival move.

**Accepted follow-ups, not blockers:** the rescheduled 01:45 UTC user cron is deployed and idempotent, but its *first unattended execution* was not observed at this decision point; verify it on the next cycle. The `diaries-backup-history` `verification.required=false` configuration limitation is deferred to 0035-FEAT; rolling storage/copy efficiency belongs to 0036-FEAT. Maintain protected checkpoint `20261013-171228Z`, existing replication parent protections, and historical Snapper/backup data until separately authorised. This closure does not authorise snapshot pruning changes, deletion, migrations or further deployment.

Final acceptance record: `evidence/Step 11/STEP-11-FINAL-RECONCILIATION-20261015.md` and `evidence/Step 11/STEP-11-FEATURE-CLOSEOUT-20261015.md`.
