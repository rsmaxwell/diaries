# Step 11 — Repeated unattended-cycle and integration evidence — OPEN

Use `../../tools/verify-0039-step11-unattended.sh` from **Windows Cygwin** after the 11 November 2026 05:30 UTC cycle. The standalone script is entirely **read-only**: it does not start cleanup, create snapshots, delete anything, initiate replication, or rescan quota accounting.

Recommended command, from the Windows Diaries repository root:

```bash
bash 'change-control/in-progress/0039-DEF - reconcile orphaned Btrfs qgroups on backup/tools/verify-0039-step11-unattended.sh' 2026-11-10 2026-11-11
```

The script saves a timestamped local evidence log in this directory and fails unless **each requested day** has a journalled `result=complete` or `result=deferred_pending` on *both* hosts. It also checks enabled and active timers, last service exit, snapshot health, dry-run classification, identical installed executable hashes and current simplified agreed-parent consistency. Review journal trends and pending counts, not just a PASS marker. Exact hosts and current Git revisions belong in the report.

The unsuccessful 10 November 07:36 proposed verification (`/usr/local/bin/btrfs-native-push` absent) was a **wrong historical CLI path**, not a replication defect. Reuse the successful read-only simplified sender/receiver verification recorded under completed 0042-FEAT; do not run the obsolete legacy tool.
