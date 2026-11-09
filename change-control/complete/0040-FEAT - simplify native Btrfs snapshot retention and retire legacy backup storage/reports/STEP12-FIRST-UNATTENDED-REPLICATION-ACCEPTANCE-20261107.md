# 0040-FEAT — Step 12: First unattended simplified replication acceptance

**Date:** 7 November 2026 (UTC)  
**Decision:** **ACCEPTED — unattended simplified replication subgate**. **Step 12 remains OPEN** for separate receiver-only retention/pruning acceptance and final evidence reconciliation. **0040-FEAT remains OPEN**.

## Production run and service evidence

The operator's `mango` terminal transcript records the *actual* unattended invocation of `btrfs-native-push.service` on `mars` at **2026-11-07 03:30:01 UTC**, with `Result=success`, `ExecMainStatus=0` and completion at **03:30:18 UTC** (17 seconds). systemd `ExecStart` is `/usr/local/bin/btrfs-simplified-replication sender cycle`; the journal reports `SUCCESS: common parent advanced to 20261107-030031Z` and a clean oneshot service finish.

The `btrfs-native-push.timer` was **enabled and active**. At observation it showed next execution **2026-11-08 03:30:00 UTC**. The source and receiver agreed-parent JSON readbacks compared equal, with schema 1 and these source snapshot identities:

| Property | Timestamp | Source UUID |
| --- | --- | --- |
| Previous agreed parent | `20261106-160001Z` | `e28d1139-a311-944c-a048-b60874a4dd02` |
| Current agreed parent | `20261107-030031Z` | `7778dda5-2b91-8c4e-8b1a-1dd038a3675b` |

The receiver was invoked with the expected previous-parent identity and acknowledged the new received snapshot. The transcript's final output is `PASS: Scheduled replication state checks` and `PASS: Verification commands completed`.

## Raw evidence and provenance

- Attached operator terminal transcript, byte-preserved: `evidence/Step 12/raw-logs/step12-first-unattended-operator-transcript-20261107-095326.txt` (source upload `note(20261107-095326).txt`).
- Transcript SHA-256: `37d7de30cea8466fd362b3760fc2ee4cf9ee9c93bbbca88c5223fe3cf738b474`.
- Original execution output, stated in transcript as recorded on `mango`: `evidence/Step 12/raw-logs/step12-first-unattended-20261107-095251.txt` (the original `mango` log remains to be reconciled into the authoritative Windows Diaries repository; this package does not claim to contain it).
- Earlier accepted evidence: guarded manual journal retirement/bootstrap and first cycle `step12-controlled-cutover-execute-20261106-155222-1432.txt`; deployment and activation `step12-latest-selection-deployment-20261106-165837.txt`; durable host-vars resolution and Ansible scheduling preview with `changed=0` on `mars` from the 6 November operator logs. These are historical acceptance inputs; do not rerun solely to regenerate them.

## Scope of this acceptance

The first unattended simplified sender-to-receiver transfer is **accepted**. The established 03:30 UTC timer, matching state readbacks, newest-snapshot behaviour and durable Ansible inventory resolve the previously open replication scheduling gate. No further full restore or repeated manual cycle is required merely to corroborate this run.

This is **not** acceptance of automatic receiver pruning. The 0040-FEAT implementation plan's Step 12 explicitly includes a separate receiver retention activation gate. The Playbooks source bundle dated 6 November has `receiver_prune_enabled: false` in the receiver manager template, and the `receiver-prune` implementation refuses live deletion because cross-host common-parent protection is not implemented. Its receipt-based `receiver-inventory` assumes every received snapshot has a legacy receipt, whereas the new simplified replication deliberately creates no such receipt. Thus the original receiver-pruning compatibility must be reviewed/redesigned for the new accepted replication state before any activation or deletion.

**Do not enable receiver pruning, modify historical checkpoint holds, or remove legacy rollback material based on this acceptance alone.**

## Next substantial increment

1. Reconcile the live 7 November raw log and other accepted Step 12 evidence from `mango` into the authoritative Windows Diaries feature directory, preserving Git changes in both repositories.
2. Update shared receiver retention to validate real Btrfs Received UUID, read-only state and the simplified agreed-parent `parent`/`prior` pins **without requiring newly created legacy receipts**, while retaining historical holds, lock protection, and existing historical receipt evidence where available.
3. Run consolidated source/real-Btrfs regression and read-only retention plans, then separately review any concrete destructive receiver-pruning candidates and operational timer changes before enabling pruning.
4. Mark Step 12 CLOSED only after that receiver-retention acceptance and evidence reconciliation; keep Step 13 and 14 independent.
