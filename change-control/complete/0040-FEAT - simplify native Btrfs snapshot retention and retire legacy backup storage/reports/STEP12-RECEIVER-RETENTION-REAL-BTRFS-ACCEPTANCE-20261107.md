# 0040-FEAT Step 12 — Disposable real-Btrfs receiver-retention acceptance

**Date:** 7 November 2026  
**Result:** ACCEPTED — disposable real-Btrfs test.  
**Scope:** New simplified receiver pruning mechanism only; no live receiver deletion authorisation.  
**Step 12:** OPEN.

## Evidence

- Operator transcript: `note(20261107-103028).txt` (supplied 7 November 2026).
- Authoritative run log generated in the Windows Diaries repository:
  `evidence/Step 12/raw-logs/step12-receiver-retention-real-btrfs-20261107-103007.txt`.
- Test: `tests/verify-0040-step12-receiver-retention-real-btrfs.py`.
- Shared Btrfs manager hash checked on `mango`:
  `da9d7f02b9145c162b8bf4c75bab5921b885f55c8b9fde1f94c95894f6cf8274`.

The operator executed the test from the Windows Cygwin Diaries checkout by streaming it to `mango`. Prerequisites were confirmed: available loop device `/dev/loop4` and `mkfs.btrfs` at `/usr/sbin/mkfs.btrfs`. The non-mutating preview printed `PREVIEW ONLY`. The controlled `--run` on `mango` then reported:

```text
RECEIVER-SIMPLE-DELETED 20261002-010000Z subvolume_id=257
RECEIVER-SIMPLE-DELETED count=1
RECEIVER-SIMPLE-DELETED count=0
PASS: disposable received Btrfs prune, holds, two parent pins, receipt preservation, disabled gate and idempotence
PASS: Disposable real-Btrfs receiver retention test
PASS: Receiver retention real-Btrfs verification
```

**Accepted:** One eligible disposable received Btrfs snapshot was deleted. A second execution found zero deletions. The test reported successful protection for the two agreed-parent generations, holds, historical receipts, and the disabled deletion gate. The test reported overall success. This acceptance does not assert a live receiver prune or a completed restore test.

## Latest live receiver plan (already accepted, read-only)

The 7 November 2026 receiver plan on `backup` reported:

```text
RECEIVER-SIMPLE-PLAN {"candidates": 0, "enabled": false, "historical_receipts_protected": 27, "holds": ["20261013-171228Z", "20261018-165453Z"], "keep": 30, "parent": {"timestamp": "20261107-030031Z", "uuid": "7778dda5-2b91-8c4e-8b1a-1dd038a3675b"}, "prior": {"timestamp": "20261106-160001Z", "uuid": "e28d1139-a311-944c-a048-b60874a4dd02"}}
```

The installed receiver manager checksum matched its source. Receiver pruning and its timer were confirmed disabled/inactive. No production snapshots were deleted during these checks.

## Remaining policy and operational gates

The receiver planner currently treats any snapshot with a historical legacy receipt as permanently protected, independently of the usual retention buckets. This is a deliberate conservative migration safeguard, but it can keep historical snapshots forever as the rest age out. Current live plan has no deletion candidates, so a live prune at this point would not demonstrate reclamation.

Recommended next implementation: separate **preservation of legacy receipt evidence** from **permanent retention of the snapshot itself**. Retain auditable receipt data outside the active receiver's legacy receipt namespace, enforce the established retention buckets, and continue preserving current/prior agreed parents, explicit checkpoint holds, any newer/unacknowledged snapshots and required legacy pins. Ensure that deletion does not create orphan-receipt refusal on the next read-only plan. Produce a complete read-only candidate inventory before any live destructive operation.

**Not authorised:** enabling the receiver prune timer, deleting a live snapshot, releasing checkpoint holds, deleting historical receipt records, or marking Step 12 CLOSED. Destructive live pruning requires separate explicit approval after the revised candidate list and rollback implications have been reviewed.

The accepted replication/bootstrap/manual transfer/first unattended transfer, permanent inventory and installation evidence remain valid and should not be rerun solely for this gate.
