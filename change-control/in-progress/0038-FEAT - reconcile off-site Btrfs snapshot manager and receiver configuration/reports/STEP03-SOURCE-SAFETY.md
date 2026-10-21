# Step 3 — Source regression and receiver-safety review

**CLOSED: 20 October 2026. Source-level acceptance only.**

## Actual evidence and results

- `note(20261020-202013).txt` (`mango`): `git diff --check` clean; `bash -n` for both wrappers passed; remote Ansible syntax passed; `--list-hosts` contained **backup only**; `--help` displayed check-default/apply-explicit contract; invalid argument was rejected.
- `note(20261020-200913).txt` (`mango`): default remote wrapper's Ansible check-mode run ended `ok=22 changed=5 failed=0 skipped=13`; diff contained three executable updates, one manager JSON update, two new systemd unit files (5 changed Ansible tasks). No activation tasks were proposed.
- `note(20261020-202256).txt` (`mango`): `roles/remote-backup/tasks/main.yaml` includes `snapshots` with legacy Snapper timer retirement. Default `btrfs_snapshot_activation_enabled=false`, `btrfs_snapshot_require_verified_diaries=false`, `btrfs_snapshot_writer_lock_path=""`, `btrfs_snapshot_unattended_legacy_prune_enabled=false`. The manager template has replication protection and checkpoint holds required for `mars` only. Native receiver uses `/@data/mars-received/@data` and `/@data/mars-received/.replication-state`, independently from the manager's `/@snapshots` root.
- Accepted 0037-FEAT producer and 0038-FEAT Steps 1–2 baselines reused without another restore or transfer.

## Explicit scope / deferred evidence

The output demonstrates configuration intent, source hygiene and a dry-run only. It does **not** demonstrate deployed runtime success, receiver state after a real run, native endpoint safety under all adversarial inputs, or complete functional backup/restore. No source-changing regression harness was needed for this source-level acceptance. Those runtime and mutation-scope questions are controlled by Step 4 review, Step 5 rollout and Step 6 verification.

Known low-priority cleanup: duplicate `os`/`stat` imports in manager source; no bearing on documented gates and not changed by this package.

**Decision: Step 3 CLOSED. Proceed to Step 4 final Ansible review only.**
