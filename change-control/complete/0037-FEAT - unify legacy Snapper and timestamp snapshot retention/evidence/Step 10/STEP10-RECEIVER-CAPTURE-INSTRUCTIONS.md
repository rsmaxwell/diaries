# Step 10 — Independent backup receiver preflight

**Status: evidence collection only; no deletion approved.**

## Execute from Windows Cygwin

From the Diaries repository root:

```bash
bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tools/step10-capture-backup-from-cygwin.sh"
```

The script uses the already configured SSH alias `backup` (override with `STEP10_BACKUP_SSH`), runs only read-only commands on `backup`, and writes its output under `evidence/Step 10/receiver-preflight/` on Windows. No WinSCP transfers, remote temporary scripts, or host modifications are needed. It expects non-interactive sudo, as in earlier feature captures.

It records the Btrfs mount, actual `/@data/mars-received/@data` repository, list of received subvolumes, latest received subvolume's UUID/received UUID and read-only flag, filesystem and device statistics, timers/failed units, currently visible replication jobs, and metadata filenames/ages. It intentionally does not print replication-state file contents, which may contain private configuration or tokens.

## Interpretation and limitations

* A `PASS` means all required read-only commands completed; **it does not prove restore viability or that the most recent mars snapshot has arrived**.
* Compare the latest received timestamp and UUID to the current `mars` source and replication receipt/state using approved read-only methods before approving a pilot. A recent received subvolume by itself does not establish healthy replication.
* The known previous receiver diagnostic failure refers to an obsolete `/@data/diaries-mars-replica/pluto` path. Do not create this directory or change the receiver's layout to satisfy that old diagnostic.
* `btrfs device stats` may show historical counters; nonzero values need assessment, not automatic remediation.
* Any failure, unexpected layout, missing receipt or unresolved replication condition blocks the Step 10 operator-approval gate. No `legacy-delete` command or approval file belongs in this step.

## After capture

Generate a new Diaries source bundle, or attach the `receiver-preflight` files. Review them alongside `evidence/Step 10/fresh-preflight/` from `mars`. Step 10 remains OPEN until an explicit operator decision is recorded about one named snapshot (candidate `@data` ID `19605`), including Step 11 stop conditions.
