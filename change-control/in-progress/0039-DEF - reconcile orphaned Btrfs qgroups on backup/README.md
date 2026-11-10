# 0039-DEF — Reconcile and manage recurring stale Btrfs qgroups on mars and backup

**Opened:** 21 October 2026. **Scope confirmed:** 9 November 2026. **Evidence reconciled:** 10 November 2026.
**Status:** **IN PROGRESS**. Steps **1–10 CLOSED** (Steps 1–7 on accepted October evidence, Steps 8–10 on the 9–10 November observations); Steps **11–12 OPEN**. No formal defect closure or feature-directory move has occurred.

## Accepted historical remediation (Steps 1–7)

The original off-site receiver had a parser incompatibility and 29,437 unmatched level-0 qgroups. The approved October cleanup removed these entries, preserved the failed-batch journal and its separately verified reconciliation, and a subsequent incremental receive passed. This is a historic point-in-time acceptance, not evidence of recurrence prevention. See existing `evidence/Step 01/` to `Step 03/`, `evidence/STEPS04-07-EVIDENCE-RECONCILIATION.md` and the original journals (including the interrupted **FAIL** batch).

## Accepted recurrence work (Steps 8–10)

- **Step 8 — CLOSED, 10 November:** On 9 November, the read-only host baselines showed 656 native `<stale>` qgroups on `mars`, zero on `backup`; both had kernel 6.8.0-147, btrfs-progs v6.6.3 and native `qgroup clear-stale`. Subsequent investigation correlated *all* 11 remaining non-zero stale qgroup IDs with the 11 pending Btrfs subvolume deletions. Background deletion completion reduced the pending IDs further. This establishes a strong operational explanation for the busy errors, not proof of an upstream Btrfs kernel defect.
- **Step 9 — CLOSED, 10 November:** A single maintained cleaner with per-host JSON configuration, ordered locks, fail-closed validation, dry-run default and recognised `deferred_pending` outcomes was installed through `btrfs-replication.yaml` on both hosts. **22 tests passed**. At 22:58 UTC on 9 November, the controlled `mars` run removed 95 eligible stale qgroups, left eight matching pending deletions, and exited successfully with an explicit deferral. The subsequent dry run showed zero eligible entries. No new snapshots were deleted by the cleaner.
- **Step 10 — CLOSED, 10 November:** Both 05:30 UTC timers are enabled and active. The first unattended run on 10 November at 05:30 removed 14 stale entries on `mars`, leaving zero immediately after the run, while `backup` completed with zero stale. Both services returned status 0. A later read-only inspection found two newly eligible entries on `mars`, consistent with normal activity between scheduled runs; zero was **not** required at arbitrary later times. Snapshot managers reported no incomplete sets and verified source production backup status.

See `reports/STEP08-10-ACCEPTANCE-RECONCILIATION-20261110.md`. Original uploaded terminal transcripts from the 9–10 November investigation are preserved under `evidence/Step 09/raw-terminal/` and `evidence/Step 10/raw-terminal/`. The Windows-collected Step 8 and Step 10 records remain authoritative where present; this package does not replace them.

## Remaining work

**Step 11 — OPEN:** Observe at least one *further* 05:30 cycle under ordinary snapshot/replication activity and confirm a bounded or understood deferred backlog, snapshot integrity, scheduled service status and identical agreed-parent records. Use the read-only `tools/verify-0039-step11-unattended.sh` collector after the 11 November run, alongside the already accepted 0042-FEAT source retirement/replication acceptance. This is not a repeat of the large October cleanup, a restore or a receiver reseed.

**Step 12 — OPEN:** Reconcile the 0039 Playbooks and Diaries source commits separately from closed 0042-FEAT, record accepted Step 11 evidence, formally close the defect and move the entire feature directory to `change-control/complete/`. The historical `evidence/STEP08-FINAL-CLOSEOUT.md` remains a superseded *proposal*, not a completed closure receipt. The 0042 feature is already CLOSED and need not be reopened.

## Operational safety

The installed cleaner changes qgroup metadata **only when its managed systemd service runs**; ordinary CLI invocation remains read-only. It validates filesystem and lock contracts and does not delete snapshots, alter agreed-parent state, invoke quota rescans or initiate replication. Native Btrfs may return a nonzero code for entries still pending deletion; those may be reported as `deferred_pending` only after exact-ID verification. Unexpected failures remain failures. Keep the managed 05:30 schedule and current 0040 simplified sender/receiver state unchanged. Ubuntu upgrades and new snapshot deletion policies remain out of scope.
