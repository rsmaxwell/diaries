# 0040-FEAT — Step 3D implementation candidate (NOT APPROVED FOR DEPLOYMENT)

## Scope

Added opt-in `receiver-prune --approval-file` to the shared manager source. Existing source mode unchanged; receiver pruning remains disabled unless `receiver_prune_enabled: true` is explicitly configured. The production receiver configuration is NOT changed in this package. No systemd timer is added or enabled.

## Guards implemented

- Root-only entry point (existing manager), manager lock plus exclusive existing receiver `writer.lock`.
- Explicit root-owned approval file naming the complete current deletion candidate set and a protected common-parent timestamp/source UUID.
- Fail closed on missing/inconsistent receipts or non-read-only snapshots; fail if protected parent is selected.
- Entire candidate list is prevalidated before deletion.
- Durable per-snapshot pending journal under receiver state directory before deletion; interrupted transactions block further pruning pending manual reconciliation.
- Receipt removed only after the corresponding subvolume delete succeeds and the path disappears.

## Evidence performed locally

- `python3 -m py_compile` — PASS.
- Step 3B/3C tests against patched manager — PASS (Step 3C confirmed).
- Step 3D negative test — PASS: missing approval, pending journal, unknown candidate; no deletion.

## Explicit unresolved acceptance gates

1. **Common-parent provenance:** an approval assertion does NOT independently prove that the same snapshot and UUID still exist on `mars`. This must be verified against a fresh source/receiver inventory with replication race protection, or integrated into the sender protocol before any production execute.
2. **Recovery correctness:** interrupted delete/receipt cleanup and pending-journal reconciliation need adversarial fixture tests and an explicit operator recovery contract.
3. **Deletion positive path:** disposable Btrfs subvolumes, actual receipt lifecycle, locks, crashes and qgroup impact need validation.
4. **Race window:** ensure source parent selection/pinning and receiver pruning cannot invalidate an in-flight or just-selected parent. Receiver lock alone does not cover sender selection before remote lock acquisition.
5. **Permission checks:** harden receipt, approval and state-directory ownership/permissions; ensure no symlink attack or unexpected subvolume lineage.
6. **Regression:** existing broad launcher-text assertion needs separate reconciliation.

**Status:** Step 3D implementation candidate only. Step 3 OPEN. Do not enable `receiver_prune_enabled`, do not deploy or invoke receiver-prune, and do not start a pruning timer.
