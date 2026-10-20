# Step 1 evidence checklist — CLOSED 2026-10-19

- [x] Playbooks source baseline and SHA-256 manifest captured.
- [x] `mars` current-state capture: `evidence/Step 01/mars-capture.txt` (105 lines).
- [x] `backup` current-state capture: `evidence/Step 01/backup-capture.txt` (43 lines).
- [x] Legacy Snapper inventory: `root` 0 numbered, `@data` 25 numbered (operator console `note(20261019-074424).txt`).
- [x] Runtime timers, native inventories, source policy and protection scope reviewed; exact deletion-time state must be recaptured before subsequent steps.
- [x] Receiver layout identified as `/@data/mars-received/@data/`, 13 received Btrfs subvolumes; receiver-manager diagnostic path mismatch documented, not repaired.
- [x] Explicit decision: Step 1 **CLOSED** for baseline/scope purposes, no production modifications or deletion authority.

## Outstanding limitation carried forward

The `backup` manager's diagnostic configuration expects `/@data/diaries-mars-replica/pluto`, which is absent. Do not interpret the failing diagnostic as healthy, and do not change current receiver directories within this step. Reconcile as part of later non-destructive deployment checks. Direct Snapper inventory is in operator terminal evidence, not the zip's raw capture files.
