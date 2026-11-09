# 0040-FEAT Step 1 — Frozen baseline and closure report

**Status: CLOSED — 23 October 2026.** Read-only inspection and source reconciliation accepted; no 0040-triggered production change or deletion. Operator terminal outputs collected in the Step 1 evidence files. This record replaces the earlier OPEN progress interpretation.

## Source identity and install reconciliation

- Diaries `main`: `f01bd76a6d5fbb42bb90979d9d13857b9b8aa4be` (clean, `0040-FEAT - start`).
- Playbooks `main`: `0d487706518fa73bf621545906f3deea97bce9b2` (clean, `0040-FEAT - start`).
- Playbooks `roles/snapshots/files/btrfs-snapshot-manager.py` SHA-256: `d564d2defacea27ffc59cf77be42dff69d1cf5ff5666ee67e6a78388e7ef5e18` (54,052 bytes). Installed `backup` manager matches this exactly.
- Installed `mars` `/usr/local/sbin/btrfs-snapshot-manager` SHA-256: `fae7bbea115c82380e4f4ebd425a8b2962fdb0ff4ec62c111f7a299f388d59e0` (53,310 bytes). Direct read-only diff identified the only changed region: the 0039-DEF qgroup-status parsing improvement in source revision `e685066` (22 October). No snapshot creation/prune/hold change appeared in the diff. This known deployment drift is recorded for future controlled parity, not repaired during Step 1.

## mars as observed

- Kernel `6.8.0-138-generic`; btrfs-progs `6.6.3`. `/media/usb` device 3.64 TiB, used 481.55 GiB, estimated free 3.17 TiB.
- Manager: 61 complete paired `root` and `@data` sets; 0 incomplete; hourly 48, daily 14, weekly 12, monthly 24, yearly 5, minimum age 30 min. Creating/pruning active hourly; native push scheduled 03:30 UTC.
- Current verification marker `valid` for Diaries dataset backup ID `20261023-003234Z`; verification and writer locks configured.
- 283 qgroups, 136 stale at capture; record only, do not combine qgroup repair with the 0040 baseline.
- Explicit checkpoint holds: `20261013-171228Z` (recovery checkpoint), `20261018-165453Z` (permanent mango evidence archive). Existing `.replication-protection.json`, `.checkpoint-holds.json` and `.native-push.lock` are part of the source protection contract.
- Legacy prune timer **enabled** at 08:20 UTC and confirmed deleting one legacy `@data` Snapper snapshot ID 19725 on 22 October. Must not silently remove during shared-manager refactor.
- Root subvolume `/media/usb` contains only nested `@data` and `@snapshots` entries. Inspected read-only root snapshot `20261023-070038Z` contains only empty placeholders; Btrfs shows 16 KiB referenced/exclusive. Explicit scope extension approved: eventually stop creating and retire `mars` root snapshots, without compromising `@data` or holds.

## backup as observed

- Kernel `6.8.0-147-generic`; btrfs-progs `6.6.3`. Device 1.81 TiB, used 1.52 TiB, estimated free 290.51 GiB; qgroups total 143, stale 0.
- Current manager is configured for unused `/@snapshots/{root,@data}` and reports **zero managed snapshots**; receiver has **19** read-only received `@data` subvolumes (9–23 October 2026). No received-snapshot prune timer scheduled; stale-qgroup timer enabled. Receiver-pruning authority needs to be introduced explicitly, without duplicating existing receiver semantics.
- Receipts for 19 snapshots are in `/@data/mars-received/.replication-state` with a mode 0600 `writer.lock` and mode 0700 containing directory (richard:richard). Recent receipts confirm send/receive exit 0 and `read_only_verified=true`.
- Latest confirmed incremental chain: `20261022-082824Z` → `20261022-120034Z` → `20261023-030037Z`. Source UUIDs for final two timestamps match both receipt `received_uuid` and received Btrfs `Received UUID`; all inspected subvolumes read-only. Distinct local subvolume UUIDs are expected. Keep common-parent and lock rules when pruning.
- `/@data/backup` exists (~326 GiB `du`). `/@data/.snapshots` holds 32 read-only Btrfs Snapper subvolumes (~9.9 TiB cumulative `du`, not exclusive). `/.snapshots` has legacy root recovery points (~768 GiB cumulative `du`). `/@snapshots/@data` and `/@snapshots/root` empty (`du 0`). These logical `du` totals cannot be added to estimate reclaimable physical space.
- Snapper configs `root` and `@data` present. Snapper APT hook `/etc/apt/apt.conf.d/80snapper` creates `pre`/`post` root snapshots; `snapperd` enabled even though scheduled Snapper/legacy create/prune timers are disabled. `/.snapshots` requires distinct Step 2 decision.

## Completeness and acceptance

- Recorded host identity, filesystem/qgroup status, manager binaries and configs, timers, source holds and locks, received snapshot IDs/receipts, representative source/receiver UUID and parent relationship, legacy paths and snapshot IDs, Snapper APT hooks and source-to-installed revision drift.
- A complete per-subvolume **UUID deletion manifest is deliberately deferred to Step 10**, immediately before any destructive operation, to avoid stale identifiers and ensure individually reviewed deletion candidates. Baseline identifies the population and representative identities, not a frozen destructive plan.
- No `@data` receiver history, receipt or holds were modified; no full restore repeated.
- **Decision: Step 1 CLOSED. Step 2 OPEN.** This is not approval for deleting any historical data or disabling any timer. Future acceptance must explicitly address `/.snapshots`, unique historic Diaries generations, source/receiver retention, legacy `mars` prune transition and destructive rollback constraints.
