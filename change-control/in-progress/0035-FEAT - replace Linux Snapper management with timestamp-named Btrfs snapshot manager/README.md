# 0035-FEAT — Timestamp-named whole-backup Btrfs snapshot management

> **ACTIVE DESIGN DECISION — 2026-10-12: SOURCE-INITIATED BTRFS PUSH AND REPLICATION-AWARE RETENTION**
>
> For the `mars` → `backup` native-replication leg, **`mars` initiates and orchestrates a push**. Previous wording assigning initiation to `backup` is superseded, but the **`pluto` → `mars` Diaries pull remains unchanged**. Retention protects the current common parent and in-flight candidate regardless of direction. No deployed behaviour changes as a result of this documentation update. See the 0034 Step 10 push architecture decision and `evidence/PUSH-REPLICATION-RETENTION-DESIGN-20261012.md`.
>

> **ACTIVE DESIGN — 2026-10-11: BTRFS SEND/RECEIVE REPLICATION**
>
> Supersedes the pending rsync-based `backup` receiver/mirror procedure; it does not erase prior snapshot-manager implementation or evidence. `mars` snapshot production continues. Native receive and retention require new implementation and live acceptance before any timer migration.

## Step 4 closure — 2026-10-15

**CLOSED (scoped acceptance):** existing `mars` history regression and native snapshot occurrences verified; history locator and independent schema-2 verifier installed on ext4 `pluto`; fixed publication reported `production / 20261015-003023Z / live / verified`. This closure does not claim live `show`, `path`, `verify` or deployment idempotency (`changed=0`) were exercised, and those checks remain additional operator verification. See `evidence/Step 4/README.md`. No snapshot pruning or restore authorised.

## Updated responsibilities (2026-10-11)

| Host | Snapshot manager / pruning | Diaries history locator | Replication |
| --- | --- | --- | --- |
| `mars` | Maintain timestamp-named read-only snapshots of the existing whole-backup-containing Btrfs subvolume; prune only when no active send or receiver incremental parent needs them | Install/read-only; list IDs and snapshot occurrences | Provide immutable snapshot for full/incremental send through privileged source helper |
| `backup` | Manage received read-only Btrfs snapshots, retention and parent preservation in an isolated repository; legacy Snapper untouched until acceptance | Optional/valuable for restore verification, not a transfer dependency | Initiate/coordinate native send/receive through `richard` SSH and privileged Btrfs helpers |
| `pluto` | Make snapshot cleanup utility available; if filesystem is not Btrfs, report unsupported/no-op safely | **Install/read-only**; show current fixed published backup, ID and any actual available containing snapshots | Continue existing complete-backup publisher; **no Btrfs send requirement** |

Snapshot cleanup and history are *two separate operator tools*. The history utility must deduplicate identical backup IDs in its summary and retain per-snapshot occurrences (`--all` or equivalent); it must not infer snapshots on ext4 or include unverified content as restorable. Retention must operate on explicitly owned timestamp namespaces, not Snapper numeric IDs or unrelated snapshot trees. For the receiving host, retention must coordinate with Btrfs incremental-parent availability and any in-flight replication; do not prune the last usable baseline/common parent without a new baseline.

## Native replication contract (2026-10-11)

- Preserve existing `mars` whole-backup layout and the installed timestamped `@data` snapshots. `btrfs send` transfers a **snapshot subvolume**, not merely the `backup/` directory inside it. Inspect the complete `@data` snapshot size, subordinate subvolumes and mount boundaries. Exclude nothing implicitly; use an explicit design revision if total scope is unacceptable.
- `backup` accepts an initial full read-only snapshot via `btrfs receive` to a dedicated *Btrfs* repository, separate from the old rsync directory and from `/@data/backup`; later receives use `btrfs send -p <common-parent> <new-snapshot>`. Match source snapshot UUIDs to destination `Received UUID` and protect the parent on each side until the child receive is validated.
- Invoke transfer through `richard`'s tested SSH alias, with constrained `sudo`/root-owned helpers for Btrfs operations; do not require root's personal SSH setup or broad writable permissions over snapshot roots. Preserve immutable received snapshots. A completed stream alone is not sufficient: check subvolume identities, read-only property, expected files and optional independent application-level verifications, then record acceptance externally.
- Use explicit transfer/snapshot locks and staging/cleanup logic. New receive state is not eligible for pruning or publication before validation. Test failed streams, concurrent sends, incompatible parents, storage exhaustion and restarts. Document measured space-sharing and transferred bytes (do not promise identical physical extent numbers on separate filesystems).
- Native receiver code must **not depend on Diaries**: backup files are ordinary data within the whole-backup tree. The independent history/restore tooling may understand schema-2 manifests and dates, without controlling transport acceptance.
- Keep `backup` native creation/prune timers and Snapper handover inactive pending deliberate acceptance. Receiving snapshots and general local snapshots have separate provenance and retention rules; do not accidentally duplicate entire receive trees in unrelated local snapshots.


## Step 1 baseline reconciliation tooling (2026-10-15)

Step 1 now has a dedicated **read-only** three-host Playbooks capture under `verification/0035-step1/`. It records actual `pluto` filesystem type, `mars`/`backup` Btrfs mount and subvolume identities, timestamp and Snapper snapshot inventory, scheduler/cron state, replication holds/receipts, retained historical rsync state and any active transfer. It does not deploy, prune, create snapshots, run transfers or change schedules. **Step 1 CLOSED 2026-10-15** after a successful zero-change three-host capture and documented reconciliation. Three exceptions (Snapper timeouts, stale receiver verification path and retained historical storage) remain tracked; this closure does not authorise remediation or deletion. See `evidence/Step 1/README.md`.

---

## Earlier design and completed-step record (historical; superseded where inconsistent with 2026-10-11)


## Type / status

Feature — **In progress**. Opened 2026-10-08; design revised 2026-10-08 to integrate fixed-directory Diaries backup and whole-backup snapshots. Existing change-control directory/title (“replace Linux Snapper management with timestamp-named Btrfs snapshot manager”) retained for continuity.

## Starting state (not a greenfield project)

The latest Playbooks bundle contains a **prepared**, shared `roles/snapshots` native Python manager, timestamps named `YYYYMMDD-HHmmssZ`, configurable read-only snapshots of `root` and `@data`, locking, GFS pruning, dry-run, timers, and Snapper handover wiring for **both `mars` and `backup`**. The original 0035 Step 2/3 source work and static regression evidence must be **retained**. Runtime pre-migration inventory, host deployment, verified-sync integration, and Diaries history are **not proven/finished**. The previous design is preserved under `evidence/2026-10-08-PRE-REDESIGN/`.

## Agreed transfer direction and live inventory (2026-10-09)

**Agreed design:** always-on backup servers initiate **pull** transfers. `mars` pulls the pinned, immutable current Diaries generation from `pluto`; `backup` pulls a coherent, verified read-only whole-backup snapshot from `mars`. Intermittently powered laptops and PCs instead **push** to a restricted landing area on `mars` when online; receipt/verification/promotion must be separate from uploader-controlled files. This is a target design, **not currently activated**.

**Observed live baseline (read-only operator inventory, 2026-10-09):** `mars` has `/dev/sdb1` Btrfs mounted at `/media/usb` and backup tree `/media/usb/@data/backup`. Its user cron job runs at **02:00** (`/home/richard/scripts/backup/backup.sh`), and root cron runs at **02:15** (`/root/scripts/backup/backup.sh`). The root `remote/backup.sh` currently **pushes** with `rsync -avzh --omit-dir-times --itemize-changes --delete --delete-excluded` from `/media/usb/@data/backup/` to SSH alias `richard-at-backup:/@data/backup`; include/exclude rules are separate files and require inspection before changes. On `backup`, `/@data/backup` lies on Btrfs mounted as `/` (`/dev/sda2`); neither user nor root has a crontab. On `pluto`, `/home/richard/projects/diaries/data/dataset-backups/production` exists; no root crontab was reported. The inventory does **not** establish a current dedicated Diaries transfer, full include/exclude coverage, actual SSH permissions, or snapshot subvolume boundaries.

**Safe transition:** inventory and preserve existing schedules and data first; install new pull services disabled by default; prove restricted read credentials, destination paths, schema-2 verification and safe reader/receiver locks; rehearse on a separate receiving subtree; then perform an explicitly controlled cutover. For the remote leg, enable the verified `backup` pull and disable `mars`'s previous push in a coordinated handover, avoiding concurrent transfers. `backup` must never read a mutating live mirror: pin a verified read-only `mars` snapshot for its entire pull. No new snapshot is labelled Diaries-restorable on rsync exit status alone. Retain the last good received snapshot on failure, and never let a laptop/PC upload directly mutate a verified snapshot source.

**Responsibility boundary:** 0034 owns the pinned Diaries publication and the `mars` pull/receiving schema-2 validation handoff. 0035 owns whole-backup snapshot coordination, safe remote `backup` pull, per-host verification, retention, Snapper migration, and deduplicated backup history. Keep existing source and evidence; do not deploy or change cron merely because this design is documented.

## Real replication topology

```text
pluto (ext4)                         mars (USB Btrfs)                 backup (Btrfs)
  fixed diaries-backup/  <--pull--    whole-backup writable mirror <--pull--  remote whole-backup mirror
                                      read-only timestamp snapshots    read-only timestamp snapshots
```

On `pluto`, 0034 produces exactly one verified, current, schema-2 `diaries-backup/` containing:

```text
diaries-backup/
├── database/diaries.dump
├── database/diaries.sql
├── files/
├── verification/
└── dataset-manifest.json
```

`backupId` and `logicalDataset` remain inside the manifest. Multiple consecutive Btrfs snapshots **may contain the same Diaries backup ID**. The snapshot's UTC timestamp records *snapshot creation*, **not** Diaries backup creation time.

## Snapshot scope and Btrfs layout

**Whole-backup snapshots**, encompassing the Diaries mirror **and other important backup content**, are the default. The exact host-specific rsync target, subvolume layout, existing `root`/`@data` snapshot sources and live mount points must be inventoried before rollout. On `mars`, current Btrfs root is `/media/usb` and data source is `/media/usb/@data`; on `backup`, `/` and `/@data` according to existing Playbooks design. The proposed `@snapshots` namespace remains distinct from legacy Snapper `.snapshots`.

**Critical:** Btrfs snapshots do not recursively snapshot nested subvolumes. The receiver's `diaries-backup/` must be ordinary directories **within the snapshotted data subvolume**, or the manager must deliberately add the correct subvolume as an independently snapshotted source. A `root` + `@data` same-timestamp set is not a single atomic multi-subvolume transaction; define a shared sync quiescence barrier and explicitly record any consistency limits for other data.

The current shared manager's `root`/`@data` and same-time snapshot-set design should be reused where proven appropriate; do not assume it already covers actual Diaries rsync targets. Names such as `@snapshots/@data/20261008-190000Z` are illustrative until runtime paths are confirmed.

## Verified snapshot creation pipeline

1. Identify the exact completed 0034 `diaries-backup/` generation using its manifest (`backupId`, logical dataset), and pin it throughout source replication.
2. Synchronise `pluto` to `mars` into the managed writable mirror; independently validate the received schema-2 database+Files dataset. Do **not** use `rsync --inplace` or `--append` on the snapshot-backed mirror. Limit any deletion to the managed subtree.
3. Coordinate *all* writers of the whole-backup snapshot source. Abort if another backup/sync job is actively mutating it or the Diaries received dataset has not passed verification.
4. Create a read-only timestamp-named whole-backup snapshot set only after verification and the write barrier. Keep the last good snapshot unchanged on failed transfers.
5. Replicate the coherent data from `mars` to `backup`; independently verify the remote Diaries dataset and snapshot only after a local success barrier. Ordinary rsync **does not transfer reflink relationships**, but snapshots on `backup` share unchanged extents locally when files remain unchanged.
6. Do not promise content deduplication across distinct files in a single mirror; extent sharing here is **between snapshots of the same stable mirror**. Use rsync's normal skip-unchanged behaviour; changed file rewrites allocate new extents by design.

Scheduled hourly snapshots for non-Diaries data may coexist, but a snapshot must never be advertised as a **verified Diaries recovery point** unless the contained manifest and dataset have passed the agreed validation barrier. A conditional schedule/hook may skip creation, annotate status, or distinguish unverified snapshots. Choose and implement one explicit policy before enabling timers.

## Native manager / retention / Snapper migration

Retain the prepared `btrfs-snapshot-manager` source, `/etc/btrfs-snapshot-manager.json`, `@snapshots` namespace, `create`, `list`, `status`, `prune --dry-run` and `prune`, lock, same-filesystem validation, read-only creation, and GFS bucket model (initial defaults: hourly 48, daily 14, weekly 12, monthly 24, yearly 5; minimum prune age 30 minutes). Validate all effective values against live state.

Existing Snapper IDs must never be renamed or bulk-deleted. Stop new Snapper timeline/boot creation **only after** manager preflight and verified rollback readiness; temporarily preserve existing Snapper cleanup until numeric snapshots naturally expire. Do not interfere with Synology DSM snapshot management. Rollback disables native timers, restores Snapper timers/config where needed, and leaves native read-only snapshots intact pending explicit review.

## `diaries-backup-history` (new required operator tool)

Provide read-only discovery on `mars` and `backup` over manager-owned retained snapshot sets:

```text
diaries-backup-history list               # one row per unique logicalDataset + backupId
diaries-backup-history list --all         # every snapshot occurrence
diaries-backup-history show BACKUP_ID     # snapshots containing one ID
diaries-backup-history path BACKUP_ID     # path to first retained occurrence
diaries-backup-history verify BACKUP_ID   # explicit full schema-2 integrity verification
```

Optional `--snapshot` selects a specific occurrence. The grouping key is **(logical dataset, backup ID)**; if one ID has incompatible manifest content or the same snapshot contains inconsistent files, mark it **conflicted/invalid** rather than merge silently. Use manifest metadata for fast `list`, with explicit `verify` for full content integrity. Missing, malformed, partial, unverified or conflicting manifests must produce visible warnings and nonzero/structured status as appropriate. Paths must be resolved **only under configured read-only manager-owned snapshot roots**, guarding against symlink escape; no arbitrary path traversal. No history command deletes, prunes, or invokes a destructive restore.

Suggested list output:

```text
LOGICAL DATASET  BACKUP ID          FIRST RETAINED SNAPSHOT   LAST RETAINED SNAPSHOT   SNAPSHOTS
production       20261008-170000Z   20261008-180000Z          20261009-080000Z        2
```

`SNAPSHOTS` counts retained occurrences, **not independent physical copies**. If several snapshots share an ID, show one summary row. Snapshot retention may remove the oldest occurrence; the history tool then reports the earliest **remaining** one. Consider an explicitly configured minimum-retention rule for unique Diaries backup IDs, but never silently override general storage-safety limits.

## Acceptance and inter-feature contract

0034 supplies immutable, verified current source with stable path and schema-2 backup identity. 0035 supplies verified receiving sync/whole-backup snapshot sets, per-host timestamp retention, deduplicated backup discovery and safe historical path selection. Snapshot metadata cannot replace dataset manifests. A preflighted `pluto` ext4 filesystem is expected, not an error. No Docker images or NAS snapshot changes are required purely for this plan revision.

## Evidence and rollout

Follow revised `IMPLEMENTATION-STEPS.md`, beginning with current on-host inventories and verification of the already-prepared manager against the real data paths. Preserve the previous design and Steps 2/3 static evidence. **No live deployment or retrospective claim of 0035 closure is made by this documentation change.**

## Recovered Playbooks source reconciliation and deployment interlock (2026-10-08 review)

The accidentally extracted `diaries/roles/` sources have been reconciled in the **latest supplied Playbooks source bundle** (`playbook-sources-20261008-202240.zip`): the shared `roles/snapshots/` role and its Python manager, default variables, templates, handler and regression test are present, and `roles/remote-backup/tasks/main.yaml` delegates to `snapshots`. The latest supplied Diaries bundle contains **no top-level `diaries/roles/` directory**. This verifies the bundle contents only; it is not proof of Git commits or that the live hosts have been updated. No further copying from an older accidental directory should occur without a deliberate diff.

**Critical source gap:** `roles/snapshots/tasks/main.yaml` currently enables the native create/prune timers and disables Snapper timeline/boot timers as part of ordinary role execution. `btrfs-snapshot-create.service.j2` invokes the manager's unconditional `create` command; the manager has no verified-rsync handshake, so deploying this role unchanged would violate the new verified-sync design. Add an explicit **default-off activation/migration gate** and prevent timer activation/legacy Snapper changes until the verified-sync barrier and host-specific inventory have passed. Deployment of files, configuration and `status` preflight must be possible without activating timers. Merely adding cautionary documentation is insufficient.

The recovered role currently defaults to two sources, `root` and `@data`, while the retention algorithm prunes each source independently. These are **not necessarily an atomic or indivisible whole-backup snapshot set**. Step 1 must establish which source contains the actual mirrored `diaries-backup/` and other protected datasets; later tests must prove coordinated set creation and retention or explicitly describe independent source histories. A one-time timestamp string alone does not confer transactionality.

`roles/remote-backup/tasks/main.yaml` now contains a single `include_role: snapshots` task. This is a delegation, **not proof** that source mirroring, validation, or snapshot scheduling are correctly integrated. Historical Snapper helper files still exist under both `roles/snapshots/files/` and `roles/remote-backup/files/`; audit their callers before deleting them. The `roles/local-backup` scripts and actual `mars`/`backup` jobs also require mapping to the verified-sync barrier.

**Recovery audit acceptance:** (a) verify the 10 formerly missing files and both reconciled task files against the latest Playbooks working tree; (b) inspect `git status`/`git diff` and commit changes separately from live migration; (c) execute `python3 roles/snapshots/tests/verify-btrfs-snapshot-manager.py`; (d) dry-run Ansible syntax/inventory checks; (e) prove normal source deployment cannot change snapshot timers or Snapper until explicit opt-in. No host activation is authorised by repository reconciliation alone.


## Receiving-replica privilege boundary — 2026-10-10 (design update, not deployed)

For 0034 Step 10's **isolated `backup` replica** (`/@data/diaries-mars-replica`), the agreed operating model is a normal-user receiver plus a privileged Btrfs snapshot manager:

- Playbooks provisions the managed receiving directory/children with `become: true`, but the owner and receiver identity is configurable `backup_pull_user` (initially **`richard`**). This is distinct from legacy `/@data/backup`, whose contents and ownership must not be altered or subjected to new `--delete` scopes.
- The `backup`-initiated pinned-source SSH/rsync pull, independent schema-2 verification and final verified-marker write execute as **`richard`**. Root SSH and root-run rsync are not part of the intended transfer path. Adapt rsync ownership/group flags for non-root receiving without weakening independent content validation.
- **`root` retains ownership of privileged operations**: Btrfs snapshot/subvolume creation, systemd timer/retention management and any required filesystem-level operations. The snapshot manager reads the published verified state and must reject an unverified or in-progress receiver, regardless of process identity.
- The unprivileged writer and root manager must cooperate on one **stable, explicitly provisioned shared lock file** (`/@data/diaries-mars-replica/.btrfs-snapshot-writer.lock` or the configured equivalent), the same inode and locking protocol across jobs. Both identities must be able to acquire it; avoid replacement by rsync, cleanup or atomic file publication. Protect lock and locally generated eligibility marker from rsync deletion. Test lock contention, aborted pull, stale/missing marker and failed verification before enabling native snapshot timers.
- A `richard`-owned mirror is compatible with **root-operated Btrfs snapshots**: writable-tree ownership does not confer permission to create/delete Btrfs snapshots. Verify snapshot source/subvolume coverage includes the isolated replica, and ensure marker discovery uses the correct `diaries-mars-replica/pluto/diaries-backup` relative path rather than silently reverting to `/@data/backup`.
- The remote immutable `mars` snapshot must be readable/traversable as `richard` before accepting an unattended pull; this is still an open 0034 integration gate. Preserve the preexisting `mars` snapshot state, `backup` Snapper cleanup/timeline and disabled native timers while testing.

**Acceptance addition for 0035 `backup` deployment:** prove one completed pull run entirely as `richard`, read-only source/verified marker access, valid independently verified receive, correct shared-lock serialization against root snapshot creation, correct history/deduplication, and unchanged legacy data. This document does **not** assert those runtime tests have passed or close 0035.


## 2026-10-12 — Source-initiated replication retention revision

For native whole-backup replication, `mars` is the SSH initiator, sender, scheduler candidate and owner of **source-side** protected-snapshot lifecycle; `backup` remains authoritative for receiver verification, readonly received snapshots, receipt issuance and receiver retention. This replaces the prior design instruction that `backup` initiate the native pull, **not** the independent `pluto` → `mars` application backup pull. This is not a change to local timestamp naming, the 0033 schema-2 format, or Snapper history.

The existing root-owned state `/media/usb/@snapshots/.replication-protection.json` and 0035 manager lock must remain the protection source of truth on `mars`. Protect candidate **before** push, and last successfully accepted common parent until a newer received child has been authenticated and accepted; fail closed for absent/corrupt/unsafe protection state. Prevent pruning either `@data` snapshot or its paired set while pinned. Never infer acceptance from a completed `btrfs send`, from writable sender metadata, or from SSH exit alone. `backup` maintains receiver-owned acceptance receipts and retains required received parents. No automatic cleanup of an incomplete receiver subtree without classification/recovery.

The current full receive `20261012-100003Z` remains an active **pull** transfer and is expected to become the push parent only after completion/verification. Keep the 0035 prune timer on `mars` disabled until live protection/prune concurrency and parent advancement are proved. Backup receiver timers and legacy Snapper transitions remain independent acceptance gates. See `evidence/PUSH-REPLICATION-RETENTION-DESIGN-20261012.md`.

## 2026-10-13 — Restricted Step 10 cleanup/hold acceptance (CLOSED)

The independent checkpoint hold and real scheduled prune passed on `mars`, and the narrowly scoped remote-backup pull cleanup deployed successfully without removing snapshot-manager or local-backup components. Evidence: `evidence/STEP-10-RESTRICTED-CLEANUP-ACCEPTANCE-20261013.md`. The runtime checkpoint `20261013-171228Z` remains held while the replication parent advances separately. Other 0035 migration and host acceptance gates remain distinct; this does **not** mean the entire feature is closed.


## 2026-10-15 Step 2 closure

**Step 2 — Preserve source timestamped read-only snapshot manager (`mars`): CLOSED.** Source-contract checks passed; read-only live capture finished with `changed=0`, 52 complete timestamp sets, intact read-only held and replication-pinned snapshots, and enabled creation/prune timers. See `evidence/Step 2/PRESERVATION-VERIFICATION-20261015.md` and `mars-preservation-20261015-083123.txt`. Nested `@data/.snapshots` was inventoried, not proven part of a send stream; no cleanup or deployment authorised.


## 0035 Step 3 closure — 2026-10-15

**CLOSED:** The read-only `backup` receiver capture reconciled eight accepted receipts with eight received read-only subvolumes; UUIDs and parent lineage matched, with no missing or unreceipted snapshots. All nine source-contract checks passed, and Ansible reported `ok=2`, `changed=0`, `failed=0`. Receiver-local snapshot timers remain disabled. Received-snapshot pruning is **not enabled or authorised**; preserve `/@data/backup`. The separate stale local manager verification path remains deferred. See `evidence/Step 3/README.md` and the captured transcript.
