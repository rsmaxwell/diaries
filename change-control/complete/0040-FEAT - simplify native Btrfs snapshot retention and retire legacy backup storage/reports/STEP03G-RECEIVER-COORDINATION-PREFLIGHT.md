# 0040-FEAT — Step 3G, receiver lock-held preflight (intermediate gate)

Status: **IMPLEMENTED FOR SOURCE REVIEW; STEP 3 REMAINS OPEN**.

## Change

The shared snapshot manager now exposes `receiver-coordination-check --snapshot TIMESTAMP --source-uuid UUID` in receiver mode. Its CLI acquires the existing manager lock and then the receiver `writer.lock`, matching the receiver's exclusive-lock boundary before inspecting the receipt inventory. It verifies a specified received parent against the corresponding receipt, refuses missing parents, mismatched source identities and unresolved prune journals, and emits `authorizes_prune=false`. This is not permission to delete and does not mutate snapshots, receipts, or source-side pin state.

Source-pin protection and receiver verification are still separate transactions. **There is no distributed lock-held atomicity across mars and backup yet.** The Step 3E unconditional receiver-prune prohibition remains in place, regardless of configuration.

## Acceptance evidence

Run the local feature regression streamed from Cygwin to mango using the Playbooks source path as the first argument. The regression uses temporary synthetic state and patches the receiver inventory; it does not contact Btrfs or production machines. Tests cover a matching receipt, mismatched UUID, absent parent, invalid timestamp, pending journal and explicit non-authorisation.

## Remaining gates

- Design a durable cross-host source pin and receiver transaction handshake, without lock-order deadlocks.
- Validate sender and receiver interactions against a disposable Btrfs setup.
- Test successful deletion and crash/restart recovery with receipt consistency.
- Independently prove source/receiver parent availability throughout deletion.
- Keep production receiver deletion and timers disabled until later acceptance gates.
