# Step 3 — Private sender subprocess lifecycle

Status: SOURCE-ONLY; **not deployed**, **not a Step 3 closure**.

## Implementation

The internal `run_private_transaction_process()` wrapper acquires the existing source push lock, starts an injected subprocess (test harness uses a local Python child), calls the pre-existing two-challenge sender protocol, and always closes input, terminates/kills and reaps the child when necessary. The source lock is held until reaping finishes. It never clears the persistent source pruning pin. No CLI command, timer or receiver privilege is introduced.

## Local regression (2026-10-23)

`sender-private-process-lifecycle.py` run against the packaged Playbooks sender: five tests passed. Cases: successful two challenges, nonzero child exit, abort on changed second source pin while the child waits, absent source lock, no CLI exposure. These tests do not contact mars or backup and do not invoke Btrfs.

## Outstanding before enabling receiver pruning

* Run the portable regression on mango against applied Playbooks source.
* Implement a **bounded full-session deadline** for blocked reads; the present protocol uses blocking `readline()` and the cleanup owner cannot rescue a permanently silent process without a watchdog.
* Validate SSH start/disconnection handling, manager/receiver lock release, privilege separation, journal/receipt reconciliation and crash recovery in disposable Btrfs rehearsal.
* Preserve independent historical checkpoint holds. Production `receiver_prune_enabled` stays `false`.

No live deletion is authorised by this evidence.
