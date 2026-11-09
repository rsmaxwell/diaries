# 0040-FEAT Step 4 — implementation and accelerated acceptance (24 October 2026)

**Status: technical acceptance PASS; formal closure ready on application of this evidence record.** Step 4 in IMPLEMENTATION-STEPS.md was originally a **source-only, no-deployment** gate; the actual rollout additionally installed the compatible manager on `mars`. This is a recorded scope deviation, not evidence of authorisation for later migration/retirement gates.

## Scope and changed files

Playbooks source modified on `mango` (tested working tree):
- `roles/snapshots/defaults/main.yaml`: required and creation source defaults remain `root`, `@data`.
- `roles/snapshots/files/btrfs-snapshot-manager.py`: configurable required/creation source lists, paired-history compatibility and guarded present-snapshot pruning.
- `roles/snapshots/templates/btrfs-snapshot-manager.json.j2`: emits the optional configuration contract.
- `roles/snapshots/tests/verify-0040-step04-migration.py`: regression fixture.
- `roles/snapshots/tasks/main.yaml`: fail-closed guard against generic snapshots role on `remote_backup` hosts, positioned before mutating tasks.
- `roles/snapshots/tests/verify-0040-receiver-role-guard.py`: regression for guard ordering and tagged runs.

Check the Git working-tree diff on `mango` before committing; no new committed revision is attested here. Prior clean baseline: `8d3e66d`.

## Accepted evidence (user-supplied terminal logs)

- `note(20261024-213017).txt`: focused `@data`-only/legacy paired/default/invalid-config regression PASS; all 8 Step 3 non-destructive coordination scripts PASS with sudo; `git diff --check` PASS.
- `note(20261024-213622).txt`: `snapshots.yaml --limit mars,backup --tags snapshots --check --diff` showed `mars` manager/config changes and **unsafe proposed source-mode overwrite of backup's receiver config**. No deployment to backup was performed.
- `note(20261024-214041).txt`: targeted production deployment on `mars` via Ansible PASS (changed=2), verification VALID, 61 complete paired timestamp sets and zero incomplete.
- `note(20261024-214311).txt`: deployed `mars` config remained `required_snapshot_sources=['root','@data']` and `creation_source_names=['root','@data']`; repeat `--check --diff` reported `changed=0`.
- `note(20261024-214855).txt`: receiver guard static regression PASS, syntax-check PASS, `mars` tagged check/diff `changed=0`.
- `note(20261024-214956).txt`: `snapshots.yaml --limit backup --tags snapshots --check --diff` intentionally FAILED at the **first** snapshots-role guard (`REFUSED: the generic snapshots role must not run on remote_backup hosts`), `changed=0`; no install, configuration or service tasks executed.

## Safety boundaries and outstanding issues

- `backup` receiver-mode deployment is owned by the dedicated `native-btrfs.yaml` path; generic `snapshots.yaml --limit backup` is intentionally rejected.
- Receiver pruning remains disabled (`receiver_prune_enabled=false` was verified earlier); no receiver-prune activation was authorised by Step 4.
- `mars` continues to create and require **paired** `root` and `@data` snapshots; the `@data`-only cutover is **not** active.
- `mars` qgroup status warning: 218 stale / 371 total; tracked separately and not treated as solved by this feature.
- The full cross-host disposable deletion rehearsal was waived under the separately accepted Step 3 accelerated-path decision. Do not describe it as tested.
- Subsequent Step 5 adversarial regressions, Step 6 plans, Step 7 rollout review, and Steps 10–11 irreversible retirement approval remain distinct gates.

## Decision

The Step 4 implementation and its additional constrained `mars` deployment are accepted based on the listed evidence; the unintended `backup` diff has been mitigated by an experimentally verified fail-closed guard. **Step 4 may be marked CLOSED once this report is applied and its change-control status reconciled.** No authorisation is given for root snapshot deletion, retention cutover, receiver pruning or legacy retirement.
