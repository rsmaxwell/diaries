# 0040-FEAT — Step 3H protected-parent handshake (intermediate gate)

Status: IMPLEMENTED FOR SOURCE REVIEW; **NOT** authorised for production pruning.

## Change

* `btrfs-native-push --prepare-prune-parent` holds the sender's existing native-push lock while it calls `protect_common_parent()` to persistently pin the common snapshot on mars, then invokes a new receiver read-only `--check-protected-parent` command.
* The receiver command takes its existing `.replication-state/writer.lock`, checks the exact named snapshot's accepted receipt and Btrfs received UUID via the restricted endpoint, and rejects pending deletion journals. It returns `authorizes_prune: false` unconditionally.
* The existing snapshot manager's receiver-prune operation remains blocked. No receiver deletion or timer enablement in this package.
* If remote validation fails after source pinning, the source pin **remains** and requires later operator reconciliation; no automatic unpin.

## Evidence (offline fixtures)

* `python3 -m py_compile` on both changed programs: PASS.
* `tests/step03h-protected-parent-handshake.py` offline regression: PASS.
* Existing Step 3E and Step 3F tests against the updated sender: PASS.
* Negative cases: missing receipt, wrong UUID, remote failure, unexpected deletion-authorisation claim.

## Important limits

This is a cross-host *readiness handshake*, not an end-to-end prune lease. The source pin is durable, and receiver validation happens under its writer lock, but that lock is released after the read-only receiver check. **No receiver deletion may be enabled based on this check.** A future step must provide a deletion transaction with durable source-pin identity, receiver lock ownership throughout deletion, lock ordering, restart reconciliation, and explicit receipt journal recovery. In particular, source-pin release must be coordinated with outstanding prune transactions. This implementation has not been deployed to either host.

## Next gate

Apply with Beyond Compare 4, run the source regression on mango, then implement transaction-bound receiver deletion only after disposable Btrfs and failure-injection tests. Step 3 remains OPEN.
