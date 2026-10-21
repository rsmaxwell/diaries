# 0037-FEAT — Step 12 stale Btrfs qgroup cleanup: formal reconciliation

**Decision: CLOSED — PASSED (cleanup and protection preservation), 2026-10-20.**

Step 12 is supplemental maintenance added after the approved Step 11 pilot. It is distinct from original implementation-plan Step 12 (“Scheduler acceptance and rollback”), which **has not** been completed or renumbered. Automatic legacy pruning remains unapproved.

## Before and after: `mars` /media/usb

| Metric | Before | After |
| --- | ---: | ---: |
| Total quota groups | 16,129 | 145 |
| Stale level-0 quota groups | 15,984 | 0 |
| Under deletion | 0 | 0 |
| Native complete snapshot sets | 58 | 58 |
| Native incomplete snapshot sets | 0 | 0 |
| Native dry-run deletion candidates | 0 | 0 |
| Checkpoint holds | 2 | 2 |
| Replication-protected checkpoint | `20261020-030026Z` | unchanged |
| Btrfs device error counters | 0 | 0 |

The before-count derives from operator's read-only Step 12 preflight transcript (`rows_total=16129 stale=15984 under_deletion=0 non_stale=145`). The execution transcript records `btrfs qgroup clear-stale /media/usb` output for the stale entries and the post-state `total=145 stale=0 under_deletion=0`. Quota rescan reports none in progress. Manager status reports `complete_timestamp_sets=58;incomplete_timestamp_sets=0`, two unchanged held checkpoints, the replication pin and valid Diaries production verification (`backupId=20261020-003106Z`). Device error counters all zero.

## Source evidence

- `execution/operator-preflight.txt`: no concurrent matching jobs, no quota rescan and five zero device-error counters.
- `execution/operator-cleanup-and-verification.txt`: cleanup output and final independent validation. The supplied cleanup transcript contains 9,999 displayed `Delete stale qgroup` lines (not the full 15,984); the independently reported final state, not the transcript line count, establishes `stale=0`. Preserve the supplied transcript without representing it as a complete per-ID record.
- `execution/SHA256SUMS.txt`: checksums of the two preserved source transcripts.
- `qgroup-preflight/`: original separately captured detailed baseline retained locally by the operator; not bundled here because it was not supplied as an attachment.

## Read-only performance regression — separately recorded outcome

Prior to cleanup, the original `snapper ... list` was observed to time out, while `list --disable-used-space` succeeded. The bounded test in `tools/step12-snapper-performance-from-cygwin.sh` captures both commands and exit codes without deleting anything. **At the time of this document, the post-cleanup performance result has not been supplied; do not claim the latency problem was cured.** Place the test transcript in `performance/snapper-performance.txt`, review its exit codes and annotate this report with the measured finding.

The performance measurement is diagnostic, *not* a criterion for declaring the 15,984 stale metadata records removed. If it still times out, keep the existing `--disable-used-space` code fix and open a separate follow-up performance investigation.

## Exclusions and boundaries

No snapshot subvolumes were intentionally deleted during qgroup cleanup; no quotas were disabled; no quota rescan was initiated; no additional legacy deletion or schedule change was authorised. Do not conflate this supplemental maintenance closure with the original feature-plan scheduler-acceptance step or overall feature closure. Receiver health was not re-tested during qgroup cleanup beyond the unchanged local replication pin.
