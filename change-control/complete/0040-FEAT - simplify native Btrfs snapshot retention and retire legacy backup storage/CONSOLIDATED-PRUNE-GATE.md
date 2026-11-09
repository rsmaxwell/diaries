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

## Current receiver-prune activation contract (revised 5 November 2026)

The old manager/writer-lock ordering, source-held challenge and fsync deletion-journal design described in October reports is historical. **Do not remove an installed fail-closed guard merely to enable pruning.** Replace old code coherently with the simplified contract in `reports/STEP12-3-SIMPLIFIED-DESIGN-DECISION-20261105.md`, then pass the independent receiver-pruning gate:

1. One shared retention-selector codebase, receiver configured for **receive-only**, with no competing pruner. Existing retention 48/14/12/24/5 and historical holds remain intact.
2. On the receiver, pruning and Btrfs receiving use the **same local non-blocking host lock**, held through each mutation. A collision logs and defers until the next timer; schedule the prune away from 03:30 UTC replication.
3. Under lock, re-read the receiver agreed-parent file and actual Btrfs identities, protect that common parent and every independent historical hold, and reject incomplete/invalid received subvolumes. If agreement with `mars` is in doubt, retain the possibly needed former parent rather than deleting it.
4. Recheck candidate identity and protection immediately before each locally selected `btrfs subvolume delete`; never delete by filename pattern alone. Ordinary logs record selections and results. No new multi-phase journal is required by this **replacement** design. Existing installed receipt/journal handling must remain operational until cutover and rollback acceptance.
5. Validate source and receiver protect the intended parent, compare non-mutating retention plans, run disposable Btrfs and collision regressions, review Ansible `--check --diff`, and obtain the separate operational go/no-go before enabling receiver deletion. Receiver prune remains disabled until explicitly accepted.

## Focused acceptance (no full restore) — current replacement design

- Source regressions: zero-candidate dry-run (no deletion), malformed or mismatched UUID/read-only metadata, parent absent/ambiguous, protected historical hold, and receiver lock contention all refuse mutation or defer.
- Disposable real-Btrfs snapshots: a clearly eligible child can be pruned; the locally pinned parent and independent historical checkpoint holds survive; an incomplete receive is never accepted as an eligible retained snapshot; receive/prune overlap backs off.
- Confirm installed sender/receiver shared-manager source revisions/config and review both current agreed-parent records. Observe one successful normal incremental after controlled rollout; check selected parent remains on both hosts. Do not force a deletion merely to create test candidates.
- Previously accepted restore and A→B transfer evidence is sufficient; no new complete restore is required solely for this gate.

## Operational constraints

- Do not mutate `/media/usb/@snapshots`, `/@data/mars-received/@data`, receipts, legacy storage, timers or production checkpoints in tests.
- No production deletion or removal of the unconditional guard is authorized by this document.
- Keep `0040-FEAT` OPEN until the combined executor and tests pass; close only following controlled deployment and evidence review.
