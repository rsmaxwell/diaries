# 0036-FEAT Step 8 Gate B — rollback preparation

**Status: CLOSED — accepted 2026-10-16.** No production mutations were made by this package. Gate A passed on 2026-10-16. Gate C remains **not started**; this evidence closure does not authorise operational cutover.

## Gate A confirmed live state

| Host | Existing publication or mount | Timer |
|---|---|---|
| pluto | `/home/richard/projects/diaries/data/diaries-backup` → `.diaries-backup-generations/20261016-003019Z`; read-only CIFS `/mnt/nas-diaries` | `diaries-complete-backup-publish.timer` enabled, local 01:30 BST on Oct 16 |
| mars | `/media/usb/@data/backup/pluto/diaries-backup` → `.diaries-backup-generations/20261016-003019Z`; marker `/media/usb/@data/backup/.diaries-snapshot-verified.json`, lock `/media/usb/@data/backup/.btrfs-snapshot-writer.lock` | pull 01:30 UTC; snapshots hourly, prune at :15; Btrfs push 03:30 UTC |
| backup | `/` is Btrfs on `/dev/sda2` | no source pull or source snapshot schedule indicated by Gate A |

The symlinks are not yet relocated and their targets must be checked again immediately before any cutover. In particular, do **not** assume the dated generation will still be the current one on cutover day.

## Collect read-only Gate B evidence on mango

```bash
cd ~/playbooks
mkdir -p ~/0036-gateb-evidence
for host in pluto mars backup; do
  ssh "$host" "bash -s -- $host" < scripts/diaries-0036-step8-gateb-rollback-inventory.sh \
    > "~/0036-gateb-evidence/${host}-inventory.txt"
done
sha256sum ~/0036-gateb-evidence/*-inventory.txt
```

Also record the Git SHA and clean/dirty state of Playbooks and Diaries *locally*, and archive the relevant deployed Ansible variable precedence and **non-secret** overrides privately. Never publish vault content, full systemd `Environment=` or NAS credentials in evidence logs.

## Acceptance requirements before Gate C

1. Confirm current `pluto` and `mars` publication links exist, are genuine symlinks, and resolve **within their own `.diaries-backup-generations/` trees**. Record symlink target strings, resolved paths, owners and last verified schema-2 identity. Abort on links that are absent, escape their managed tree or change unexpectedly.
2. Identify a **verified, read-only** `mars` Btrfs historical snapshot and its schema-2 backup ID / manifest digest; confirm the matching off-site `backup` received snapshot and valid receiver receipt / protection ancestry from existing inspection tools. Record concrete identifiers and evidence, not inferred success.
3. Confirm host-side full backup, pull, snapshot, prune and push timers, deployed scripts, unit hashes, path permissions, marker/lock, expected database and Files selector. Keep private configuration copies available for rollback. Review 01:30 BST vs 01:30 UTC scheduling across the October 25 UK clock change.
4. Confirm original publisher and receiver scripts, generation targets and data have been retained. Arrange a rollback-alias name **without creating it yet** and confirm free space for fixed directories. Confirm no writer currently holds the shared lock before a future maintenance window.
5. Approve exact maintenance window and rollback operator. No renames, writer activation or timer suspension as part of Gate B inventory.

## Future controlled migration — NOT EXECUTE IN GATE B

- Gate C begins by stopping conflicting timers/services and checking outstanding operations. Immediately re-read each symlink and preserve each link and its still-existing target under a specifically named rollback alias **on the same filesystem**, with current path/target recorded; never overwrite an existing alias. Do not delete or move the generation target.
- Create fixed plain directories only at verified managed publication paths, using the same owners and marker/lock boundary. On `pluto`, enable guarded fixed capture and accept a complete schema-2 manifest. On `mars`, enable fixed receiver, verify independent schema-2 and eligibility before snapshotting. These are separate, gated operations.
- **Rollback trigger:** failure of capture, pull, verification, snapshot or replication receipt. Freeze all new writers first. Preserve incomplete fixed directory by renaming to a diagnostic name without deleting content; atomically restore each original symlink and its original timer/configuration, only after verifying its saved target still exists. Check historical restore and marker correctness before resuming old schedules.
- Do not use `rm -rf`, `rsync --delete` on a generation/snapshot, synthesize a marker, or remove remote receipts. All legacy generation deletion requires later separate approval.

## Accepted Gate B runtime evidence — 2026-10-16

**Decision: CLOSED — read-only rollback preparation accepted.** Gate A inventories, the Gate B collector output from all three hosts, privileged Btrfs identity inspection, a production receiver receipt, and both repository committed baselines were reviewed. This is an evidence and planning closure; the production writer/pull/snapshot/push configuration has **not** been changed.

### Production publications and rollback targets

- `pluto`: `/home/richard/projects/diaries/data/diaries-backup` is a symlink to `.diaries-backup-generations/20261016-003019Z` (captured 2026-10-16 14:02:41 UTC). The target resolves inside `/home/richard/projects/diaries/data/.diaries-backup-generations/` and exists as a directory.
- `mars`: `/media/usb/@data/backup/pluto/diaries-backup` is a symlink to `.diaries-backup-generations/20261016-003019Z` (captured 2026-10-16 14:02:43 UTC). The target resolves inside `/media/usb/@data/backup/pluto/.diaries-backup-generations/` and exists as a directory. Its `/media/usb/@data/backup/.diaries-snapshot-verified.json` marker and `.btrfs-snapshot-writer.lock` are ordinary files.
- Preserve **both** generation trees and record each currently resolved symlink again at Gate C immediately before any rename; the daily backup may advance the generation ID.

### Known-good off-site replication checkpoint

**Snapshot:** `20261016-030037Z` (`@data`). This is historical 0034/0035 production evidence, not a new 0036 fixed-workflow replication test.

| Property | `mars` source | `backup` received |
|---|---|---|
| Snapshot | `/media/usb/@snapshots/@data/20261016-030037Z` | `/@data/mars-received/@data/20261016-030037Z` |
| Subvolume ID | `20753` | `55787` |
| UUID | `e1735c53-0831-764d-ac07-672de8dbe81e` | `f67dbc87-3329-6e41-8311-61b58a85217f` |
| Received UUID | none (native source) | `e1735c53-0831-764d-ac07-672de8dbe81e` |
| Flags | `readonly` | `readonly` |

The receiver acceptance record was directly inspected at `/@data/mars-received/.replication-state/20261016-030037Z.json` and states:

- `schema=1`, `transport=btrfs-incremental`, `snapshot=20261016-030037Z`;
- `source_uuid=received_uuid=e1735c53-0831-764d-ac07-672de8dbe81e`, matching the independent `btrfs subvolume show` evidence;
- `parent_snapshot=20261015-030004Z`, `parent_source_uuid=6f44e0e0-1968-6e4d-a3bd-9f77d71e9a47`;
- `destination=/@data/mars-received/@data/20261016-030037Z`;
- `completed_at_utc=2026-10-16T03:32:02.082660+00:00`, `read_only_verified=true`;
- `source_send_exit=0`, `receiver_receive_exit=0`.

This verifies both the physical received UUID and the recorded application-level acceptance. It does **not** assert that a fresh database restore was rerun during Gate B.

### Deployed configuration and version evidence

- `pluto` `diaries-complete-backup-publish.timer` enabled (next 2026-10-17 01:30 BST). Timer SHA-256 `390783016e523426bf79bdb8f0a1de17b501d479249a4a0336ca12e31e8901ac`, service SHA-256 `3242b2a883d3e83d5525be6c941edc8b956869e72ce738e9f113af914d12788a`. Independent NAS CIFS `/mnt/nas-diaries` is read-only.
- `mars` `diaries-pull.timer` enabled (next 2026-10-17 01:30 UTC); snapshot create/prune timers and `btrfs-native-push.timer` enabled. Pull timer SHA-256 `f48a20e7d6c6e9ac75c9f125266c46f631e3748c523b356fd25be65aea45591b`, pull service SHA-256 `d8bf17643c6e04f64a3fd07d5f250659d5c8a6643e8d2ed5b24ba6bd25fff35e`.
- `backup` is on Btrfs; source snapshot timers disabled as expected. Non-root inventory could not enumerate all Btrfs subvolumes (`Operation not permitted`); follow-up `sudo btrfs subvolume show/list` succeeded. This is not a blocker.
- Inventory SHA-256 on `mango`: `pluto` `b57c8d41a122debec444a0df74061c577d25dd55876f1a9596226c35b637b2b8`; `mars` `b9dc39e126a2220eb8523f5b927bffe7a006a2b8dad24bb48bd747cda1732eaa`; `backup` `a5307d4238554df65a707885f17115c5156664649ea9b987488cf1cdd7752650`. Original inventories remain on `mango` at `~/0036-gateb-evidence/`.
- Playbooks HEAD: `0bf68c5a46eed4975a002b55f29ba1bb94dfbb10` (2026-10-15 11:28:41 +0000, `0035-FEAT Step 8`). Diaries HEAD: `0ffb5d89202545ca139d83e7ea4c2f109bbfdd84` (2026-10-15 12:36:53 +0100, `0035-FEAT Step 9b`). These are **committed baselines**, not proof the applied 0036 working trees are clean; keep the actual uncommitted patches/configuration for rollback.

### Gate B acceptance and Gate C boundaries

**Gate B CLOSED.** The current symlink targets, installed units, eligible recovery checkpoint, matching off-site received UUID and validated receiver receipt, operator runbook and repository committed baselines are sufficiently documented. Reuse this evidence; no further Gate B rehearsal is requested.

**Gate C NOT STARTED.** Do not stop timers, migrate either publication symlink, create fixed production directories, enable fixed capture/pull, or remove generations on the strength of Gate B closure alone. At Gate C: reconfirm fresh symlink targets, ensure no outstanding writers, capture effective configuration and any uncommitted changes, agree the maintenance window and operator, preserve rollback aliases and historical checkpoints, then follow the approved staged migration/verification sequence. Check the 2026-10-25 BST/GMT schedule relationship before unattended operation. Gate D observation and Gate E retirement remain open.
