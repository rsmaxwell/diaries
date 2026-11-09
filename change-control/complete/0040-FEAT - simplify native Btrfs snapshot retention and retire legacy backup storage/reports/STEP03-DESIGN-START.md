# 0040-FEAT Step 3 — Design shared manager and configuration contract

**Status: OPEN — design examination begun 23 October 2026.** No source or production modifications in this stage.

## Architecture choices already fixed

- One production `btrfs-snapshot-manager.py` source deployed identically on both hosts; use `source` and `receiver` declarative modes rather than maintaining a separate pruning implementation.
- Managed collection is `@data` only: locally created snapshots on `mars`, accepted received snapshots on `backup`.
- Retention buckets and minimum age remain unchanged on both hosts; protection and replication safety may require extra retained snapshots.
- Receiver must reject `create`; do not enable receiver prune until controlled gates and no competing deletion authority.
- Existing native sender/receiver continue to own transfer, receipts, and the receive writer lock.

## Step 3 design questions to resolve through read-only source review

1. Inventory `btrfs-snapshot-manager.py`: `Config`/sources schema, `scan`/completeness assumptions, create, retain/prune, holds, lock lifecycle and legacy CLI dispatch; define minimal backward-compatible transition from paired sources.
2. Inventory `btrfs-native-push.py` and `btrfs-native-push-receiver.py`: exact parent-choice algorithm, accepted-lineage/receipt contract, lock acquisition order and what an interrupted receive leaves behind.
3. Decide source and receiver config schema. Avoid empty-string fallbacks allowing receiver to run source-only actions. Define configured inventory root and readonly received-subvolume validation, and fail-closed behavior for absent receipts or identity mismatch.
4. Specify protected snapshots: explicit holds, current accepted common parent, any in-flight parent or pending transfer ancestor, age-based keepers and protected evidence snapshots.
5. Define atomicity/recovery of receipt removal, subvolume deletion and interrupted cleanup, and how source/receiver reconcile different retained sets.
6. Define the migration staging: preserve old pairs and legacy-prune until alternate invariants pass; no feature-private scripts in permanent Playbooks roles; activate sender/receiver timed tasks only at approved gates.

## First execution stage: read-only source-contract inventory

Use `mango` Playbooks to locate current CLI/config/snapshot and native send/receive lock and parent-selection functions. Capture relevant excerpts and existing tests. No test/deployment step yet. Record results under `evidence/Step 03/` before specifying the final config schema.

**Gate to mark Step 3 CLOSED:** design interfaces and invariants reviewed against actual code, explicit failure modes documented and test matrix approved. Subsequent Step 4 implements code.
