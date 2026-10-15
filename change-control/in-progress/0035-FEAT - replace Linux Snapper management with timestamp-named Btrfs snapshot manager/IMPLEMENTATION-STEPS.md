# 0035-FEAT — IMPLEMENTATION-STEPS (native Btrfs replication revision, 2026-10-11)

> **ACTIVE DESIGN DECISION — 2026-10-12: SOURCE-INITIATED BTRFS PUSH AND REPLICATION-AWARE RETENTION**
>
> For the `mars` → `backup` native-replication leg, **`mars` initiates and orchestrates a push**. Previous wording assigning initiation to `backup` is superseded, but the **`pluto` → `mars` Diaries pull remains unchanged**. Retention protects the current common parent and in-flight candidate regardless of direction. No deployed behaviour changes as a result of this documentation update. See the 0034 Step 10 push architecture decision and `evidence/PUSH-REPLICATION-RETENTION-DESIGN-20261012.md`.
>

**Status:** Feature OPEN. This plan supersedes the outstanding rsync receiver/snapshot coupling steps, **not** historical evidence or already implemented standalone timestamp snapshot-manager functions. Preserve default-off activation and Snapper handover. 0034 owns production whole-backup publication and the send/receive orchestration; 0035 owns native snapshot creation, discoverability, retention and compatibility on relevant hosts.

## Step 1 — Reconcile observed host state and baseline (required)

**CLOSED — 2026-10-15:** Source-contract regression PASS; `mango` read-only three-host capture finished with `pluto ok=4`, `mars ok=6`, `backup ok=6`, and `changed=0`, `failed=0` everywhere. Baseline identities, schedules, snapshot/receipt lineage and zero-change execution reconciled in `evidence/Step 1/README.md`, with raw capture `evidence/Step 1/baseline-20261015-081000.txt`. Known limitations explicitly carried forward: timed-out Snapper inventories, stale `backup` local manager verification configuration, historical snapshot/mirror retention. **No configuration or deletion changes are authorised by this closure.**

- Record existing snapshot-manager installation, `root`/`@data` subvolume IDs, mount/UUID, `@snapshots` location, Snapper numeric snapshots, actual scheduler state and whole-backup-containing source on `mars`, `backup` and filesystem type on `pluto`.
- Confirm `pluto` is or is not Btrfs at deployment time; **never** assume it has native snapshots just because the history/prune utilities are installed there.
- Record the retained `/@data/backup` rsync mirror as historical/non-native, the isolated native receive tree/receipts separately, and whether any transfer is active at capture time. **Gate:** no preexisting snapshot or data overwritten.
- Reconcile rather than auto-correct any mismatch against the accepted 0034 close-out facts (01:45 `mars` user cron, source-initiated native push, held checkpoint `20261013-171228Z`, and preserved historical Snapper/backup data). Completed: live output reviewed and accepted baseline recorded in Step 1 evidence; exceptions are preserved for later steps.

## Step 2 — Preserve source timestamped read-only snapshot manager (`mars`)

- Validate installed 0035 manager takes complete, read-only timestamp-named snapshots of the existing source subvolume containing `/media/usb/@data/backup`; do not split/move the backup tree without a separate approval.
- Document whole-subvolume scope, nested subvolume handling, source UUIDs, read-only flags, timestamp naming and lock coordination with backup publication and `btrfs send`.
- Keep creation and prune schedules as previously accepted on `mars`; confirm Snapper timeline migration only to the extent already evidenced. Do not drop numeric Snapper snapshots en masse.
- Add safeguards preventing source parent snapshot deletion while it is used as a replication baseline or in-progress send.

**2026-10-15 closure: CLOSED.** Playbooks source-contract verification passed all nine checks and the read-only `mars` capture completed (`ok=2`, `changed=0`, `failed=0`). There were 52 complete `root`/`@data` timestamp sets and zero incomplete sets. Inspected checkpoint, replication-parent and recent snapshots were read-only, and hold/pin UUIDs matched. Existing creation/prune timers remained active. Source `@data/.snapshots` is a nested legacy subvolume; its presence was inventoried, not proof that its contents participate in Btrfs send. See `evidence/Step 2/PRESERVATION-VERIFICATION-20261015.md` and retained transcript. No host changes were made or authorised.

## Step 3 — Define receiver snapshot identity/retention (`backup`)

- Install Btrfs receive prerequisites and a dedicated receive repository separate from `/@data/backup` and rsync receiver directory. Decide whether it is a subvolume and how root-owned helpers constrain writes.
- Preserve read-only/received UUID identity of destination snapshots; define acceptance receipt outside immutable received subvolumes. Refuse unaccepted snapshots as replication parents or prune targets.
- Retention distinguishes local `root`/`@data` timestamp sets from **received** snapshots. Pin common parents on both endpoints; never prune the last usable incremental parent until a replacement baseline exists. Shared locking must exclude send/receive and prune; independently verify no unexpected snapshots under receive roots.

## Step 4 — Extend `diaries-backup-history` for `mars` **and** `pluto`

- Install the read-only history/locator on **both `mars` and `pluto`** (and optionally `backup`). Derive real backup IDs from frozen schema-2 dataset metadata; summarize unique backup IDs, with an `--all`/equivalent occurrence mode listing every containing timestamped snapshot path.
- On `mars`, find backups inside each Btrfs snapshot of the existing whole-backup-containing source; include accurate absolute restore-source paths and separately identify live/current copy.
- On `pluto`, resolve current fixed published `diaries-backup/` and any genuine snapshots; if `pluto` remains ext4, clearly show that no Btrfs snapshots exist. Do not invent snapshot history or run a destructive restore.
- If installed on `backup`, locate backup IDs in **received** Btrfs snapshots rather than the obsolete rsync directory.
- Tests: duplicate IDs, repeated unchanged snapshot, corrupted manifest, unavailable snapshot, non-Btrfs filesystem, multiple paths, and safe error behavior.

## Step 5 — Provide timestamp snapshot cleanup on `mars` and `pluto`

- Install native prune/dry-run/status utility on **both** hosts. Restrict deletions to manager-created timestamp names and validated Btrfs read-only snapshots; preserve unrelated subvolumes and all numeric Snapper IDs.
- On ext4/non-Btrfs `pluto`, report unsupported/no-op safely rather than deleting conventional directories. Document that no actual Btrfs pruning occurs there until explicitly configured on a Btrfs filesystem.
- Preserve GFS policy from existing docs (hourly 48, daily 14, weekly 12, monthly 24, yearly 5, minimum age 30 minutes) unless explicitly reconfigured; always keep the newest valid set and any replication-pinned parent.
- Show prune dry-run, refusal of active/pinned snapshot, coordinated multi-source timestamp-set retention, partial set handling and isolation from unrelated paths.

## Step 6 — Integrate native send/receive safety (joint gate with 0034 Step 10)

- Establish immutable source and accepted destination UUID pairing, last-common-parent discoverability, stream lock(s), and host-specific privilege boundaries using `richard` SSH plus narrowly permitted privileged Btrfs helper(s).
- Demonstrate full receive, later incremental receive, parent pinning, interruption cleanup and no unintended concurrent snapshot/prune. **Do not** use old rsync `.diaries-snapshot-verified.json` as the authoritative native receive marker.
- Measure receive extent sharing/disk allocation and transfer sizes, but do not claim cross-host physical extent identity. Validate optional application-level schema-2 content independently of the generic replication pipeline.

## Step 7 — Stage deployment on `mars`, `pluto`, and `backup`

- Install/rehearse `mars` snapshot/history/prune helpers and check retention of send parents. Verify it can still take and list timestamped read-only snapshots without changing the complete-backup source.
- Install history and pruning utilities on `pluto`, prove fixed published Diaries backup discovery, and confirm safe unsupported/non-Btrfs prune behavior if relevant.
- On `backup`, deploy receive integration **install-only** first. Verify live initial baseline and incremental from 0034, received snapshot lineage, independent retention and existing legacy `/@data/backup` safety.
- Keep `backup` native snapshot timer activation and Snapper handover disabled until signed-off, with no automatic scheduling as part of normal Ansible deployment.

## Step 8 — Retention, restore and failure acceptance

- Exercise timestamp retention across GFS boundaries, newest-snapshot safety, pinning of active transfer parents and old Snapper namespace preservation.
- Verify history locator maps IDs to real absolute paths and a snapshot-resident schema-2 dataset restores successfully into a **disposable** environment via the unchanged 0033 restore tool.
- Simulate storage pressure, loss of SSH, interrupted full/incremental transfer, duplicate received snapshot and stale/unknown parent; prior accepted receive remains usable. Log source/destination UUID and exact paths.

## Step 9 — Controlled scheduler migration, rollback and close-out

- Obtain explicit acceptance on all relevant hosts before changing timers/cron. Enable only required native snapshot/sender/receiver schedules and disable conflicting legacy transfer jobs once the new path is proven. Retain Snapper cleanup while numeric legacy snapshots age out naturally; never mass-delete them.
- Verify operational instructions, fault handling, observed snapshot retention and restore, revision/commit IDs, rollback and repeatable deployments. Close 0035 only after documented live verification; native `backup` snapshot timers remain off until approved.

## Safety contract

0035 must not introduce Diaries awareness into generic Btrfs transport, change `pluto`'s schema-2 format, treat rsync data as a received Btrfs baseline, modify preexisting `/@data/backup`, rewrite historical evidence or imply the design has already been deployed.


## Follow-on acceptance — 2026-10-12 push-based replication coordination (OPEN)

These steps supersede any pending implementation instructions describing `backup`-initiated native replication; previous completed steps/evidence remain historical.

1. Confirm 0035 protected-source registry and shared stable lock work when `mars` initiates and holds the transfer, with root-only permissions and fail-closed state loading.
2. Test candidate-before-send pinning and existing common-parent pinning, including a simulated prune between candidate registration and the Btrfs send operation.
3. Test receiver-acknowledged promotion, release of the superseded parent only after successful independent receipt verification, and recovery from lost acknowledgement after a successful receive.
4. Ensure source retention never deletes the last common parent if `backup` is offline, transfers fail, or the receiver is behind; receiver retention likewise preserves its last accepted parent. Explicitly define a safe manual recovery/reseed procedure for lost parents.
5. Validate set-level pruning across paired `root`/`@data` snapshot sources; a pin on `@data` must exclude the corresponding timestamp set from deletion. Prove no race between concurrent snapshot create, prune and push.
6. Confirm that both historical snapshot discovery and normal Diaries backup history remain correct; no loss to existing `/@data/backup`, legacy Snapper data or the completed read-only received baseline.
7. Keep automatic pruning **disabled** on `mars` until dry-run and live tests pass. Keep native transfer scheduling disabled until explicit controlled 0034 cutover. Record `mango` source regressions, on-host state checks and the first successful incremental push in the evidence folder before closure.

**Not implemented by this documentation update:** `mars` source-side push operator, receiver endpoint changes, deployment/schedule changes, and acceptance of the still-running full transfer.

## 2026-10-13 — Restricted Step 10 cleanup/hold acceptance (CLOSED)

The independent checkpoint hold and real scheduled prune passed on `mars`, and the narrowly scoped remote-backup pull cleanup deployed successfully without removing snapshot-manager or local-backup components. Evidence: `evidence/STEP-10-RESTRICTED-CLEANUP-ACCEPTANCE-20261013.md`. The runtime checkpoint `20261013-171228Z` remains held while the replication parent advances separately. Other 0035 migration and host acceptance gates remain distinct; this does **not** mean the entire feature is closed.
