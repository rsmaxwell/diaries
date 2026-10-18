# 0036-FEAT Step 8 Gate E — controlled retirement (2026-10-18)

**Status: IN PROGRESS — implementation of read-only inventory only. NOT CLOSED.**

## Inherited acceptance

Gate A–D are CLOSED. Gate D accepted scheduled unattended production cycles on 2026-10-17 and 2026-10-18, including verified schema-2 capture/receive, snapshot eligibility, read-only history and off-site incremental receipts. Reuse their evidence; do not rerun a full restore solely for retirement.

## Gate E ordered controls

1. **Read-only inventory.** Collect the deployed fixed/rollback publication paths, scripts, active units, current backup markers, snapshot/replication locations, and source/deployed Git revisions across the three hosts. Run `verification/0036-gate-e/collect-gate-e-readonly.sh` on mango; review all non-zero exit statuses, especially `backup` SSH and files needing sudo.
2. **Dependency and name reconciliation.** Audit every deployed `0036` path, NAS mount switch, config variable, script and template before renaming. Distinguish historical test/change-control identifiers from actual runtime identifiers. Preserve the fixed-path capture/pull contract and idempotent Ansible convergence; do not unilaterally rename source on one host. Stable-name migration must be staged with a reversible source+deployment plan and compatibility checks. **No such migration has yet occurred.**
3. **Legacy publisher execution retirement.** Prove old generation publisher is not a timer, service, Cron job or runnable active path; preserve 0034 historical restore tooling and rollback aliases. Legacy execution retirement is distinct from data deletion.
4. **Rollback-window decision.** Obtain explicit operator approval to end legacy rollback availability, after confirming the accepted on-site/off-site checkpoint and current receipt still exist. If withheld, leave old symlinks/generations intact and Gate E open.
5. **Separately approved destructive removal.** Identify exactly which generation directories and symlinks would be removed, with canonical paths, file types, Btrfs subvolume status and size. Seek an additional explicit approval **for deletion**. No `rm -rf`, recursive deletion, snapshot pruning or removal of old Snapper history in this package.
6. **Post-deployment verification and close-out.** After an authorised stable-name migration and execution retirement, confirm all five timers, one capture→receive→snapshot→offsite receipt, and restored historical discovery compatibility, record deployed Diaries and Playbooks Git SHAs, rollback/retention decisions, and operator approval. Only then mark Gate E, Step 8 and 0036-FEAT CLOSED.

## Current safety disposition

- **No Docker build required** for this read-only documentation/Playbooks verification increment.
- Keep scheduled capture, pull, snapshot, prune and push services enabled and unchanged.
- Preserve `pluto` and `mars` `.pre-0036-rollback` aliases and their generations.
- Preserve historical 0034/0035 Btrfs history, replication ancestry, receipts, checkpoint holds and legacy Snapper snapshots.
- Do not interpret Gate D success as consent to delete any backup content.
