# 0040-FEAT Step 12 — Simplified receiver retention: implementation candidate

**Date:** 7 November 2026  
**Decision:** Source implementation and fixture regressions prepared. **Live receiver pruning NOT AUTHORISED.** Step 12 remains OPEN.

## Accepted earlier work (not repeated)

- Retired legacy receiver transaction journal safely archived, with no deletion of historical snapshots or receipts.
- Source/receiver simple agreed-parent records bootstrapped, manual real transfer accepted.
- Latest-snapshot executable deployed to mars/backup and unattended service accepted, with first scheduled 7 November 03:30 UTC transfer successfully advancing the same current/prior parent records on both hosts.
- Permanent Ansible host variables preserve the simplified sender; normal scheduling preview on mars was `changed=0`.

Evidence: previously uploaded 7 November systemd and state readback terminal transcript and Step 12 acceptance reports. This report records no new live actions.

## Implemented change

The *existing shared* `roles/snapshots/files/btrfs-snapshot-manager.py` now provides `receiver-simple-plan` (read-only) and `receiver-simple-prune` (explicit separate enable gate) in addition to source-mode prune. Retention bucket logic is reused from `retention_keep_set`; this does not introduce a second retention algorithm. The older receipt-based receiver manager commands remain unchanged and disabled for deletion.

A simplified received snapshot is verified from Btrfs `Received UUID`, subvolume ID and read-only property. The manager refuses bad/missing current or previous agreed-parent identities, an unexpected receiver filesystem, altered or duplicated received UUIDs, symlinks, unexpected checkpoint holds, unfinished journals and snapshots not conforming to the managed collection. Historical receipt-backed snapshots are protected without trusting their receipt metadata. An orphaned receipt causes refusal rather than cleanup. Pins protect the current and previous agreed-parent generations, anything newer than current parent, any legacy agreed-parent pins and independent root-controlled checkpoint holds.

Deletion code remains dormant unless `receiver_prune_enabled` is explicitly true; maximum 20 subvolumes per invocation; one candidate is revalidated under the manager lock before each deletion. The manager records a durable root-only `.simple-prune-pending.json` journal before Btrfs deletion; any uncertain outcome blocks future pruning pending operator reconciliation. It never deletes a legacy receipt. The new receiver service/timer default disabled, with a proposed 04:15 UTC schedule after the 03:30 UTC sender job.

## Source and test checks

The patch is based on **playbook-sources-20261106-163125.zip** (source bundle) and the **diaries-sources-20261106-163130.zip** change-control bundle. Current live Git revision and any later working-tree changes on mango must be checked before applying. The Playbooks ZIP intentionally omits the existing `roles/btrfs-replication/README.md`, `btrfs-simplified-replication.py` and its original tests to avoid overwriting reconciled local edits.

Local fixture verification: 15 new receiver-prune tests PASSED; 11 agreed-parent pin tests PASSED; source-selection, mixed snapshot source and adversarial tests PASSED; 20 simplified replication tests PASSED; 3 simplified parent-protection tests PASSED. Python syntax, YAML parsing and template guards checked. No live Btrfs or Ansible commands were run in the preparation environment.

### Next acceptance gates

1. Inspect source/package diffs against the current `mango` Playbooks working tree. Record Git SHA/dirty paths and changes. Run full consolidated tests, inspect the new manager checksum, and preview `btrfs-replication.yaml --limit backup --tags simplified-receiver-retention --check --diff` with explicit install=true, prune_enabled=false.
2. Deploy **install-only** to backup after accepting the preview. Confirm the new timer is stopped and disabled and the existing sender unchanged. Execute read-only `receiver-simple-plan` under the shared lock; save every `RETAIN`/candidate output, Btrfs UUIDs, historical receipts/holds and qgroup status.
3. Run the feature-local disposable real-Btrfs test with `--run` on mango, in an isolated loopback fixture. Do not use a live backup directory.
4. Review the exact live candidate set and recovery coverage, and obtain **separate explicit authorisation** for live destructive pruning. This may require policy decisions for receipt-backed historical snapshots, which this implementation intentionally preserves rather than silently expiring.
5. After approval only, enable the dedicated receiver timer via permanent Ansible inventory and check-mode preview, perform bounded deletion with full logs, verify Btrfs state/qgroups and both agreed-parent records, and demonstrate idempotence and rollback to disabled timer. Only then consider closing Step 12.

**Safety note:** New software and timer installation alone does not authorise destructive snapshot operations. Avoid running `receiver-simple-prune`, even manually, on `backup` before the separate deletion gate.
