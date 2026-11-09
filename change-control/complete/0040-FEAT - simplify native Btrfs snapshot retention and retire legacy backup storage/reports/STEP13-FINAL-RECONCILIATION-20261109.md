# 0040-FEAT — Step 13 final evidence and repository reconciliation

**Reconciled:** 9 November 2026. **Decision:** Step 13 operational acceptance **PASS** and final Playbooks housekeeping **PASS**. **Formal Step 13 closure is approved and becomes recorded upon successful Windows Diaries Git promotion of the closure package.** That commit/push is not claimed until its actual terminal result is checked. Step 14 remains OPEN.

## Accepted evidence

- Playbooks `main` `6ccbf73` pushed and deployed; bounded source prune options validated, timer inactive/disabled while not approved, role/regression tests PASS and first deployment recheck idempotent.
- Operator explicitly approved capped hourly source pruning. The originally paused timer was enabled on `mars` via `/etc/ansible/host_vars/mars/local-backup.yaml`. Early inventory and vault-account failures are recorded as diagnostic history; neither activated deletion.
- First live, activation-triggered run 8 November 14:43:17–14:43:24 deleted exactly 10 complete sets and finished successfully. Follow-up old `:15` attempts sometimes failed on legitimate shared-lock contention, including a verified overlap of the 15:00:11–15:17:22 snapshot-creation service.
- The approved schedule adjustment to `:45` was previewed as exactly one Ansible timer unit change and deployed without failure. First normal 9 November 08:45:39–08:51:53 execution completed exit 0 with `PRUNE-CAP: eligible=87 selected=10 max_delete=10`, 10 actual deletions, **146 complete and managed**, **0 incomplete**. Checkpoint holds were reported protected; parent and prior were already verified after the prior overnight replication to be equal on sender and receiver.
- As of the 9 November accepted `:45` status: 606 stale source Btrfs qgroups, no qgroups under deletion, warning active; **0039-DEF remains responsible**. Do not treat Step 13 as a qgroup recurrence fix or as reason for an additional destructive cleanup.

## Authoritative Windows reconciliation (observed, not yet promoted)

- Cygwin log dated **9 November 09:08** confirms ZIP integrity and extraction of **21 files** into `change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/evidence/Step 13/` under the Windows Diaries repo. It verified the 08:45 final journal `Deleted 10 complete timestamp sets` line. This is independent of merely having created the ZIP.
- Pre-import Windows Git was `main`, commit `4f166ac` (Step 12 closure). Two Step 13 reports were present **untracked**, not committed. The subsequent `git status` and Git commit/push **are not yet evidenced**.
- Preserve the entire 21-file Step 13 evidence set, including original errors, previews, raw journals and corrected runs. The detailed event chronology and primary log names are in `reports/STEP13-BOUNDED-SOURCE-PRUNING-OPERATIONAL-ACCEPTANCE-20261109.md`. The contemporaneous prepared-only catch-up plan is historical and should not be rewritten as if deployment had already occurred.

## Source and operational ownership

- Playbooks implementation: commit **`6ccbf73`** after `e5ae755`; `roles/snapshots/` manager, source defaults, task, service template, tests and README. Shared receiver/sender simplified replication remains owned by Playbooks; receiver-pruning acceptance and legacy runtime retirement were closed under Step 12.
- Permanent per-host variables live in `/etc/ansible/host_vars/mars/local-backup.yaml` on `mango`: `btrfs_snapshot_activation_enabled=true`, `btrfs_snapshot_prune_activation_enabled=true`, `btrfs_snapshot_prune_on_calendar="*-*-* *:45:00"`; no host override is needed for the role default max-delete 10. `roles/snapshots/README.md` and `reports/STEP13-SOURCE-PRUNING-RUNBOOK-20261109.md` describe the operation and rollback.
- The existing 0040 Step 12 TAR/receipt rollback archives remain untouched. Step 13 rollback is primarily **disable source prune timer** immediately, then persist the pause in the inventory and reapply the tagged snapshots role. No current evidence supports resetting the agreed-parent state, deleting historical checkpoints or restoring retired legacy code as part of this step.

## Housekeeping completed — 9 November 2026

The operator checked current `mango` Playbooks `main` at `6ccbf73`, with a clean working tree. `git ls-files` confirmed `roles/btrfs-replication/tasks/native.yaml.pre-wrapper-tags` tracked; `git grep` found no references. The operator ran guarded `git rm` and committed/pushed **`e0da797`** (`0040-FEAT: Remove obsolete replication task backup`). The final log shows clean Playbooks status and `HEAD -> main, origin/main` at `e0da797`. Exactly one 281-line backup file was removed; no changes to the deployed pruning runtime were required. Raw operator transcript: `evidence/Step 13/step13-playbooks-housekeeping-20261109-092216.txt`.

## Final closure and promotion checklist

- [x] Capped source manager deployed, accepted and tested (`6ccbf73`); user explicitly approved scheduled pruning.
- [x] Accepted normal `:45` operation, 10 deletions, service exit 0, zero incomplete sets and verified replication state.
- [x] Windows evidence import independently verified: 21 original raw files, accepted journal line checked.
- [x] Historic Playbooks backup investigated, removed, committed and pushed (`e0da797`); clean Git status.
- [x] Step 13 documentation/runbook/promotion and formal closure record prepared for repository-relative ZIP promotion.
- [ ] **Last required closure gate:** In the authoritative Windows Diaries checkout, inspect the applied ZIP against local changes, verify all **22** raw Step 13 files and intended reports, `git diff --check`, stage only this feature, commit, push, verify clean state, and record actual commit identifier in operator terminal/evidence. Do not call this last gate PASS before execution.

**Closure disposition:** Step 13 is ready for formal CLOSED status by accepting and committing the attached docs and evidence in the Windows Diaries repository. Step 14 remains OPEN; it owns the whole-feature acceptance, final legacy-data inventory, rollback and documentation review, and eventual directory move to `change-control/complete/`. Existing accepted Btrfs correctness and restore evidence may be reused. 0039-DEF remains open for qgroup recurrence (606 stale at accepted 08:45 run); 0041-FEAT retains account-hardening scope.
