# 0050 — Receiver layout, source regression and Ansible preview review (2026-11-17)

**Status: PRE-DEPLOYMENT ACCEPTANCE PASSED; LIVE DEPLOYMENT PENDING.** This is an evidence review, not a declaration that Step 3 or the feature is CLOSED.

## Observed baseline

- On `backup`, `btrfs-backup-status --local-only`: HEALTHY, 42 received sets, qgroups 45 total/0 stale, current agreed parent `20261117-030039Z`, previous `20261116-150008Z`. Receiver prune timer active; no destructive operation executed.
- The read-only layout check for received snapshot `20261116-150008Z` found both `backup/.diaries-snapshot-verified.json` and `backup/pluto/diaries-backup/dataset-manifest.json` and recorded their SHA-256 digests. Layout check exit 0.
- Source validation on `mango` verified controller commit `a81eafdf1fccf6bcd7d9d1b3dfa77143872682e8` and Playbooks base `a2508ad61f479c1b2bc20cb39896006c1f2906e1`. Intended 0050 Playbooks changes were uncommitted; generated Python `__pycache__` directories were untracked and are not part of feature changes.

## Tests and preview

- 0050 receiver fixture: 9 tests PASS, covering receiver-only backup, existing source compatibility, conflict, tampered/unsafe marker, empty inventory, full verify dispatch, show/path and occurrences.
- Real schema-2 verifier fixture: PASS for intact received dataset and correct refusal after test-file tampering.
- Permanent 0050 deployment contracts: 4/4 PASS; 0049 backup management 19/19 PASS; 0041 security 8/8 PASS; replication 25/25 PASS; existing history/status regressions PASS. The two `ERROR:` messages are expected rejection paths in tests that finished `ok`.
- `ansible-playbook btrfs-replication.yaml --syntax-check` PASS.
- `ansible-playbook btrfs-replication.yaml --limit backup --check --diff` PASS: `backup ok=33 changed=3 unreachable=0 failed=0 skipped=47`.
- The three proposed changes are the receiver read-only `diaries_history` configuration (shown twice in preview because two tasks use the same config destination) and updated/installed shared history/status commands. Existing independent verifier task reported `ok` (unchanged). The manager retains `verification.required=false`; no replication/retention/0041 security changes proposed.

## Next acceptance gate

Deploy only to `backup` with the normal Playbooks role, then capture installed CLI/config and live `diaries-backup-status`, `diaries-backup-history list --all/show/path/verify` results. Compare source and receiver inventories, including any naturally receiver-only backups; the disposable receiver-only fixture already passes without changing retention. Capture receiver parent/holds/prune preview and strict Ansible idempotence. Do not mark deployment PASS before reading its log.
