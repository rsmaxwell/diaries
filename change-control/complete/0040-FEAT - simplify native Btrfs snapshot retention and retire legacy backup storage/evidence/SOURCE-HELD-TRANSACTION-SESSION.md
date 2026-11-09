# Step 3 — Internal source-held transaction session (2026-10-23)

Status: **source-level regression passed; not deployed; Step 3 OPEN**.

Implementation: added `run_source_held_transaction_locked` to the receiver wrapper as an internal adapter that connects the already-tested coordinator to two fresh challenge/response exchanges over the same caller-supplied channel. One occurs before transaction re-planning and another via the snapshot manager callback immediately before the journal. Protected parent UUID propagates to the manager. Missing second response, changed nonce, ineligible candidate, or callback failure fails closed. Success is reported only after the injected transaction completes.

Evidence: 6/6 disposable simulated-transport regressions passed locally on the bundled source. These are **not** Btrfs deletion tests or real SSH sessions. The test uses a candidate stamp only as a fixture and does not delete anything.

Important limitations: this adapter is **not exposed from the production receiver CLI**, does not acquire the two writer locks by itself, and does not grant deletion capability. `mars` currently closes SSH stdin after its single candidate handshake; the next integration must extend the sender to maintain the authenticated channel and pinned source through all challenge rounds. A future privileged service must enforce locks, source-bound session lifetime, manager journal transaction, privilege separation, checkpoint holds, and interruption recovery. The checkpoint manager remains at `receiver_prune_enabled: false`; no sudoers deletion permission is proposed.

Next gates: Cygwin→mango source regression, then consolidate the sender/receiver/manager integration and execute disposal-only Btrfs destructive and interrupted-recovery rehearsals. Keep existing production 19 snapshots untouched. Do not deploy this source-only integration until the combined protocol has been reviewed.
