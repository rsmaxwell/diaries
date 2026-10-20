# 0037-FEAT Step 10 — Operator approval and closure

**Decision: APPROVED, limited to one Step 11 pilot.**  
**Recorded:** 2026-10-20 (operator approval given explicitly in the project conversation; no exact approval clock time asserted).  
**Step 10: CLOSED for the purpose of selecting and authorising this one pilot; Step 11 execution remains separately gated.**

## Exact approved identity

| Field | Approved value |
|---|---|
| Host | `mars` |
| Source name | `@data` |
| Snapper configuration | `@data` |
| Legacy Snapper snapshot ID | `19605` |
| Creation timestamp (UTC) | `2026-09-28T00:00:38+00:00` |
| Btrfs subvolume ID at reviewed preflight | `20165` |
| Btrfs UUID at reviewed preflight | `489332dc-3b48-eb40-b59a-d9bd86cc9915` |
| Reviewed plan decision | `WOULD-DELETE` |

The operator expressly approved **only** snapshot `19605` for a **single controlled Step 11 deletion pilot**, subject to previously stated safeguards. This is not authority to delete any other snapshot or to enable scheduled legacy pruning. No actual deletion has occurred as part of Step 10.

## Basis and limits

- Fresh 2026-10-20 `mars` read-only inspection reported candidate `19605` as `WOULD-DELETE`, with the identity above; 58 complete native sets, zero incomplete, two checkpoint holds, and an off-site replication pin at `20261020-030026Z`.
- Receiver capture recorded `/@data/mars-received/@data/20261020-030026Z`, a read-only received subvolume and corresponding replication receipt. This is evidence of recent receipt, **not** an independently tested recovery/restore.
- `backup.service` was a missing unit with a stale failure dated 2026-01-29; `user@0.service` failed during root user-manager shutdown on 2026-10-15. These were assessed as non-blocking to this specific pilot based on observed subsequent replication, not proved unrelated in all circumstances.
- The operator accepts a one-snapshot controlled pilot on this evidence, **not** an assumption that a deleted snapshot can be restored.

## Explicit safety conditions

1. Immediately before execution, verify `hostname`, exact Snapper configuration/ID/UTC creation time/Btrfs read-only subvolume ID and UUID against the reviewed values; stop on any mismatch.
2. Capture a new `legacy-plan` and confirm exactly one matching `WOULD-DELETE` candidate for `@data`/`19605`; do not use stale results to justify deletion.
3. Verify native status, holds, replication pins and absence of active snapshot/prune/replication jobs; fail closed on unclear state or missing metadata. Do not change the existing native timers or off-site receiver.
4. The manager must obtain its existing lock, re-plan and revalidate immediately before deletion. No direct manual Snapper deletion, no raw Btrfs subvolume deletion, and no batch operation.
5. The root-owned exact-match approval must be prepared only at the controlled execution gate; restrict it to `mars`/`@data`/`@data`/`19605`. Remove/deactivate it immediately after the attempt, irrespective of outcome.
6. Preserve all historical legacy `KEEP` snapshots, including anchor `19886`; protect native sets and receipt/holds. Abort on any unexpected output and reconcile the resulting state before another attempt.
7. Post-execution: prove ID `19605` absent and all other IDs/pins/holds/native sets unaffected; capture updated plan and status; retain logs in Step 11 evidence. Do not describe it as successful unless those checks pass.

**No executable approval JSON is included in this change-control package.** The example in the Step 11 runbook is deliberately disabled and must not be copied onto `mars` as an active policy.
