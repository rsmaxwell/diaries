# 0040-FEAT — Sender-held prune preflight (accelerated integration)

## Scope
Adds `btrfs-native-push --prune-preflight` on mars, under the existing native-push lock. It calls the previously tested `prepare_prune_parent()` operation to persist the source protection and verify the receiver under writer.lock, then checks the accepted-parent identity is uniquely present in the receiver listing.

The result deliberately reports `authorizes_prune=false`, `deletion_executed=false`, and `retention_candidates=not_calculated`. Receiver pruning remains blocked in the snapshot manager. The existing `--latest` path is unchanged.

## Evidence
Local Python compilation passed. Five mocked regression tests passed for valid handshake, absent/duplicate parent, failed pin, and CLI gating. The test does not contact mars or backup.

## Remaining acceptance gate
A privileged, constrained receiver deletion endpoint holding writer.lock through verified retention selection, source protection lifetime and recoverable journal/receipt operations is **not implemented**. It must be designed and tested before enabling deletion. This source step is not authorisation to run production pruning. Protecting or releasing a source pin modifies state on mars; never execute the new command casually in production.
