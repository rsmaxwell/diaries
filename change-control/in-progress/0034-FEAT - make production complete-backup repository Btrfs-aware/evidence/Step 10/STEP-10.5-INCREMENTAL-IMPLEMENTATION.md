# 0034-FEAT Step 10.5 — Native incremental replication implementation

Status: **SOURCE IMPLEMENTED; NOT YET ACCEPTED OR CLOSED** (12 October 2026).

## Baseline evidence already supplied

The full received baseline `20261009-170001Z` is accepted at `/@data/mars-received/@data/20261009-170001Z` with receipt `/@data/mars-received/.replication-state/20261009-170001Z.json`. Its receiver `Received UUID` matches source `052c9376-0616-8b4a-9d28-f757b86fdec8` and it remains read-only.

## Implementation contract

- `btrfs-native-pull --snapshot <NEW_TIMESTAMP> --preflight` selects the newest earlier locally receipted snapshot also verified on `mars` and `backup` to have matching source UUID and received UUID. A missing common parent fails closed when receipts already exist; the helper does **not** rebootstrap automatically.
- The endpoint on `mars` supports `incremental-source --snapshot <NEW_TIMESTAMP> --parent <PARENT_TIMESTAMP>` and validates both source and parent as read-only snapshots of the pinned `@data` origin before executing `btrfs send -p`.
- The receiver retains the existing fixed destination, target-absent assertion, single operator lock, independent sender/receiver exit codes and post-receive identity checks. It writes `btrfs-incremental` receipt atomically, including parent snapshot and parent source UUID, only after success.
- No automatic prune, deletion, scheduler or modification of `/@data/backup` or the obsolete rsync replica is introduced. Source and destination parent **must be protected against independent external cleanup** until Step 10.6 retention integration is proved.

## Tests performed offline

- `python3 -m py_compile` for both helpers.
- `python3 roles/remote-backup/tests/verify-native-btrfs-static.py`.
- `python3 roles/remote-backup/tests/verify-native-btrfs-incremental.py`.

## Still required for acceptance

1. Apply Playbooks patch and run `ansible-playbook --syntax-check native-btrfs.yaml` on `mango`.
2. Run `ansible-playbook native-btrfs.yaml --ask-vault-pass` and verify deployment on both machines.
3. Pick a **newer existing, readonly `@data` snapshot** on `mars`; do not delete the baseline. On `backup`, run `btrfs-native-pull --snapshot <NEW_TIMESTAMP> --preflight` and inspect the selected `parent` and `parent_uuid`.
4. Run an explicitly approved single live incremental; inspect received UUID, read-only flag, receipt `btrfs-incremental` and parent fields, and verify expected content.
5. Exercise fail-closed cases (missing/mismatched parent, pre-existing target, incomplete receive). Test pruning safety separately; **do not enable automatic cleanup yet**.

Note: the helper's `--full` is an explicit *new baseline only* option and will refuse execution if accepted receipts already exist.
