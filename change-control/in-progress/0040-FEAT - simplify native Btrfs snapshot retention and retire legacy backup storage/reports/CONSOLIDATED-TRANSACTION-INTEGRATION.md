# 0040-FEAT — Consolidated receiver deletion transaction integration

Status: **source-level integration passed; production prune DISABLED; feature OPEN**.

## Changes

`roles/snapshots/files/btrfs-snapshot-manager.py` replaces unreachable pre-Step-3J deletion code with an internal `receiver_delete_one_locked` implementation. It validates selected targets against the current verified inventory and retention set, explicitly excludes the protected parent, validates the candidate subvolume identity, invokes the injected source-pin verification callback, durably writes a pending journal, performs the injected subvolume deletion, verifies absence, checks the receipt again, removes it and syncs the state directory, then durably finishes the journal. Exceptions retain the pending journal.

**Safety boundary:** The executor is internal and assumes both receiver locks and source protection are held by its caller. It does not implement that cross-host ownership itself. The `receiver-prune` CLI remains permanently blocked by an explicit exception in this change. It must NOT be enabled in production or wired to an untrusted pin claim or an approval file. This is NOT the completed production pruning transaction.

## Focused offline results

- Python compilation passed.
- New isolated transaction tests: missing source-pin callback fails closed, protected parent cannot be deleted, injected crash retains journal, successful test deletion cleans receipt/journal while leaving protected parent, CLI remains blocked.
- Existing Step 3J and Step 3K: 9 tests each passed.
- Existing receiver lock coherence: passed.

## Remaining final implementation gate

The sender must retain its native-push coordination lock and durable source-side protection context while invoking the receiver, and the receiver must retain its exclusive writer lock during the whole transaction, verify the source pin under a trustworthy protocol, bind explicit approval to the current verified retention plan, and handle interrupted journal recovery. Only after a disposable end-to-end test should a production CLI be exposed. No Ansible installation or production deletion is authorised by this package.
