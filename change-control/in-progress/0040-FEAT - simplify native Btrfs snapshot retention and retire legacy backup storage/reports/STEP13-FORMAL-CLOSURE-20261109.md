# 0040-FEAT — Step 13 formal closure and source-promotion acceptance

**Prepared and accepted for promotion:** 9 November 2026. **Step decision:** **CLOSED on successful Git promotion of this exact final package and its evidence.** Until the user confirms that final Windows commit/push, the closure record is a prepared declaration and must not be represented as an already committed result. **0040-FEAT remains IN PROGRESS; Step 14 OPEN.**

## Scope and source revisions

Step 13 cleaned final source configuration, operational runbooks and evidence without changing the Step 12 agreed-parent architecture or receiver snapshots. Source-pruning runtime was implemented in Playbooks **`6ccbf73`**, with `prune --max-delete 10`, explicit pruning activation, and an independent scheduler. The deployed host inventory `/etc/ansible/host_vars/mars/local-backup.yaml` permits pruning and schedules **hourly at `:45`**, separate from hourly creation at `:00`. The original timer `:15` failures are retained as evidence rather than hidden.

The remaining tracked historical Playbooks file `roles/btrfs-replication/tasks/native.yaml.pre-wrapper-tags` was checked against current `main` at `6ccbf73` (tracked, no source references, clean tree). The operator removed it via `git rm`, committed **`e0da797`** and pushed; `origin/main` and local `main` matched, with clean final status. This is a source-only cleanup; the **deployed** pruning runtime remains `6ccbf73` and does not need redeployment merely to remove this unreferenced backup.

## Evidence accepted

1. The first activation-triggered live prune on 8 November at **14:43:17–14:43:24 UTC** passed, deleting 10 complete sets under the configured cap. The old `:15` schedule conflicted with snapshot creation (15:00:11–15:17:22 UTC), causing lock-protected non-destructive failed attempts. These are explained in `step13-creation-prune-lock-correlation-20261108.txt` and diagnostic logs.
2. Following the user-approved shift to `:45`, the **first normal scheduled** 9 November run began **08:45:39 UTC**, ended **08:51:53 UTC**, `Result=success`, `ExecMainStatus=0`; `PRUNE-CAP: eligible=87 selected=10 max_delete=10`, `Deleted 10 complete timestamp sets`, snapshot state **146 complete / 146 managed / 0 incomplete**. Evidence: `evidence/Step 13/step13-prune-0845-completion-20261109.txt`.
3. Checkpoint holds `20261013-171228Z` and `20261018-165453Z` and replication protection were reported during the accepted run. The 9 November sender/receiver status check showed equal agreed-parent `20261109-030030Z` and prior `20261108-030011Z` after unattended replication. Evidence: `step13-unattended-pruning-followup-20261109-080857.txt`, `step13-prune-0845-completion-20261109.txt`.
4. **21 original raw evidence files** were transferred from `mango` into the authoritative Windows Diaries repo, archive-integrity checked, extracted and explicitly verified on 9 November at 09:08; the accepted 10-delete journal line was read back. The **22nd raw file** `evidence/Step 13/step13-playbooks-housekeeping-20261109-092216.txt` records the final Playbooks cleanup.
5. Operator runbook and rollback are in `reports/STEP13-SOURCE-PRUNING-RUNBOOK-20261109.md`; source changes and provenance in `PROMOTION-MANIFEST.md`; incident/acceptance chronology in `reports/STEP13-BOUNDED-SOURCE-PRUNING-OPERATIONAL-ACCEPTANCE-20261109.md` and `reports/STEP13-FINAL-RECONCILIATION-20261109.md`. This closure package preserves original failed-run evidence.

## Operations and exclusions

The existing protections, Btrfs writer coordination, receipts, sender/receiver agreed-parent state and checkpoint holds remain intact. Emergency stop: from `mango`, `ssh mars 'sudo -n systemctl disable --now btrfs-snapshot-prune.timer'`; persistent pause requires `btrfs_snapshot_prune_activation_enabled: false` in `/etc/ansible/host_vars/mars/local-backup.yaml` and reapplying the tagged snapshots role. Never unpin a parent, remove holds, or run uncapped pruning merely to accelerate catch-up.

At the 08:45 acceptance, `mars` reported **606 stale qgroups** (`qgroups_under_deletion=0`, warning); recurring stale-qgroup handling belongs to **0039-DEF**, without new destructive maintenance approval here. **0041-FEAT** owns later dedicated sender/receiver accounts and SSH privilege tightening. No additional full restore/replication E2E test is required for Step 13 because previously accepted correctness evidence remains sufficient.

## Final publication gate

The closure is effective when the operator confirms the correct, conflict-free ZIP has been applied in the **Windows Diaries repo** on its intended `main` branch, all 22 Step 13 evidence files plus reports are preserved, the feature-scoped Git diff is reviewed and passes whitespace checks, and the documentation/evidence commit has been pushed with a clean working tree. The resulting Diaries Git commit must be captured from the terminal output; **it is not known at preparation time**. If that promotion fails, leave Step 13 administratively OPEN pending correction.

**Step 14 remains OPEN.** Do not move this feature directory into `change-control/complete/` until the independently accepted whole-feature closure decision.
