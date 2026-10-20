# Step 12 — `legacy-prune` preview correction (20 October 2026)

## Observation

Production command `sudo btrfs-snapshot-manager legacy-prune --legacy-map root=root --legacy-map @data=@data --max-delete 1` returned `ERROR: unattended legacy pruning requires explicit --execute` (exit code 2). No deletion occurred.

## Correction

`legacy-prune` without `--execute` now prints a bounded, read-only preview of sorted `WOULD-DELETE` candidates (up to `--max-delete`), announces `NO DELETION AUTHORISED`, and returns successfully. The inventory/retention selection is performed by the same `legacy_plan` function used by execution. Invalid bounds and missing explicit mappings still fail closed. `--execute` retains per-candidate plan revalidation, Btrfs identity checks and the bounded deletion limit.

The `btrfs-snapshot-prune.service` opt-in unattended command still includes `--execute`; its default activation flag remains false. No timer or production activation is changed by this package.

## Validation (source environment)

- Python compilation: passed.
- `verify-legacy-prune-preview.py`: preview no mutation; invalid bounds/mappings; execution revalidation and one deletion with mocked commands; changed plan fails closed: passed.
- Existing `verify-unattended-legacy-prune.py`, `verify-btrfs-snapshot-manager.py`, `verify-qgroup-status.py`: passed.

## Remaining acceptance

Apply Playbooks patch to mango, repeat tests, deploy only manager binary to mars with Ansible `backup=yes`, verify checksum matches, run production preview **without** `--execute`, inspect scheduler and protection baseline. Unattended pruning remains DISABLED until separately reviewed and approved for activation. No production deletion has been authorized by this source correction.
