# 0040-FEAT — Consolidated guarded-pruning integration gate

Status: **OPEN**. Production receiver pruning remains **disabled**.

## Accepted evidence (2026-10-23)

- `backup`: 19 received snapshots verified, 0 inventory problems, 0 retention candidates; no deletion authorized.
- Receiver read-only manager deployed and Ansible check-mode idempotent (`changed=0`).
- Manager/receiver writer-lock ordering verified by focused regression and live read-only inventory/plan.
- Simulated journal/recovery tests and isolated Btrfs test-subvolume deletion accepted (not production receiver execution).
- Renamed role `btrfs-replication` used on both source `mars` and receiver `backup`.

## Design blocker observed in source

`btrfs-native-push.py --prepare-prune-parent` durably pins source parent, then calls receiver for a check. That receiver check releases its exclusive `writer.lock` before returning. It explicitly reports `authorizes_prune=false`.

`btrfs-snapshot-manager.py receiver_guarded_prune` has an unconditional fail-closed exception: `receiver pruning blocked: live common-parent coordination not implemented`. The older destructive code below that exception is unreachable and MUST NOT be activated by deleting the exception. It does not use the newer fsync-safe journal helpers, and it does not establish a cross-host pin-lifetime contract.

## Single consolidated implementation contract

1. One sender-driven, root-constrained orchestration command on `mars`, with a serialization lock preventing competing source replication/pruning coordination. It obtains a verified common parent, persists its source protection, and invokes the receiver transaction without releasing the pin.
2. The receiver command acquires manager lock then the **existing** exclusive `/.replication-state/writer.lock` for the entire transaction. It checks a live source pin identity or a non-releasable protected parent token, and independently verifies received UUID, read-only property, receipt identity, and filesystem membership under lock.
3. Retention is recalculated *under lock*; protect current verified parent, latest receiver snapshot, accepted checkpoint holds `20261013-171228Z` and `20261018-165453Z`, and any source/receiver replication pins. Never delete with zero candidates; never override retention merely to create candidates.
4. Before EACH deletion: validate a candidate, create the fsync-safe pending journal, delete exactly that Btrfs subvolume, durably remove its matching receipt, clear the journal only when both are absent. A pending/ambiguous state fails closed and is classified by `receiver-recovery-plan` for explicit reconciliation.
5. Source pin remains present on any error or uncertain SSH result. Releasing it requires a separate, explicitly gated operation that establishes at least one **other** current shared parent; no automatic release on failure.
6. Install via existing `btrfs-replication`/`snapshots` Ansible roles. Default `receiver_prune_enabled=false`, no new timer until accepted. Deploy with `--check --diff`, verify, deploy, then idempotency.

## Focused acceptance (no full restore)

- Test valid zero-candidate plan (no deletions); invalid receipt and UUID (hard refusal); locked receiver and concurrent send (hard refusal/serialization); missing/stale source protection and attempted release (hard refusal).
- Disposable received Btrfs subvolumes with real receipt files: one eligible child deleted; protected parent and checkpoints survive; receipts/journal reconcile; interrupted stages remain diagnosable and restart-safe.
- Confirm receiver and sender installed manager source hashes and config, then one live source/receiver common-parent proof. Verify next normal incremental replication and receiver inventory. No forced deletion when retention gives zero candidates.

## Operational constraints

- Do not mutate `/media/usb/@snapshots`, `/@data/mars-received/@data`, receipts, legacy storage, timers or production checkpoints in tests.
- No production deletion or removal of the unconditional guard is authorized by this document.
- Keep `0040-FEAT` OPEN until the combined executor and tests pass; close only following controlled deployment and evidence review.
