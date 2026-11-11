# 0039-DEF — Steps 8–10 acceptance reconciliation

**Date:** 10 November 2026. **Disposition:** Steps 8, 9 and 10 CLOSED on the documented operator-run terminal evidence. **Remaining:** Step 11 repeated unattended-cycle acceptance; Step 12 Git/source reconciliation and formal defect closure. This report is an evidence synthesis, not a claim that commands ran within ChatGPT.

## Source and host baselines (Step 8)

The operator's 9 November Windows Cygwin read-only baselines (`evidence/Step 08/mars-baseline-20261109-135149Z.txt`, `backup-baseline-20261109-135152Z.txt`) passed. Both machines reported Linux kernel **6.8.0-147**, btrfs-progs **v6.6.3**, and native `btrfs qgroup clear-stale` support. `mars`: **656** stale qgroups, zero unmarked orphans, live snapshot inventory healthy; `backup`: **0** stale, 35 qgroups, 34 live subvolumes. This supersedes the old source-bundle-only status, but does not erase that historical review.

## Causal investigation and corrected implementation (Step 9)

1. First controlled `mars` cleanup failed with `Device or resource busy` after making **partial progress**: 656 stale before, **62** afterward; **594** removed. In contrast `backup` completed zero-stale cleanup successfully. The earlier failure remains preserved as FAIL.
2. The **62** remaining entries were initially all nonzero in the accounting fields. `btrfs qgroup show -p -c` showed no parent/child relationships. The quota rescan completed, but nonzero stale entries persisted; no uncontrolled quota reset or second rescan followed.
3. Btrfs had **43** deleted subvolumes pending physical cleanup; a 20-minute `btrfs subvolume sync` timed out (exit **124**) but reduced pending deletions to 38. Later exact-ID correlation showed **11** pending deleted subvolumes matched **all 11** nonzero stale qgroups, with `nonzero_not_pending=[]` and `pending_not_nonzero=[]`. The normal asynchronous deletion lifecycle is a **strong evidence-backed explanation**, not a proven universal kernel root cause. During these observations ordinary prune cycles changed retained snapshot counts; no incomplete timestamp sets were reported and the source backup marker remained valid.
4. The common cleaner was updated to classify native busy failures as an *expected deferral only for exactly matching pending deleted subvolume IDs*. The error path remains nonzero for unexpected conditions. **22/22 regression tests passed**, including actual host-output parsing, lock/security tests and the 91 eligible/11 pending replay.
5. Ansible deployed the same cleaner to both hosts with host-specific `/etc/btrfs-stale-qgroups.json`, including distinct filesystem and writer-lock paths, and shared templates. On 9 November 22:58 UTC, `mars` completed a controlled live run: `stale_before=103`, `removed=95`, `stale_after=8`, `deferred_pending=8`, `result=deferred_pending`, `ExecMainStatus=0`. The following dry run showed `stale_eligible=0`. Snapshot sets remained **69 complete/0 incomplete** and the Diaries production backup verification remained valid.

## Deployment and first unattended execution (Step 10)

- Both timers were explicitly enabled through Playbooks after the controlled run and reported **enabled/active** for the 10 November 05:30 UTC cycle.
- 10 November **05:30:21 UTC**, `mars`: `stale_before=14`, `removed=14`, `stale_after=0`, `result=complete`, `ExecMainStatus=0`.
- 10 November **05:30:00 UTC**, `backup`: `stale_before=0`, `stale_after=0`, `result=complete`, `ExecMainStatus=0`.
- At **07:29 UTC**, the read-only `mars` dry run found two new eligible stale qgroups; the snapshot manager reported **70 complete/0 incomplete**, `qgroups_status=ok` and a valid production backup marker for `20261110-003113Z`. `backup` reported **33 complete/0 incomplete**, zero stale and healthy status.
- In the independently accepted **0042-FEAT** source-retirement verification, simplified sender and receiver both reported an **equal, verified** parent `20261110-030004Z`, the active service used `/usr/local/bin/btrfs-simplified-replication sender cycle`, and backup/replication/retention timers were healthy. That evidence is retained under completed 0042 and **reused**, not re-executed, for 0039 Step 11's integrity baseline.

## Failure and evidence integrity

Preserve the initial 9 November failed native `clear-stale` invocation, the 20-minute pending-deletion sync timeout, the controlled quota rescan, and the 10 November 07:36 Step 11 wrong-CLI failure. These are not retroactively marked successful. The later corrected verification establishes the intended shared cleaner and the live simplified sender/receiver state. The old 22 October interrupted 675-deletion journal remains **FAIL** with its separate acknowledged reconciliation.

Primary local evidence: `evidence/Step 08/` (operator-collected raw host baselines); `evidence/Step 09/raw-terminal/` (verbatim uploaded investigation, source/deploy and controlled-run logs); `evidence/Step 10/scheduled-maintenance-20261110.txt` plus `raw-terminal/` (first 05:30 run). The completed 0042 change-control directory carries the Git retirement/deployment/rollback archive and parent verification. No duplication of 0042 archival evidence here.

## Outstanding Step 11 / Step 12 acceptance

One first unattended cycle is not sufficient to prove bounded recurrence. Capture at least one further **05:30 UTC** maintenance cycle on both endpoints (11 November or later), verify service/journal classification, per-host snapshot counts, timer state, executable identity, no unexpected orphan/under-deletion state and current simplified agreed-parent equality. The read-only collector is `tools/verify-0039-step11-unattended.sh`. Consider new entries between runs normal only if subsequent scheduled service processes them or they correspond to confirmed pending deletions. Do not assert that the filesystem will never produce stale qgroups.

Next, record **0039-only** Playbooks and Windows Diaries Git commits and installed runtime identity, keep 0042-FEAT CLOSED, and formally move the entire 0039 directory to `change-control/complete/` **only after** Step 11 and operator acceptance. Neither the accepted 22 October bulk cleanup nor a full restore, receiver reseed, OS upgrade, new snapshot deletion policy or forced quota reset belongs in this closeout.
