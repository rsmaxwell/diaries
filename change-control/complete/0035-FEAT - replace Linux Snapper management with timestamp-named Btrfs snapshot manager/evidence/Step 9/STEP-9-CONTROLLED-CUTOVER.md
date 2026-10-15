# 0035-FEAT Step 9 — Controlled scheduler migration, rollback and close-out

**Status:** CLOSED — Gates 9A and 9C PASS, Gate 9B accepted as no-change adoption (2026-10-15).

## Source baseline

Derived from uploaded Playbooks source bundle `playbook-sources-20261015-114710.zip`, and Diaries `diaries-sources-20261015-114713.zip`. Record current `git rev-parse HEAD` on both repositories before operator execution. Step 8 closure remains accepted.

## Gate 9A — read-only three-host preflight

Use `verification/0035-step9/preflight.yaml`. Collect timer enabled/active states and last trigger values, `mars` manager status and dry-run, `mars` native push result and legacy rsync conflict, `backup` receiver passive status and legacy files, `pluto` schema-2 publication. **No timers or snapshots are modified.** Evidence: `/tmp/0035-step9-preflight.txt` (pending). Acceptance: three hosts reachable, no changed tasks, no unexpected receiver timers or legacy off-site rsync conflict.

## Gate 9B — explicit separate authorization required

The existing `btrfs_snapshot_activation_enabled` controls BOTH create and prune timers. Do not enable casually: although Step 8 validated dry-run retention and protection, automatic destructive pruning on `mars` still needs a deliberate go/no-go and production evidence plan. `btrfs_snapshot_snapper_handover_enabled` is separate; legacy numeric snapshots must age naturally. `btrfs_native_push_schedule_enabled` governs the source sender and checks for conflicting rsync transport. Receiver-local snapshot timers stay off. Do not retire legacy Snapper cleanup or enable `backup` timers under Step 9 without separate approval.

## Gate 9C — verification, rollback and closure

Capture live scheduler state and at least one successful unattended run (snapshot creation and native push where approved), inspect source protection pins and matching receiver receipt, and prove no dual off-site transport. Record commit IDs and revised operational instructions. Rollback is schedule-only: preserve snapshot repository, pins, receipts, and accepted parents. Do not treat rollback as permission to delete or reseed.

**Outstanding:** Gate 9A on-host execution, explicit 9B approval and controlled activation if needed, 9C live verification/rollback review, final feature closure. Do not mark Step 9 or 0035-FEAT CLOSED yet.

## 2026-10-15 Gate 9A/9B outcome

Gate 9A PASS on all three hosts with zero changes; see `GATE-9A-9B-ACCEPTANCE-20261015.md`. Gate 9B adopts the existing target scheduler state with **no new cutover**. Gate 9C read-only final verification and rollback assessment remain outstanding. The already-active prune schedule is **not** a request for additional pruning.

## 2026-10-15 final Step 9 closure

Gate 9C read-only health and preservation checks passed across `mars`, `backup`, `pluto` (`changed=0 failed=0`). No schedule changes were needed or performed. See `STEP-9-CLOSURE-20261015.md` and retained full transcript. Earlier pending sections above are historical pre-execution guidance superseded by the dated closure.
