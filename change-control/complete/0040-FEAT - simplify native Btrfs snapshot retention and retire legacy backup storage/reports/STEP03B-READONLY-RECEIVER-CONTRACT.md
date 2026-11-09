# 0040-FEAT — Step 3B read-only receiver contract (23 October 2026)

Status: **IMPLEMENTED LOCALLY, NOT DEPLOYED. Step 3 remains OPEN.**

## Change

- Shared manager now accepts `mode` (`source` default for backwards compatibility; `receiver` opt-in).
- Each source may specify an absolute `snapshot_directory`; source mode retains old `snapshot_root/name` behaviour when absent.
- Receiver mode requires exactly one collection, an explicit directory and an absolute `receiver_state_dir`.
- `receiver-inventory` checks receipt schema, snapshot identity, destination, read-only property, and Btrfs Received UUID; missing or inconsistent state fails closed.
- In receiver mode all mutation commands (including create, prune, legacy and checkpoint modifications) are blocked. Receiver dry-run prune is intentionally not enabled yet.
- No Ansible deployment/configuration/timer changes and no production actions.

## Local tests

- `python -m py_compile roles/snapshots/files/btrfs-snapshot-manager.py`: PASS.
- `python tests/step03b-receiver-contract.py` (feature-local harness adapted for supplied source): PASS; receiver mutation denied, receipt mismatch rejected, source default compatibility validated.
- Existing `roles/snapshots/tests/verify-btrfs-snapshot-manager.py`: NOT PASSING on supplied bundle owing to pre-existing static launcher assertion `host="${1:-mars}"` and `mars|backup`. Requires investigation; not attributed to new manager logic.

## Security follow-up for Step 3C/4

A receiver read-only inventory is not yet a verified retention deletion plan. Before enabling any receiver prune, implement lock ordering with `.replication-state/writer.lock`, atomic receipt retirement/recovery, filesystem identity validation, common-parent protection, explicit holds, and adversarial regression tests. Keep existing source creation/pruning behaviour unchanged until controlled migration.

## Deployment

None. Promote the shared source file only after code review. Step 3 not closed.
