# 0040-FEAT — Design and safety contract

## Architectural rule

One production `btrfs-snapshot-manager` codebase and one deterministic retention selection implementation installed on **both** `mars` and `backup`. Host differences are declarative configuration plus narrowly scoped source/receiver safety checks. Avoid a second, independently maintained receiver-pruning program.

### Source: `mars`

- Collects backups from configured machines into the existing fixed working dataset.
- Creates timestamped read-only Btrfs snapshots of that dataset.
- Maintains source-side holds/pins, source snapshot selection and send-parent safety.
- Initiates native incremental replication to `backup` using existing sender tooling.
- Keeps existing accepted backup/snapshot schedules unless an explicit deployment gate changes them.

### Approved mars root-snapshot retirement

The `mars` Btrfs root at `/media/usb` contains only nested subvolumes `@data` and `@snapshots`. A read-only inspection of `@snapshots/root/20261023-070038Z` verified only empty placeholders; Btrfs reports 16 KiB referenced and exclusive. Root snapshots therefore do not capture the backup datasets. The operator approved retiring this snapshot population in 0040-FEAT.

- Target source-managed population: **only** `/media/usb/@snapshots/@data/<timestamp>`; no newly created `root/<timestamp>` snapshots after controlled activation.
- Target receiver-managed population: **only** `/@data/mars-received/@data/<timestamp>`.
- Both modes share identical snapshot selection code but host-specific inventory, creation permissions, lock and parent/receipt checks.
- Snapshot-set completeness must be based on configured datasets, **not** hardcoded paired `root` plus `@data` presence. Preserve compatibility with existing root/`@data` pairs during migration.
- Preserve `@data` history, source holds and common send/receive parent; remove only individually inventoried root snapshots at an explicitly approved destructive gate.
- Review tools, timers, roles, reports, and regression tests for root-pair assumptions before disabling source creation or deleting snapshots.
- Avoid attempting to delete placeholder directories *inside* read-only snapshots. The root snapshot subvolumes themselves are retirement candidates.
- The legacy `btrfs-legacy-prune.timer` on `mars` remained **enabled** and deleted a Snapper `@data` snapshot on 22 October 2026. This active migration path must be managed deliberately; do not silently remove the functionality in a shared-manager refactor.

### Receiver: `backup`

- Receives snapshots at `/@data/mars-received/@data/<timestamp>`; does not locally create snapshots of those data.
- Shares the same retention selection algorithm on this received inventory, but **receiver mode** is incapable of `create` and rejects invalid or non-received candidates.
- Coordinates pruning with the replication state and writer lock and checks retained sender/receiver parent compatibility before deletion.
- Preserves `/@data/mars-received/.replication-state/` including receipts, locks and currently required baselines. Receiver prune must not destroy information required for future incrementals or rollback.
- Existing native receiver implementation may already perform retention: identify ownership and disable any duplicate pruner before activation. Exactly one authority prunes each receiver snapshot population.

## Desired data layout on `backup`

```text
/
└── @data/
    └── mars-received/
        ├── @data/
        │   ├── <timestamped received read-only snapshot>/
        │   └── ...
        └── .replication-state/
            ├── writer.lock
            ├── <receipt>.json
            └── <other required receiver metadata>
```

This describes the **backup-data** layout, not the entire Linux root filesystem. Additional normal OS directories, top-level Btrfs subvolumes and system metadata may remain.

## Retirement candidates and non-candidates

| Path | Disposition | Required gate |
| --- | --- | --- |
| `/@data/backup` | Retire old mutable backup tree | Confirm no writers, comprehensive content coverage or explicit acceptance of unique loss, rollback and Snapper extent references |
| `/@data/.snapshots` | Retire legacy Snapper `@data` subvolumes | Enumerate actual Btrfs subvolumes, protections, mount configuration and retention consequences |
| `/@snapshots/@data` | Retire obsolete local snapshot tree | Confirm emptiness/contents and no installed references |
| `/@snapshots/root` | Retire obsolete local snapshot tree | Confirm emptiness/contents and no installed references |
| `/.snapshots` | **Retire — approved in Step 2** | Disable APT Snapper pre/post hooks through Playbooks; verify no recreation after deletion |
| `/@data/mars-received/@data` | **Keep**; retained snapshots managed by shared tool | Read-only identity, receipts, parent dependency and protected anchors |
| `/@data/mars-received/.replication-state` | **Keep** | Receipt and writer-lock invariants |

Btrfs nested subvolumes must be inventoried and deleted via supported subvolume operations in correct order; `rm -rf` is not an acceptable substitute for approved Btrfs snapshot deletion. Pruning may free less than apparent `du` because of shared extents and outstanding subvolumes; measure real filesystem usage after Btrfs deletion completion and qgroup reconciliation.

## Snapshot protection invariants

1. Fail closed when inventory, timestamp, UUID, read-only flag, receipt, lock or parent identity cannot be validated.
2. Recheck all invariants immediately before each permitted deletion.
3. Keep source and receiver replication parent compatibility; a snapshot's GFS age alone is insufficient justification to delete it.
4. Avoid overlapping source send/receiver receive with receiver prune; use the established replication writer lock. Respect any other installed lock domains.
5. No pruning via duplicate timers/tools. Opt-in to activation only after positive check/diff, deployment and runtime acceptance.
6. No mutation of received subvolume UUID, Received UUID or ro flag to implement deduplication. Deduplication is not a prerequisite of this feature.
7. Preserve supported historical restore contract: verify representative manifests/paths and previously accepted recovery evidence; no repeated full restore absent new risk.
8. Keep 0039 stale-qgroup maintenance operational and independent; inspect any lock interaction without silently modifying its schedule.
9. Record identities, receipt sets and Btrfs capacity before and after every destructive step; preserve an explicit rollback/abort strategy.

## Retention contract approved in Step 2

Hourly/daily/weekly/monthly/yearly buckets can be computed identically on both hosts, with explicit handling for UTC snapshots, unavailable periods, holds, incomplete sets, missing received counterparts, transfer baseline and generation lineage. Do not assume same policy yields identical keeps on a partially replicated receiver. Protect the most recent verified common parent (and any additional required baseline) until the sender/receiver protocol confirms safe advance. Reconcile the current receiver's pre-existing pruning semantics before replacing or reusing them.

## Metadata

`backup/.diaries-snapshot-verified.json` located in the overall snapshot points to the embedded Diaries backup using `datasetRelativePath=backup/pluto/diaries-backup` and `sourceIdentity=pluto:/home/richard/projects/diaries/data/diaries-backup`; `backupId` identifies the embedded dataset generation, not the containing Btrfs timestamp. Preserve marker and schema-2 restore discovery.

## Step 2 decisions accepted (23 October 2026)

- Retire **all legacy Snapper snapshot populations on both hosts** under later controlled gates, including root `/.snapshots` and APT-generated pre/post snapshots on `backup`, and legacy `mars` Snapper history and pruning machinery.
- Retire native root snapshots on `mars`, using `@data`-only snapshots going forward.
- Retain hourly 48, daily 14, weekly 12, monthly 24, yearly 5 and minimum age 30 minutes on both hosts, using the same algorithm.
- Operator explicitly accepts loss of historical recovery points that exist only in the legacy trees, including pre-9-October-2026 snapshots and two older Diaries generations if not otherwise preserved. This does **not** permit deletion of live data still required for an accepted current restore; verify coverage in Step 10.
- Protect source holds, receipts, lineage, receive lock, and verified common send/receive parent(s). Exact parent selection semantics require Step 3 source review.
- Final capacity guard, identity-specific deletion manifest and rollback/abort criteria require Step 10 review and a **separate Step 11 go/no-go**. Step 2 closure is policy acceptance, not an operational deletion permit.
