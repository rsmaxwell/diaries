# Step 3J — Durable journal staging (intermediate gate)

Implemented two internal primitives in the permanent snapshot manager:
`receiver_journal_write` uses exclusive creation, file fsync, and parent-directory fsync;
`receiver_journal_finish` refuses journal removal until both the named snapshot
and receipt are absent, then unlinks and fsyncs the parent directory.
Neither primitive is exposed as a CLI command. `receiver-prune` still fails
unconditionally, including when configuration enables it.

Local regression: Python compilation passed; 9 of 9 simulated-filesystem
regression tests passed on 2026-10-23. No Btrfs snapshots were created or
deleted; no remote systems were accessed.

## Outstanding gates

This is not complete Step 3J transaction execution. It does not implement
the cross-host lock-held deletion protocol, receipt unlink with fsync,
transaction state reconciliation, crash-proof Btrfs deletion, safe pin
release, or disposable real-Btrfs tests. No production deployment or
receiver pruning is permitted. Feature Step 3 remains OPEN.
