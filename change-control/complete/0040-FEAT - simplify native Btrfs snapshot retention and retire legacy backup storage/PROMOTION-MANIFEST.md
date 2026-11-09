# 0040-FEAT — Production promotion manifest

**Final status (9 November 2026): Step 12 and Step 13 CLOSED; Step 14 operational audit and receiver reconciliation PASSED. Whole-feature closure is CONDITIONAL on explicit acceptance of retaining historical `/@data/backup` and two empty legacy directory containers, followed by a successful full feature-directory Git move/commit/push to `change-control/complete/`.** Until that promotion, 0040-FEAT is IN PROGRESS. Playbooks `e0da797`; latest confirmed Windows Diaries base `815eb25`. Historical statements below retain their contemporaneous dates and meanings.

## Original design extension (historical planning record)

23 October 2026: include retiring the unnecessary `mars` `/media/usb/@snapshots/root/<timestamp>` history and changing the shared manager to accept `@data`-only timestamp sets. Permanent Playbooks changes are anticipated for snapshot creation configuration, paired-set validation, retention tests and retirement controls. **No source promotion, timer change, deletion or deployment has occurred as a result of this documentation update.** The existing active `mars` legacy prune service requires separate compatibility and migration assessment.

## Step 12 simplified design revision — 5 November 2026

The operator approved a lower-complexity agreed-parent native replication model with next-scheduled-run interrupted-receive retry. See `reports/STEP12-3-SIMPLIFIED-DESIGN-DECISION-20261105.md` and `IMPLEMENTATION-STEPS.md`. The transactional journal, staged stream transform, ownership witness and multi-stage promotion proposals are **not** target production components. **No simplification deployment or test cleanup is claimed by this design-only revision**. Keep the installed native sender, receiver, and rollback evidence until the reviewed replacement and consolidated regression acceptance. Record actual Git revisions, hashes, enabled timers and Playbooks file removals at cutover.

## Simplified Step 12 development acceptance — 5 November 2026

**ACCEPTED:** 18 core source regression tests; three simplified and eleven existing agreed-parent protection tests; independent exit-75 local lock collision; and successful disposable real-Btrfs interrupted receive → exact cleanup → retry, plus lost-acknowledgement reconciliation without retransmission. Raw evidence and tested-file hashes are in `reports/STEP12-SIMPLIFIED-SOURCE-AND-REAL-BTRFS-ACCEPTANCE-20261105.md` and `evidence/Step 12/raw-logs/`. The source implementation is **not yet an immutable Playbooks commit**: observed Playbooks `HEAD=bdba058b...` had significant local changes; source script SHA-256 `9be64295a6b6807df0fcd33d924b7a6549959f2a03dcab2953dcf0ac77fa6297` is the tested identity.

**Still pending:** read-only installed-state/SSH/sudo inspection, reviewed Ansible `--check --diff`, state bootstrap/reconciliation decision, operational installation and cutover, real-host runtime/parent/lock verification, and separately approved receiver pruning. Existing 03:30 timer, native executable and established checkpoints remain unchanged by this record. See `tools/README-STEP12-SIMPLIFIED-OPERATIONAL-PREFLIGHT.md`.

## Track future promotions

| Revision | File path (Playbooks repository relative) | Reason | Target host(s) | Test evidence | Check/diff evidence | Deployment evidence | Rollback |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pending | Pending | Shared manager/source and receiver config | `mars`, `backup` | Pending | Pending | Pending | Pending |

Record: immutable Git revisions, reviewed diffs, program parity hashes, config differences, timer enablement, native sender/receiver health, positive/negative test results, no changes to unintended hosts, accepted deletions, capacity metrics and full close-out. Nothing under this feature tree is automatically deployed.

## Source/deployment reconciliation — 25 October 2026

The new shared manager implementation has been installed on `mars` and `backup`, and source/install SHA-256 was verified as `cb4785a3880f83201e7718f10fd8a053f4f0cce2b5a9f65f09c0374c5ebd132e`. The renamed entry point is `btrfs-replication.yaml`. Its two-host check-mode idempotency evidence is `mars changed=0 failed=0` and `backup changed=0 failed=0`. The production receiver remains protected; receiver-prune activation is not accepted. The original in-progress source modifications and deletions are in Playbooks working tree based on `a8f857c3b4f2ff57dd83d58bbbe0a99150797625`, **not yet an immutable committed promotion**. Record the final Playbooks Git revision and source diff at commit/release.

| Workstream | Changed files / surface | Accepted evidence | Remaining gate |
| --- | --- | --- | --- |
| Shared manager | `roles/snapshots/files/btrfs-snapshot-manager.py`, tests, native snapshot role | Source/install parity and host inventory verification | Final Git revision and feature completion |
| Snapper retirement | Removed active Snapper helpers, legacy units, retirement role tasks and entry playbook; cleaned relevant inventory | Source regressions, controlled host retirement and active-reference audit | Separate native `mars` root retirement; preserve rollback/evidence |
| Replication playbook rename | `native-btrfs.yaml` → `btrfs-replication.yaml`; role defaults/README/tasks and remote references | Syntax pass; `mars` and `backup` `--check --diff` both `changed=0` | Include in final source commit |
| Protection idempotency | `roles/btrfs-replication/tasks/native.yaml`, `tests/verify-replication-protection-idempotency.py` | Formatting-independent `mars` check; fixture cases missing/disabled/wrong path passed | Preserve regression in commit |
| Operational documentation | `roles/local-backup/README.md` | Removed obsolete legacy-pruning instructions | Final documentation audit |

The backup-only 115 original legacy Snapper snapshots, plus the APT-generated extra snapshot and empty legacy container subvolumes, were retired under their separately documented guarded approvals. This does not close overall Steps 10–11 or authorise deletion of received snapshots. Keep the raw evidence/approved manifest on `mango` until it has been archived as historical evidence; do not move evidence scripts into permanent operational roles.


## Step 12 final production promotion and rollback — 8 November 2026

**Accepted and CLOSED for Step 12; feature not yet closed.** Source versions: Playbooks `6553ace` (simplified sender/receiver retention) and `e5ae755` (read-only sender status, updated `diaries-backup-status`, legacy installer gates). Final archived Diaries evidence revision: `a719542`.

- `mars`: `/usr/local/bin/btrfs-simplified-replication sender cycle` invoked by retained `btrfs-native-push.service` and 03:30 UTC timer. `sudo -n /usr/local/bin/btrfs-simplified-replication sender status` and `sudo -n /usr/local/sbin/diaries-backup-status --json` verified. Obsolete sudoers removed through Ansible.
- `backup`: same simplified replication executable serves receiver operations; `btrfs-receiver-simple-prune.timer` enabled/active at 04:15 UTC with maximum 10 deletions/run; first unattended execution successful on 8 November with 0 eligible deletion candidates.
- Guarded retirement: `39` obsolete executable/module files on `mars`, `35` files/units on `backup`; removed with exact-file checksums and verified TAR archives, followed by independent operational verification and receipt-only finalisation. The obsolete `btrfs-legacy-prune.timer` is now unloaded. This did **not** remove any snapshots, agreed-parent state, holds or datasets.
- Rollback ownership: feature `evidence/Step 12/rollback/` contains original per-host files in `legacy-code-mars-20261108-085914Z.tar` and `legacy-code-backup-20261108-085914Z.tar`. SHA-256 `c7c900e99a8dd552a1966cd2ed5185dc38e57a41efd264e453fdd783cf26b638` (`mars`) and `7769d82d75a1c4f7bad2428a8df3d247070a8340403a7890c39d566eb892648c` (`backup`). Restoration, if required, needs separate explicit operator authorisation; restoring old files is not authorisation to invoke their old protocol.
- Completion receipt: `evidence/Step 12/rollback/legacy-code-retirement-20261108-085914Z.json`; original failure and independent successful checks are preserved under `evidence/Step 12/raw-logs/`.

See [`reports/STEP12-FINAL-ACCEPTANCE-AND-CLOSURE-20261108.md`](reports/STEP12-FINAL-ACCEPTANCE-AND-CLOSURE-20261108.md) for the full evidence index and explicit closure decision. Final feature-wide promotion/runbook reconciliation remains part of Step 13.


## Step 13 bounded source-prune promotion and rollback — 8–9 November 2026

**Step 13 CLOSED upon successful Windows Diaries Git promotion of this closure package; Step 14 remains OPEN.** Runtime source Playbooks **`6ccbf73`** (pushed, deployed), succeeding `e5ae755`, provides source `prune --max-delete N` with a 1–10 cap, default 10 for the scheduled service; source prune timer is independently activation-gated with explicit inactive/disabled enforcement until approved. The existing receiver `btrfs-receiver-simple-prune.timer` at 04:15 UTC and its independent limit were unchanged.

| Host | Component / setting | Accepted state and rollback |
|---|---|---|
| `mars` | `/usr/local/sbin/btrfs-snapshot-manager`; `btrfs-snapshot-prune.service` | `--config /etc/btrfs-snapshot-manager.json prune --max-delete 10`; preserve holds and parent protection. |
| `mars` | `/etc/ansible/host_vars/mars/local-backup.yaml` | `btrfs_snapshot_activation_enabled: true`, `btrfs_snapshot_prune_activation_enabled: true`, `btrfs_snapshot_prune_on_calendar: "*-*-* *:45:00"`; source creation remains hourly at `:00`. Config ownership: `mango` Ansible inventory, not Diaries or Playbooks Git checkout. |
| `mars` | `btrfs-snapshot-prune.timer` | Enabled/active; first ordinary `:45` prune successfully deleted 10 complete sets on 9 Nov 08:45–08:51 UTC. For emergency pause: `ssh mars 'sudo -n systemctl disable --now btrfs-snapshot-prune.timer'`; set inventory activation variable `false` and reapply the tagged snapshots role to make the pause persistent. |
| `mars` / `backup` | Simplified replication | Sender 03:30 UTC; receiver prune 04:15 UTC. Verified current agreed parent `20261109-030030Z`, prior `20261108-030011Z`; leave receiver state, receipts, checkpoints and both parents intact. |

**Evidence:** The 21 original raw `evidence/Step 13/` files were imported from `mango` into Windows, with ZIP verification and the final accepted journal checked on 9 November. Primary sources: `step13-capped-source-deployment-20261108.txt`; `step13-prune-schedule-45-deployment-20261109-075503.txt`; `step13-unattended-pruning-followup-20261109-080857.txt`; `step13-prune-0845-completion-20261109.txt`. Historical `:15` lock-contention failures and inventory/verification-script corrections remain retained, not erased. Reports: `reports/STEP13-SOURCE-PRUNE-CATCHUP-PLAN-20261108.md`, `reports/STEP13-BOUNDED-SOURCE-PRUNING-OPERATIONAL-ACCEPTANCE-20261109.md`, `reports/STEP13-SOURCE-PRUNING-RUNBOOK-20261109.md` and `reports/STEP13-FINAL-RECONCILIATION-20261109.md` and `reports/STEP13-FORMAL-CLOSURE-20261109.md`. The additional 22nd file `evidence/Step 13/step13-playbooks-housekeeping-20261109-092216.txt` preserves the source-cleanup commit/push transcript.

**Idempotency:** initial bounded manager deployment verified `changed=0, failed=0` on recheck; schedule-change Ansible preview showed precisely one intended timer change, live deployment `changed=1, failed=0`. No full-role idempotency run after the schedule change is separately claimed. The 8 November source activation was explicitly approved. Do not invoke unbounded manual prune to accelerate the backlog.

**Final Playbooks housekeeping revision:** Operator verification on `mango` at Playbooks `6ccbf73` confirmed that tracked `roles/btrfs-replication/tasks/native.yaml.pre-wrapper-tags` was unreferenced. The 9 November `git rm`/commit/push created **`e0da797`** and clean `main` (`origin/main` matched). Exactly one historical 281-line task backup was removed from Git; no production scripts, timers or retention state were changed by this commit. `6ccbf73` remains the exact deployed source-prune runtime revision. Final Windows Diaries evidence/documentation promotion is required before Step 13 closure is recorded as complete.

**Follow-on boundary:** At accepted `:45` run, `mars` had 146 complete source snapshot sets, zero incomplete, and 606 stale qgroups, with `qgroups_under_deletion=0`; stale-qgroup recurrence stays in 0039-DEF. No new restore or destructive cleanup is authorised by this manifest. Step 14 must assess whole-feature cleanup and independent closure before moving the directory.


## Step 14 final source/deployment and retention reconciliation — 9 November 2026

| Component | Accepted state | Evidence / qualification |
| --- | --- | --- |
| Playbooks | `main` commit `e0da797`, clean checkout; deployed source-manager change from `6ccbf73` | `step14-receiver-and-legacy-data-review-20261109-095639.txt`, `step14-receiver-manager-reconciliation-20261109-100229.txt` |
| Shared manager | Identical Playbooks/source/receiver SHA-256 `89602f0aac07900b367a82728e42339ee9c9d3ed40e55010af87576dadc7a2b7` | Receiver Ansible deploy `changed=1 failed=0`, receiver repeat `--check --diff` `changed=0 failed=0` |
| Simplified sender/receiver | Identical executable hashes `7eba4a04aca1f9b04333cd82952744ab1559cc7736092d7d1dcc11a25be67363`; agreed parent `20261109-030030Z`, prior `20261108-030011Z`, status `relation=equal` | `step14-final-readonly-audit-20261109-094544.txt`, `step14-receiver-final-verification-20261109-103348.txt` |
| Source snapshots | No native `mars` root snapshot subvolumes; hourly `@data` creation; `:45` source prune with 10-set cap; 09:45 prune success | `step14-final-discrepancy-investigation-20261109-094938.txt` |
| Received snapshots | `backup` 32 retained, 0 candidates, 27 historical receipts preserved, 0 orphaned; receiver timer active/enabled | `step14-receiver-manager-reconciliation-20261109-100229.txt` |
| Recovery/rollback | Step 11 root-retirement receipts, Step 12 TAR rollback records, Step 13 source prune pause/runbook preserved | Prior accepted feature evidence, no new destructive test |
| Legacy backup | `/@data/backup` **still contains historical backup data; NOT removed** | Protected by `roles/remote-backup/README.md` and existing 0035 verification; material exception to originally listed retirement scope requires explicit approval |
| Empty containers | `/@snapshots/@data`, `/@snapshots/root` are empty ordinary directories, not Btrfs subvolumes | No deletion required for data safety; retention exception to literal directory absence |
| Capacity and warning | `mars` 3.4 TB available, `backup` 856 GB available at audit; `mars` 606 stale qgroups | 0039-DEF owns stale-qgroup recurrence; 0041-FEAT owns sender/receiver user hardening |

**Feature status gate:** A Step 14 closure report is prepared, not automatically effective. Accept the stated historical-data and empty-directory exceptions explicitly, then perform the whole feature-directory move to `change-control/complete/` using the authoritative Windows checkout, stage exact feature scope, review/commit/push. Any failure leaves 0040-FEAT OPEN. Keep historical evidence and decisions; do not delete `/@data/backup` or either parent/hold.
