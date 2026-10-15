# 0035-FEAT Step 5 — Timestamp snapshot cleanup acceptance

**Status: CLOSED — 2026-10-15.**

## Scope and acceptance

- `mars`: retained GFS hourly 48 / daily 14 / weekly 12 / monthly 24 / yearly 5, minimum age 30 minutes. The source-contract test passed its fail-closed candidate preflight, read-only Btrfs verification, explicit `--apply` requirement and `pluto` refusal assertions.
- The guarded manager preflights **all** proposed members of paired timestamp sets, confirms a managed Btrfs subvolume with `ro=true` and refuses unsafe candidates before deletion. No deletion was attempted in this acceptance.
- `mars` live status reported `complete_timestamp_sets=52;incomplete_timestamp_sets=0`, production marker `backupId=20261015-003023Z`; dry-run returned `CHECKPOINT-HELD: ['20261013-171228Z']`, `REPLICATION-PROTECTED: ['20261015-030004Z']`, `RETENTION sets: total=52 keep=52 sources=2`, `Would delete 0 complete timestamp sets`.
- `pluto`: ext4 publication; both installation status and independently rerun Vault-authenticated dry-run reported `UNSUPPORTED: pluto filesystem=ext4 — no native snapshot pruning configured; no-op` (standalone `rc=0`). No ordinary directories were deleted.
- The `backup` receiver and accepted native-received snapshots are outside this feature step; no receiver pruning, local timer changes, historical Snapper deletion or legacy `/@data/backup` removal was authorised.

## Verification chronology

1. `python3 verification/0035-step5/verify-source-contract.py` — two PASS result groups.
2. `ansible-playbook verification/0035-step5/install-cleanup.yaml --ask-vault-pass --check --diff` — successful check mode; predicted `mars changed=2`, `pluto changed=1`, zero failures.
3. Actual install playbook — `mars ok=4 changed=2 failed=0`; `pluto ok=3 changed=1 failed=0`; `mars` and `pluto` status results as above.
4. `ansible mars -b -m command -a '/usr/local/sbin/diaries-snapshot-cleanup --host mars dry-run'` — `rc=0`, kept all 52 sets and preserved both protected timestamps.
5. Initial standalone `pluto` command was blocked by missing Vault secrets, **not** by cleanup execution.
6. Retried `ansible pluto -b --ask-vault-pass -m command -a '/usr/local/sbin/diaries-snapshot-cleanup --host pluto dry-run'` — `rc=0`, expected ext4 `UNSUPPORTED` no-op.

Source logs: `step5-mango-deployment-20261015-091640.txt`, `step5-pluto-dry-run-20261015-091743.txt`.

## Limitations preserved on closure

- With all 52 sets eligible for retention, this dry-run did not exercise an actual positive deletion plan or a real deletion. Neither is required for this restricted non-destructive gate; do not infer they have been proved.
- The prior broad `verify-btrfs-snapshot-manager.py` assertion about the `mars`-only `scripts/snapshots.sh` launcher remains a separate regression to reconcile.
- No automatic cleanup of receiver accepted snapshots, conventional ext4 backup generations, or historic numeric Snapper snapshots is enabled by Step 5.
- Explicit `prune --apply` is **not** authorised by this closure.

**Closure decision:** Step 5 CLOSED as a source-contract, guarded installation and non-destructive live verification gate. The wider 0035-FEAT remains IN PROGRESS.
