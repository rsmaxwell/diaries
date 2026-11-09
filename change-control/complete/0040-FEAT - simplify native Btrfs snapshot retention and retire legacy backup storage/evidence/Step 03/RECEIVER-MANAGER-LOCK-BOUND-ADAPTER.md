# 0040-FEAT Step 3 — Private receiver manager-lock-bound adapter

Status: **source implementation and local unit regression only** (Step 3 remains OPEN).

## Change

- Adds private `run_manager_bound_transaction` in the receiver wrapper.
- Requires receiver mode and production prune setting `false`.
- Validates distinct regular manager and receiver writer lock files, then acquires both exclusively (manager first, writer second) for the entire two-challenge transaction and manager callback.
- Binds protected-parent UUID and source-pin recheck to `receiver_delete_one_locked` via the manager callback.
- Keeps the public receiver CLI unchanged; **no production deletion permission, sudoers rule, or timer**.
- On errors, no success response is emitted; the manager retains its pre-existing journal and the source retains its independent pin.
- Corrects the sender regression harness's hardcoded temporary path to accept a source argument.

## Local source regression

`python3 receiver-manager-bound-transaction.py PATH/TO/btrfs-native-push-receiver.py` -> **6 tests, OK**. Tests exercise coordination with injected callbacks and temporary regular lock files; they **do not delete actual Btrfs subvolumes**.

## Outstanding before destructive capability

- Validate combined sender/receiver over an actual SSH lifecycle, without enabling production deletion.
- Establish the isolated privileged callback and guarantee the source lock/pin throughout.
- Test real deletion and interrupted recovery in disposable Btrfs subvolumes, including journal and receipt reconciliation.
- Deploy only after approved check/diff, safety acceptance, idempotency and rollback review.

Production receiver pruning stays disabled; the 19 received snapshots and historical recovery holds are out of scope for destructive testing.
