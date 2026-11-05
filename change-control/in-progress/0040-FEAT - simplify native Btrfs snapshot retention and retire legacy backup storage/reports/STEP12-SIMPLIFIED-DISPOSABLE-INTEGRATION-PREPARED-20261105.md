# 0040-FEAT — Step 12 simplified real-Btrfs integration preparation

**Status: PREPARED; not yet executed on mango or accepted. Step 12 remains OPEN.**

The previous consolidated source regression, supplied as
`note(20261105-133205).txt`, showed 31 passing tests and passing pruning
source-selection and shared-retention checks on `mango`.

This increment introduces a **one-off disposable real-Btrfs test** in the
Diaries feature's `tests/` directory. It tests actual simplified receiver
CLI operation on loopback Btrfs datasets, rather than the superseded staged
receiver protocol. It covers a native truncated incremental stream, recovery
from a writable incomplete candidate, successful retried native receive,
receiver-side advancement, sender-side lost-acknowledgement recovery and
non-blocking lock back-off. It does not modify production Playbooks code.

The test will report whether the truncated `btrfs receive` left a candidate or
removed it. In the latter case it creates a **disposable writable subvolume**
to represent a power-loss residue before testing cleanup. That distinction
must be preserved in the acceptance evidence.

Successful test execution will justify proceeding to consolidated operational
verification of the real `mars` ↔ `backup` SSH/sudo path and service cutover;
it does not itself authorise activation, rollback removal, pruning activation
or feature closure.

No full restoration or repetition of the previously accepted A→B production
replication is required by this test.

Run instructions: `tests/README-STEP12-SIMPLIFIED-REAL-BTRFS.md`.
