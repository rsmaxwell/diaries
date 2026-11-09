# Step 3C — Receiver retention planning (read-only)

Status: source implemented and local regression passed; Step 3 remains OPEN.

## Contract

- Adds `receiver-plan` to the single snapshot-manager executable. It is permitted only in `receiver` mode.
- Reuses the unchanged `retention_keep_set()` algorithm, including minimum age and hourly/daily/weekly/monthly/yearly buckets.
- First validates every timestamped received snapshot using its receipt, Btrfs received UUID and read-only flag; rejects missing, invalid and orphan receipt records.
- A historical receipt's `parent_snapshot` does not need to remain present for a retained snapshot to be valid.
- Always retains the most recent snapshot (existing algorithm), but **does not claim** that this alone proves a safe common replication parent on both hosts.
- Reports `RETAIN` or `CANDIDATE-NOT-AUTHORIZED`, with `executable=false`; it cannot remove a snapshot or receipt. Receiver `prune` and mutation commands remain prohibited.
- Host-specific current production receiver configuration and timer activation are deferred to later controlled gates.

## Evidence

Against the 0040 Step 3B manager baseline:
- `python3 -m py_compile roles/snapshots/files/btrfs-snapshot-manager.py` passed locally.
- `tests/step03b-receiver-contract.py` passed locally after the change.
- `tests/step03c-receiver-plan.py` passed locally, confirming shared retention selection, rejection of invalid identity and orphan receipts, and no mutation.

No production state was changed. Scripts and test outputs belong only under this feature directory; the one permanent modified source file is promoted separately via the Playbooks ZIP.

## Pending Step 3D

Coordinate receiver writer lock with receiver transactions; prove a common surviving incremental parent with source/receiver identity validation; implement auditable receipt/subvolume deletion transaction and interruption recovery. Do not enable deletion pending acceptance.
