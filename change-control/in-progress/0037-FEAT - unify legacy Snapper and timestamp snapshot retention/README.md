# Evidence index

Create one `Step NN/` subdirectory per implementation step. Keep live captures and approval records here, not in Playbooks production directories. Implementation evidence is recorded under `evidence/Step NN/`; see the step-specific closure records.

## Supplemental Step 12 — stale Btrfs qgroup maintenance (2026-10-20)

**CLOSED — PASSED** for qgroup cleanup and native snapshot protection reconciliation: stale records 15,984 → 0, total quota records 16,129 → 145. See `evidence/Step 12/STEP12-RECONCILIATION-AND-CLOSURE.md`. Read-only Snapper performance measurement remains unreported and will be stored under `evidence/Step 12/performance/`. **Original implementation-plan Step 12 (scheduler acceptance and rollback) is now CLOSED in its own formal record** and is not superseded by the supplementary maintenance step.

## Step 12 unattended retention implementation staging (2026-10-20)

Operator requested unattended aging-out of both native timestamp sets and legacy Snapper snapshots. The native 08:15 UTC timer already prunes timestamp sets. Playbooks source changes stage a bounded, opt-in legacy-prune command (one legacy snapshot per run by default) under the same existing oneshot service; defaults off and not yet activated. See `evidence/Step 12/STEP12-UNATTENDED-PRUNING-STAGING.md`. Original Step 12 remains OPEN until runtime activation, verification and rollback acceptance.

## Original Step 12 — scheduler acceptance / rollback — FORMALLY CLOSED (2026-10-20)

**CLOSED — PASSED.** Permanent `local-backup.yaml` deployment, repeat-run idempotency, host inventory opt-in, daily legacy timer enablement, hourly native timer preservation, two guarded systemd deletions (IDs `19629` and `19677`) and post-state verification accepted. See `evidence/Step 12/STEP12-SCHEDULER-FORMAL-CLOSURE.md` and `scheduler-acceptance/` for preserved operator logs. The pre-activation text above is historical staging evidence, not current state. Step 13 remains next; the overall feature is **not yet closed**.

## Step 13 — production documentation and housekeeping (2026-10-20)

**IN PROGRESS.** Permanent Playbooks promotion paths/hashes and the host-side cleanup checklist are recorded in `PROMOTION-MANIFEST.md` and `evidence/Step 13/STEP13-PRODUCTION-DOCS-AND-HOUSEKEEPING.md`. No host cleanup, full untagged deployment or final feature closure is claimed. Historical Step 12 staging text above is superseded by its formal closure.

## Step 13 — FORMALLY CLOSED (2026-10-20)

**CLOSED — PASSED WITH RECORDED DEFERRED HOUSEKEEPING.** Full production Playbooks reconciliation and repeat-run idempotency accepted. Residual root-owned legacy helpers retained and explicitly deferred; feature remains OPEN until Step 14. See `evidence/Step 13/STEP13-FORMAL-CLOSURE.md`. The earlier IN PROGRESS status above is superseded.

## Step 14 — final reconciliation (IN PROGRESS, 2026-10-20)

The post-cleanup production deployment is idempotent and Step 13 remains CLOSED. Final Git revisions, source/evidence inventory and controlled relocation to `change-control/complete/` are pending. See `evidence/Step 14/`.
