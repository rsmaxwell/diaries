# 0038-FEAT Step 06 — Formal acceptance

**Decision: CLOSED — 21 October 2026.**

## Evidence provenance

- `note(20261020-203934).txt` — `backup` post-deployment status, JSON, timer states and 14-receiver-subvolume baseline (IDs `55593` through `55792`).
- `note(20261021-071157).txt` — `backup` installed executables/permissions/Python syntax, replication-state files and directory.
- `note(20261021-071328).txt` — `backup` Btrfs snapshot `show`, latest receipt JSON and full received subvolume inventory.
- `note(20261020-205235).txt` — earlier `mango` check-mode Ansible convergence (Step 5 accepted evidence, reused for context only).

Original raw logs remain user-supplied evidence and are **referenced rather than fabricated or copied into this package**.

## Verified receiver-side operation

- New incremental timestamp: `20261021-030006Z`; destination: `/@data/mars-received/@data/20261021-030006Z`.
- Btrfs subvolume ID `55805`, **Received UUID** `c0ad8538-dc61-bc48-8922-6c37eaf1a902`, flag `readonly`. Btrfs local UUID is different, correctly; compare receipt to **Received UUID**, not local UUID.
- Receipt `schema=1`, `transport=btrfs-incremental`; `source_uuid` and `received_uuid` each equal `c0ad8538-dc61-bc48-8922-6c37eaf1a902`.
- Parent `20261020-030026Z`; `read_only_verified=true`; `source_send_exit=0`; `receiver_receive_exit=0`; completion `2026-10-21T03:32:02.616684+00:00`.
- Fifteen received subvolumes enumerated; the original 14 named snapshots and subvolume IDs are retained, with new ID `55805`.
- All three installed manager/history/verifier programs compiled as Python and are root-owned, `0755`. Fifteen timestamped receipt files mode `0600`, receiver state directory `0700`, owner `richard`.
- The local manager reports a valid Btrfs snapshot root and disabled Diaries verification, with no locally managed timestamp sets; all three local snapshot timers remain disabled and inactive.

## Qualification and decision

`qgroups_status=unavailable;reason=unexpected_output` is a non-blocking optional status-parser diagnostic; no Btrfs qgroup repair was demonstrated or needed for this gate. The normal overnight incremental arrival is positive operational evidence, not proof of every future schedule/retention outcome. **Step 6 CLOSED**; progress to Step 7 negative and idempotency regression without manual transfer, restore, pruning or changing received snapshots.
