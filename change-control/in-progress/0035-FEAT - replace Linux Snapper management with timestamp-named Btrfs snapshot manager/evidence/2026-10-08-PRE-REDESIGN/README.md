# 0035-FEAT - Replace Linux Snapper management with timestamp-named Btrfs snapshot manager

## Type

Feature

## Status

In progress

## Priority

Medium

## Opened

2026-10-08

## Summary

Replace new Snapper-managed Btrfs snapshot creation on the Linux backup hosts `mars` and `backup` with one small Playbooks-managed native Btrfs snapshot manager.

New snapshots are named directly with UTC timestamps such as:

```text
20261008-070000Z
```

rather than being presented primarily through Snapper numeric IDs such as `381`, `382`, and `383`.

The feature deliberately does **not** change Synology NAS snapshot management. The NAS remains owned by DSM/Snapshot Replication. It also does not turn Diaries complete backups into Btrfs snapshots; 0034 remains the separate feature that makes schema-2 Diaries backup directories Btrfs/reflink-aware.

## Why this is separate from 0034

There are two different recovery objects:

```text
Btrfs snapshot
    storage/filesystem recovery point
    host-specific
    native subvolume snapshot

Diaries complete backup
    application-consistent recovery point
    PostgreSQL + matching Files + verification + manifest
    portable schema-2 directory
```

0035 manages the first object. 0034 optimises the second object. They may share naming and retention concepts, but neither depends on the other.

## Existing implementation being replaced

The current Linux snapshot model uses Snapper:

- `mars` reaches the shared `snapshots` role through `local-backup`;
- that role provisions Btrfs plus `aisbergg.snapper` and creates `root` and `@data` Snapper configurations;
- `backup` duplicates much of that Snapper setup directly inside `remote-backup`;
- Snapper's timeline, cleanup and boot timers manage lifecycle;
- Snapper's native operator identity is a numeric snapshot ID.

The current Playbooks evidence also shows an explicit template override of:

```text
TIMELINE_LIMIT_HOURLY = 2
TIMELINE_LIMIT_DAILY  = 12
```

The remaining effective Snapper retention values must be captured from the live hosts before final retirement of Snapper so the migration record preserves what was actually deployed.

## Target architecture

Both Linux hosts use the same Playbooks role and the same small Python manager:

```text
                       roles/snapshots
                             |
             +---------------+---------------+
             |                               |
           mars                            backup
    /media/usb/@snapshots                 /@snapshots
             |                               |
       +-----+-----+                   +-----+-----+
       |           |                   |           |
      root       @data                root       @data
       |           |                   |           |
 timestamp    timestamp            timestamp    timestamp
 snapshots    snapshots            snapshots    snapshots
```

The actual source paths remain host-specific through the existing Btrfs variables:

```text
mars:
    filesystem/source root: /media/usb
    data source:            /media/usb/@data
    managed snapshots:      /media/usb/@snapshots

backup:
    filesystem/source root: /
    data source:            /@data
    managed snapshots:      /@snapshots
```

Runtime preflight must confirm the resolved paths and Btrfs filesystem identity before scheduled creation is enabled.

## Snapshot naming and layout

`@snapshots` is itself a Btrfs subvolume. Under it, each configured source has a normal directory containing read-only Btrfs snapshots whose destination name is the UTC creation timestamp:

```text
@snapshots/
├── root/
│   ├── 20261008-070000Z
│   ├── 20261008-080000Z
│   └── 20261008-090000Z
└── @data/
    ├── 20261008-070000Z
    ├── 20261008-080000Z
    └── 20261008-090000Z
```

One `create` invocation generates one timestamp and uses it for every configured source. The resulting root and `@data` snapshots therefore form an obvious same-time set without introducing a separate numeric operator ID.

Btrfs still assigns its own internal numeric subvolume IDs. Those remain filesystem implementation metadata rather than the normal human-facing identity.

## Native manager

The permanent operator tool is installed as:

```text
/usr/local/sbin/btrfs-snapshot-manager
/etc/btrfs-snapshot-manager.json
```

Supported operations are:

```bash
sudo btrfs-snapshot-manager status
sudo btrfs-snapshot-manager list
sudo btrfs-snapshot-manager create
sudo btrfs-snapshot-manager prune --dry-run
sudo btrfs-snapshot-manager prune
```

The manager:

- requires root;
- requires every source and the snapshot repository to be on Btrfs;
- requires the sources and repository to resolve to the same Btrfs filesystem UUID;
- requires the repository root itself to be a Btrfs subvolume;
- creates read-only snapshots with `btrfs subvolume snapshot -r`;
- rolls back only snapshots created by the current multi-source invocation if a later source fails;
- serialises create/prune operations with a lock file;
- lists/prunes only names matching `YYYYMMDD-HHmmssZ` below its own configured repository;
- never traverses or modifies Snapper's `.snapshots/<ID>` hierarchy.

## Scheduling

The shared role installs separate systemd timers:

```text
btrfs-snapshot-create.timer
btrfs-snapshot-prune.timer
```

The initial schedule is:

```text
create: every hour at :00
prune:  every hour at :15
```

The creation timestamp itself is always UTC even though systemd may evaluate the schedule in host local time.

## Retention policy

The new manager implements a small GFS-style retention algorithm. It selects the newest snapshot in progressively coarser UTC time buckets.

The initial explicit Playbooks policy is:

```text
hourly:  48
 daily:  14
weekly:  12
monthly: 24
 yearly:  5
minimum age before pruning: 30 minutes
```

A snapshot may satisfy more than one bucket. The newest managed snapshot is always retained.

The important architectural decision is the **policy vocabulary**, not these exact values. The values are normal Playbooks configuration and can be tuned after operational review without changing snapshot names or layout.

This vocabulary is intentionally compatible in concept with the thinning approach used by Synology Snapshot Replication and with future Diaries complete-backup retention, while each system remains responsible for deleting only the recovery objects it owns.

## Non-destructive Snapper migration

Do not rename Snapper directories and do not bulk-delete the existing numeric snapshots.

During deployment the role performs this handover:

```text
snapper-timeline.timer -> stopped + disabled
snapper-boot.timer     -> stopped + disabled
snapper-cleanup.timer  -> remains enabled temporarily

btrfs-snapshot-create.timer -> enabled
btrfs-snapshot-prune.timer  -> enabled
```

This gives the desired gradual transition:

```text
old Snapper snapshots
.snapshots/381
.snapshots/382
.snapshots/383
        |
        | existing Snapper cleanup policy
        v
   naturally age out

new native snapshots
@snapshots/@data/20261008-070000Z
@snapshots/@data/20261008-080000Z
@snapshots/@data/20261008-090000Z
        |
        | native GFS pruning
        v
 timestamp-only managed history
```

The native manager never deletes a legacy Snapper snapshot. Snapper cleanup remains solely to retire legacy media. Once both hosts have no legacy snapshots requiring Snapper, a later step in this feature removes the package/configuration and obsolete Playbooks helpers.

## Synology NAS

Synology remains outside 0035 implementation scope.

DSM already owns its Btrfs snapshot metadata, timestamp-oriented naming, scheduling and retention. 0035 must not create/delete subvolumes inside Synology's internal snapshot locations or attempt to make DSM consume the Linux manager's metadata.

The systems cooperate only at the policy level:

```text
Synology NAS -> DSM/Snapshot Replication
mars         -> native Playbooks Btrfs snapshot manager
backup       -> native Playbooks Btrfs snapshot manager
Diaries      -> schema-2 complete-backup manager (0034 for Btrfs awareness)
```

## Safety boundaries

The manager must fail closed when:

- a configured source is not Btrfs;
- a source is not a Btrfs subvolume;
- the managed repository root is not a Btrfs subvolume;
- source and repository are not on the same Btrfs filesystem;
- a timestamp destination already exists;
- any native `btrfs` command fails;
- another create/prune operation already holds the manager lock.

Pruning is constrained by both repository location and timestamp-name syntax. Unrelated directories, Snapper numeric IDs, Diaries backup directories and Synology snapshots are not eligible.

## Rollback

Rollback does not require deleting new timestamp snapshots.

If the native manager proves unsuitable:

1. stop/disable `btrfs-snapshot-create.timer` and `btrfs-snapshot-prune.timer`;
2. re-enable the existing Snapper configurations and `snapper-timeline.timer`/`snapper-boot.timer` where desired;
3. leave already-created timestamp snapshots read-only until an explicit retention decision is made.

Do not automatically translate native timestamp snapshots back into Snapper numeric snapshots.

## Implementation state

Source implementation has been prepared for both hosts:

- the shared `roles/snapshots` role now installs the native manager, configuration and systemd timers;
- `mars` continues to consume that role from `local-backup`;
- `backup` now consumes the same shared role instead of its duplicate Snapper provisioning path;
- the role preserves Snapper cleanup during migration while disabling new Snapper timeline/boot creation;
- a permanent regression test exercises GFS selection, namespace separation and Playbooks wiring;
- Python compile, regression and YAML parse checks pass in the prepared source.

The feature remains **In progress** until live state is captured and the new implementation is deployed/rehearsed on `mars` and `backup`.

## Acceptance criteria

- [ ] Current live Snapper configuration and snapshot inventories are captured on both hosts before handover.
- [x] One shared Playbooks role implements new snapshot management for both `mars` and `backup`.
- [x] New snapshots use UTC `YYYYMMDD-HHmmssZ` names.
- [x] One create run uses the same timestamp for `root` and `@data`.
- [x] Native snapshots are read-only Btrfs subvolume snapshots.
- [x] The manager owns a separate `@snapshots` subvolume and never manages Snapper `.snapshots` content.
- [x] GFS-style hourly/daily/weekly/monthly/yearly retention is implemented and configurable.
- [x] Pruning never treats a numeric Snapper ID as a native managed snapshot.
- [x] Create and prune operations are serialised.
- [x] Multi-source creation failure rolls back only the new timestamp set from that invocation.
- [x] `backup` no longer carries a second active Snapper provisioning implementation.
- [x] Snapper timeline/boot creation is disabled only after native-manager preflight succeeds.
- [x] Existing Snapper cleanup is preserved during migration.
- [ ] `mars` runtime deployment creates and lists a valid timestamp snapshot set.
- [ ] `backup` runtime deployment creates and lists a valid timestamp snapshot set.
- [ ] Dry-run and controlled pruning are proven on both hosts.
- [ ] Existing backups remain accessible after snapshot creation/pruning.
- [ ] Legacy Snapper snapshots are shown to continue ageing out without new numeric timeline snapshots appearing.
- [ ] After legacy snapshots are gone, Snapper and obsolete source helpers are removed and the feature is closed.

## Dependencies

This feature depends on the existing Btrfs filesystem/subvolume provisioning used by the `btrfs` Playbooks role.

It does not depend on 0034 and 0034 does not depend on it.
