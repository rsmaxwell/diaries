# 0040-FEAT — Step 06 evidence: read-only runtime plans

**Decision: CLOSED — 25 October 2026 (accelerated acceptance).**

## Recorded operator evidence

- `note(20261024-220341).txt`: production baseline on `mars` (62 complete paired sets, 0 incomplete, 1 complete paired deletion candidate `20261022-220038Z`), `backup` (20 VERIFIED receiver snapshots, 0 inventory problems, 0 deletion candidates, plan `executable=false`, recovery `CLEAN`, `receiver_prune_enabled=false`). This is a prior-day baseline, not a same-time comparison.
- `note(20261025-072450).txt`: proposed `@data`-only configuration evaluated using a temporary JSON file, without changing installed settings. 63 sets retained, 0 deletion candidates; source Btrfs UUID of `20261024-030038Z` `22e0ca45-0f49-c745-85b0-af6b6cfb915c` equals the receiver snapshot's **Received UUID**. This establishes a valid historical incremental-parent relationship, not which parent the live sender will select next.
- `note(20261025-072649).txt`: same-run dry-run comparison on `mars` of installed paired configuration and temporary proposed `@data`-only configuration. Both report `RETENTION sets: total=63 keep=63 sources=2`, `Would delete 0 complete timestamp sets`; identical holds `20261013-171228Z`, `20261018-165453Z` and replication protection `20261023-030037Z`, `20261025-030026Z`.

## Configuration and remaining boundaries

- Live `mars` remains configured with `required_snapshot_sources=[root,@data]` and `creation_source_names=[root,@data]`. Proposed configuration was used only with `--config` and `prune --dry-run`.
- `backup` remains in `mode=receiver`, `receiver_prune_enabled=false`; receiver plan was not executable, and no receiver deletions were approved.
- Proposed source plan continues to inventory two configured sources while requiring only `@data` for *completeness*. Mixed-history behaviour is established by the Step 05 fixture, **not** this production comparison.
- `mars` qgroup status reported 218 stale qgroups, 0 under deletion. Track separately; do not interpret as acceptance of qgroup remediation.
- Retention plan outputs are time-sensitive. The prior-day one-set deletion plan and next-day zero-candidate plan are not comparable evidence of a policy effect; same-run comparisons are authoritative.
- Full cross-host destructive rehearsal was waived under the accelerated-path decision. No production deletion, retention change, root-creation cutover or receiver-pruning activation is authorised by this step.

## Gate result

The operator elected to proceed following review of the identical same-run plans and accepted historical UUID relationship. **Step 06 CLOSED for the read-only plan-review gate**, with zero deletions and the above residual limitations recorded. Step 07 requires Ansible `--check --diff`, rollback preparation and explicit approval of the exact diff before deployment. Step 10/11 still require identity-specific deletion approval.
