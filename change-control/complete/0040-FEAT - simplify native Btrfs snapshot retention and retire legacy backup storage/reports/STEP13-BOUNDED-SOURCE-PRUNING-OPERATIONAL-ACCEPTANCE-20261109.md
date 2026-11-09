# 0040-FEAT — Step 13 bounded source-pruning operational acceptance

**Decision date:** 9 November 2026 (UTC)
**Scope:** `mars` source-side `@data` snapshot pruning and hourly schedule.
**Decision:** **Operational acceptance PASS** for capped, unattended source pruning. **Formal Step 13 closure remains pending** evidence import into the authoritative Windows Diaries checkout and documentation/repository reconciliation.
**Feature:** remains **IN PROGRESS**; Step 14 whole-feature closure is separate.

## Confirmed source and configuration

- Playbooks branch `main`, commit **`6ccbf73`** (`0040-FEAT: Bound and safely gate source snapshot pruning`), pushed and deployed to `mars` on 8 November 2026. Tests, Ansible syntax, `--check --diff` and post-install idempotency (`changed=0`, `failed=0`) passed.
- The service installed at `/etc/systemd/system/btrfs-snapshot-prune.service` runs `/usr/local/sbin/btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json prune --max-delete 10`. The limit is 1–10; the scheduled default is **10**.
- The authoritative `mars` inventory override is `/etc/ansible/host_vars/mars/local-backup.yaml`: `btrfs_snapshot_activation_enabled: true`, `btrfs_snapshot_prune_activation_enabled: true`, `btrfs_snapshot_prune_on_calendar: "*-*-* *:45:00"`. The deletion cap remains a Playbooks snapshots-role default, not a host-vars entry.
- Hourly creation remains at `:00`; bounded pruning is **enabled and active** at `:45` with `Persistent=true`. Native replication sender remains scheduled for 03:30 UTC. The receiver-pruning schedule and retention policy were not changed by this increment.
- The existing GFS retention policy was preserved: 48 hourly, 14 daily, 12 weekly, 24 monthly, 5 yearly, minimum snapshot age 30 minutes. Checkpoint holds and agreed-parent protection remain mandatory.

## History of deployment and acceptance

1. **8 November, preflight:** initial source pruning paused since 30 October; unbounded dry run identified 204 of 273 snapshot sets eligible for deletion. The protected parent, prior and held timestamps were excluded from the deletion plan. Capped tests passed.
2. **8 November, source deployment:** the bounded manager, service and explicit stopped/disabled pruning gate deployed from `6ccbf73` (`failed=0`), with Ansible idempotency (`changed=0`). Capped dry run selected 10 of 208 eligible sets. The pause remained enforced across reboot until separate operator approval.
3. **Operator approval and activation:** the operator approved enabling hourly pruning with maximum 10 snapshot-set deletions per run, retaining all existing protections. The initial inventory edit attempt failed safely because it assumed a single host-vars YAML file; actual inventory is `/etc/ansible/host_vars/mars/local-backup.yaml`. A subsequent verification attempt as `root` lacked `/root/.vault_pass.txt`; running as `richard` resolved it. Neither pre-activation failure performed pruning.
4. **8 November 14:43:17–14:43:24:** first live activation-triggered prune **PASS**; 10 complete timestamp sets removed; no incomplete sets; sender/receiver parent and prior identities agreed after deletion.
5. **8 November 15:15 and other `:15` runs:** several scheduled prunes **deferred as service failures** (`ERROR: another operation holds /run/lock/btrfs-snapshot-manager.lock`, exit status 2). A correlated snapshot-creation run started 15:00:11 and finished 15:17:22, proving at least one real schedule overlap. The shared lock rejected concurrent operation and protected state.
6. **Overnight 8–9 November:** multiple successful scheduled prunes removed 10 sets per run, while expected lock-contention failures were documented. Overnight replication advanced: on 9 November the sender and receiver agreed on current parent `20261109-030030Z` / UUID `239f29b4-9577-0e4b-b4f2-5f5cb9f7484c`, prior `20261108-030011Z` / UUID `dcb7bae6-d1b0-824c-9d2d-1f5c7b8a2d58`.
7. **9 November ~07:55:** Ansible preview confirmed exactly one changed unit, from `OnCalendar=*-*-* *:15:00` to `OnCalendar=*-*-* *:45:00`. Deployment **PASS** (`changed=1`, `failed=0`); installed unit and `--max-delete 10` read back correctly; sender/receiver parent consistency **PASS**.
8. **9 November 08:45:39–08:51:53:** first normal `:45` run **PASS**. Service ended `Result=success`, `ExecMainStatus=0`, `ActiveState=inactive`. Retention plan `total=156 keep=69`, `PRUNE-CAP eligible=87 selected=10 max_delete=10`; journal recorded **10 actual deletions**, then `Deleted 10 complete timestamp sets` and successful unit completion. Post-run `complete_timestamp_sets=146`, `managed_snapshots=146`, `incomplete_timestamp_sets=0`, verified Diaries production marker. Next trigger 09:45 UTC. Both existing checkpoint holds were printed in the plan.

## Explicit operational acceptance

**Accepted:** capped pruning implementation, explicit activation safety, controlled first live deletion, hourly schedule change to `:45`, first normal scheduled `:45` service completion, retention/hold verification, and sender/receiver parent consistency already accepted before/after the transition. Existing accepted integration/restore evidence is sufficient; no expensive replay is required.

**Do not misstate:** successful collection of a journal is not itself proof of a successful prune. The 9 November 08:47 intermediate check observed `ActiveState=activating` and temporary counts `complete=153` vs `managed=149` while deletion was active. The 08:53 final check established clean completion with **146/146**. The previous `:15` lock-contention failures remain recorded historical failures, not silently reclassified as successful runs. A single successful `:45` run demonstrates acceptance of the revised schedule, not a guarantee that all future lock overlaps are impossible.

## Outstanding items and closure boundary

- **0039-DEF stale qgroup recurrence:** `qgroups_stale` was 456 before pruning restarted, 596 on 9 November 08:08, and **606** after the accepted 08:45 run; `qgroups_under_deletion=0`, `qgroups_status=warning`. This defect remains open to separate investigation and recurrence prevention; it was **not fixed** by Step 13, and no qgroup cleanup/destructive action is implied by this acceptance.
- **Formal Step 13 closure remains pending:** import all raw `evidence/Step 13/` logs from `/home/richard/diaries` on `mango` into the authoritative Windows Diaries checkout, preserve earlier failed attempts and correction evidence, verify Git status and reconcile the feature's `README.md`, `IMPLEMENTATION-STEPS.md`, `PROMOTION-MANIFEST.md` and relevant operator runbooks against **current** checked-out versions. Confirm housekeeping candidates (including any tracked `.pre-wrapper-tags` backup) are unreferenced before changing them.
- **Step 14 remains OPEN:** after Step 13 is formally closed and repository/evidence promotion is reconciled, perform final whole-feature closure decision and move the feature directory from `change-control/in-progress/` to `change-control/complete/` only on that accepted decision.
- Rollback of automated source pruning: set `btrfs_snapshot_prune_activation_enabled: false` in `/etc/ansible/host_vars/mars/local-backup.yaml` on `mango` and reapply the snapshots role; for an immediate stop, `ssh mars 'sudo -n systemctl disable --now btrfs-snapshot-prune.timer'`, followed by the inventory correction. Do not alter checkpoint holds or agreed-parent files.

## Raw evidence on mango to be imported intact

The primary raw logs are already held in `change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/evidence/Step 13/` on `mango`. Preserve this entire directory, including (among others):

- `step13-source-pruning-readiness-20261108.txt`, `step13-source-pruning-dry-run-20261108.txt`
- `step13-capped-source-deployment-preview-20261108.txt`, `step13-capped-source-deployment-20261108.txt`
- `step13-source-pruning-activation-20261108-140440.txt` (safe pre-activation failure), `step13-source-pruning-activation-rerun-20261108-141226.txt` (vault account correction)
- `step13-source-pruning-activation-preview-20261108-142604.txt`, `step13-source-pruning-live-20261108-144221.txt`
- `step13-first-live-prune-verification-20261108-150120.txt`, `step13-second-prune-and-qgroups-20261108.txt`, `step13-prune-1515-failure-diagnostic-20261108.txt`
- `step13-source-lock-contention-20261108.txt`, `step13-creation-prune-lock-correlation-20261108.txt`
- `step13-prune-schedule-45-20261109-075108.txt` (preflight script mistake), `step13-prune-schedule-45-preview.txt`, `step13-prune-schedule-45-deployment-20261109-075503.txt`
- `step13-unattended-pruning-followup-20261109-080857.txt`, `step13-revised-schedule-acceptance-20261109-084716.txt`, **`step13-prune-0845-completion-20261109.txt`** (final accepted service proof)

This report is an interpreted acceptance record, not a substitute for the original raw terminal evidence, nor a claim that those logs have already reached Windows Git.
