# 0034-FEAT — Step 10.2 frozen native Btrfs replication contract

**Date:** 2026-10-11  
**Status:** DESIGN FROZEN / IMPLEMENTATION NOT STARTED  
**Scope:** `mars` → `backup` whole-`@data` Btrfs send/receive. Step 10.1 inventory evidence supplied 2026-10-11.

## 1. Preserved boundaries

- `pluto` → `mars` remains the existing complete-backup publication/pull contract, including its schema-2 dataset and verification. This replication transport **does not inspect or require Diaries manifests**.
- `mars` retains `/media/usb/@data/backup` inside the writable `@data` subvolume. Its native timestamped read-only `@snapshots/@data/<timestamp>` snapshots remain the sendable source. Do not move or split `/backup` into a new subvolume.
- The initial rsync receiver `/@data/diaries-mars-replica` **cannot seed** Btrfs incremental replication and is not the new receive destination. The historical `/@data/backup` repository and both legacy Snapper namespaces remain out of scope for writes/deletion.
- No automatic enablement of a receiver service, backup native-snapshot timer, pruning, or Snapper handover as part of this design freeze.

## 2. Measured filesystem and subvolume identity

| Property | `mars` source | `backup` receiver |
|---|---|---|
| Device/mount | `/dev/sdb1` mounted at `/media/usb` (Btrfs top level 5) | `/dev/sda2` mounted at `/` (Btrfs top level 5) |
| Filesystem UUID | `72d1d8ea-900e-4fca-837f-1b1febec036c` | `b915f967-7cb4-4c14-b11b-f52209637a22` |
| Writable data subvolume | `/media/usb/@data`, ID `260`, UUID `fc4585b5-1649-b94c-bcb6-a9253c9cf080` | `/@data`, ID `275` (existing production data) |
| Native snapshot container | `/media/usb/@snapshots`, ID `20446` | `/@snapshots`, ID `55511` (existing 0035 manager) |
| Disk state from inventory | 3.64 TiB device; 479.47 GiB used | 1.81 TiB device; approx. 953 GB available (`df`) |

**Frozen baseline candidate:** `/media/usb/@snapshots/@data/20261009-170001Z` (subvolume ID `20453`, snapshot UUID `052c9376-0616-8b4a-9d28-f757b86fdec8`, parent UUID `fc4585b5-1649-b94c-bcb6-a9253c9cf080`, read-only). `btrfs subvolume show` reported **325.20 GiB referenced**, **16 KiB exclusive**. These are *not* measured send-stream bytes.

`mars` has a nested legacy `@data/.snapshots` subvolume, ID `262`. Sending the parent snapshot does **not** recursively send nested subvolumes; the chosen native snapshot sends the ordinary `@data` contents, including `/backup`, but not the nested legacy Snapper repository. Do not accidentally recurse or separately replicate historic Snapper snapshots. A source-content and nested-subvolume preflight remains mandatory.

## 3. Frozen source and receiver paths

| Item | Exact path / value |
|---|---|
| Source SSH alias | `mars` as resolved by `richard`'s SSH config on `backup` |
| Source snapshot root | `/media/usb/@snapshots/@data` |
| First full send | `/media/usb/@snapshots/@data/20261009-170001Z` |
| Destination parent | `/@data/mars-received/@data` on the verified `backup` Btrfs filesystem |
| Received snapshot | `/@data/mars-received/@data/<same-source-timestamp>` |
| Receipt/transaction state | `/@data/mars-received/.replication-state/` (outside received immutable snapshots) |
| Legacy rsync destination (excluded) | `/@data/diaries-mars-replica` |
| Historical repository (excluded) | `/@data/backup` |

The receiver parent is an **isolated directory**, not a second independently managed snapshot source. `btrfs receive` creates immutable received **subvolumes** as its children. Never receive into `/@snapshots` (0035 locally managed timestamp sets), `/@data/backup`, or the rsync replica. Protect the receiver root from symlink/path confusion and unexpected pre-existing files or subvolumes. The parent location is frozen but shall be provisioned only by the implementation/deployment steps, not by this document.

## 4. Privileges and transaction protocol

- An operator invokes replication on `backup` as `richard`. SSH connects to **`mars`** using `richard`'s existing SSH config; no root-over-SSH access or cloned private key is required.
- `btrfs send` and `btrfs receive` are privileged filesystem operations: define **auditable least-privilege local helper(s)** on the respective hosts for exact validated source/destination paths. Do not grant unrestricted remote shell or arbitrary `sudo btrfs` arguments. Implementation must specify how the receive process acquires privilege without exposing a general root command channel.
- Use an exclusive receiver transaction lock plus source-side send/prune exclusion or explicit source-snapshot leases. 0035 pruning on either side must respect pinned parent UUIDs and active transactions. The legacy `.btrfs-snapshot-writer.lock` controls rsync mirror writes; it is **not** the native receive-completion protocol.
- Preflight checks: source filesystem/subvolume UUID and read-only flag; exact timestamp and source path; receiver UUID/mount/capacity; destination absent; accepted-parent identities (incremental); matching snapshot scope; non-overlap with protected repositories; SSH and helper permissions; available space margin.
- Transfer exactly one native snapshot in a transaction. Observe exit codes for **both** stream endpoints and SSH (`pipefail`/explicit wait), and never treat the presence of a partially created subvolume as successful receive.
- Accept only after source identity matches destination `Received UUID` and received subvolume is read-only; record source UUID, parent UUID, snapshot name, destination path/received UUID, completion timestamp and verification outcomes in an **atomic receipt outside the received snapshot**. Content spot/metadata validation and independent restore tests are acceptance steps, not transport-specific Diaries checks.
- Interrupted, duplicate, wrong-parent, disk-full or suspicious receive: fail closed; preserve all previously accepted read-only received snapshots; quarantine/clean only a transaction-owned *unaccepted* destination after operator-safe identity checks. Do not auto-overwrite a valid snapshot.

## 5. Baseline, incrementals, and retention handshake

1. **Full baseline**: send the chosen read-only snapshot without a parent to the empty destination. Verify the destination's `Received UUID` equals `052c9376-0616-8b4a-9d28-f757b86fdec8`, read-only state, size/content and receipt. Keep both matching snapshots unchanged.
2. **Incremental**: choose a newer source read-only snapshot, require an **accepted** matching parent on `mars` and `backup`, then send with `btrfs send -p <source-parent> <source-child>` to `btrfs receive` at the same receiver parent. The *received* parent is selected using Btrfs UUID ancestry rather than matching names alone.
3. Pin the **latest accepted common parent** at both ends through retention; keep the active source child as needed. Advance the pin only after the newer receive and its receipt pass acceptance. Do not prune either endpoint's last available parent; failed incremental sends do not advance it.
4. The source snapshot manager owns timestamp creation and retention on `mars`; 0035 receiver retention owns native received snapshots on `backup`. No task may equate a 0035 local `/@snapshots` snapshot to an accepted native **received** parent. Retention must coordinate with in-flight send/receive, and preserve the parent even if standard GFS age policy would otherwise prune it.
5. A missed/removed parent, changed read-only state or diverged UUID lineage stops incremental replication and requires an explicitly approved new full baseline, not a best-effort diff or identity rewrite.

## 6. Operational gates and non-goals

**10.2 frozen design only:** no `btrfs send`/`receive` command has been executed or claimed successful; no host configuration changed and no timers enabled. Step 10.3 implements opt-in helpers and source regression, Step 10.4 executes and validates the full baseline, Step 10.5 validates incremental lineage. Step 10.6 tests recovery/retention and deploys operator tools (`diaries-backup-history` plus timestamp pruning on `mars` and `pluto`), and Step 10.7 performs an explicitly approved cutover. `pluto` may be ext4; the pruning utility must safely refuse native Btrfs pruning there.

**Acceptance evidence to capture:** preflight output; exact commands and tool versions; source/destination Btrfs UUIDs; source snapshot and received UUIDs; stream exit codes; read-only property; sizes and free space before/after; state receipts; failure/recovery and retention-parent tests; no change to `/@data/backup`, the rsync replica or legacy Snapper/timer state.

**Dependencies/uncertainties for Step 10.3:** receiver privilege-helper design and path allowlisting need implementation and regression; source `/backup` contents and any excluded nested volumes need final preflight; storage margin is provisional; source-snapshot prune pinning has not yet been demonstrated live.
