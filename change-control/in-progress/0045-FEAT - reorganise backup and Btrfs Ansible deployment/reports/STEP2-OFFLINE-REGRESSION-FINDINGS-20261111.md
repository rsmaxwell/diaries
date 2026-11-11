# 0045-FEAT — Step 2 offline regression findings (11 November 2026)

**State:** Step 1 CLOSED (`731c6a3`). Step 2 source-equivalence PASS; source reorganisation and offline validation still OPEN, not deployed. Playbooks pre-refactor revision `7dfa93fef6d975aa82f5f4cfdf54497b106e7645` (working tree contains intended Step 2 modifications).

## Operator evidence

- `note(20261111-120328).txt`: `mango` confirms `backup-collection.yaml` and `scripts/backup-collection.sh` exist, launcher shell syntax PASS. Existing and new Step 2 files are uncommitted; this is expected before source acceptance.
- `note(20261111-120403).txt`: Ansible syntax checks PASS for `backup-collection.yaml`, `btrfs-replication.yaml` and `snapshots.yaml`; replication 25 cases PASS, agreed-parent protection 5 PASS, shared retention PASS. Snapshot regression fails at its pre-refactor textual assertion `native timer enablement is behind explicit activation`. `roles/local-backup/tests/verify-diaries-pull.py` was not reached in this particular run.
- `note(20261111-120433).txt`: `mango` caller audit finds repository references in `scripts/local-backup.sh` and `scripts/remote-backup.sh`; dangling systemd symlinks caused two non-fatal `grep` warnings. No matching local cron/systemd/Jenkins references were reported among readable paths, but user crontabs, external schedules and Jenkins on other hosts are not exhaustively inspected. **Do not retire old entry points yet.**
- Previously accepted source-equivalence check confirms the refactored 24 snapshot and 36 native replication tasks are identical in ordered task semantics; role dispatch and new operator entry points PASS.

## Regression correction

`roles/snapshots/tests/verify-btrfs-snapshot-manager.py` formerly read only `roles/snapshots/tasks/main.yaml`; Step 2's main task file statically imports eight phase files, so that assertion no longer looked at effective task definitions. The correction recursively resolves *static* imports from the snapshot role, rejects missing, escaping, cyclic and import-level control changes, and verifies that exactly 24 effective tasks are present. The two timer-state systemd tasks must **each** retain `when: btrfs_snapshot_activation_enabled | bool` with both state and enabled settings. Other existing safety assertions now examine the reachable task files.

Offline verification on a copy of the 11:19 Playbooks source bundle plus the 27-file Step 2 refactor ZIP:

- Full snapshot-manager regression PASS.
- Other four permanent regression scripts PASS (replication 25 tests, protection 5 tests, shared retention, local-backup pull).
- Negative tests PASS: removing both timer guards, removing either one, or removing an imported file makes the snapshot regression FAIL as intended.
- No live host, package, systemd or snapshot changes were performed during this correction.

## Remaining Step 2 work

1. Apply the separate Playbooks regression-test correction to `/home/richard/playbooks` with Beyond Compare 4; rerun consolidated tests in the `mango` SSH terminal.
2. Complete external caller checks (including other users' crontabs and `pluto` Jenkins where applicable) before deleting old operator entry points.
3. Review source changes and capture acceptance evidence. Do not claim deployment equivalence until the accepted baseline has been compared after deployment.
