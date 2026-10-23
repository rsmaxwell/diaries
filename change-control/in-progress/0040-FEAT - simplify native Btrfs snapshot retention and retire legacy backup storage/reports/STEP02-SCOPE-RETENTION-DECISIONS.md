# 0040-FEAT Step 2 — Approved scope and retention decisions

**Status: CLOSED — 23 October 2026.** Operator agreed to the choices across the Step 2 conversation. No files were deleted, timers changed, or production software deployed during Step 2. This is a policy decision, **not** operational deletion authorisation.

## Approved steady state

- **Identical executable, one retention-selection implementation** on `mars` and `backup`; host-specific declarative configuration and role-specific safety checks.
- `mars` creates and prunes only read-only `/media/usb/@snapshots/@data/<timestamp>`; retire unnecessary root snapshots `/media/usb/@snapshots/root/<timestamp>` and mandatory paired-set logic, without affecting protected `@data` snapshots.
- `backup` receives and prunes only read-only `/@data/mars-received/@data/<timestamp>`; preserve `/@data/mars-received/.replication-state/` receipts and `writer.lock`; no local snapshot creation.
- Retain **unchanged** `hourly=48`, `daily=14`, `weekly=12`, `monthly=24`, `yearly=5`, `minimum_age_minutes=30` on both hosts. Apply protection/parent constraints in addition to bucket selection.

## Approved legacy retirement

- `backup`: retire `/@data/backup`, `/@data/.snapshots`, `/@snapshots/@data`, `/@snapshots/root`, **`/.snapshots` including APT-generated root recovery points**; remove or disable Snapper APT hooks, stale Snapper configuration/services/timers and obsolete legacy pruner **through Playbooks**.
- `mars`: retire remaining **legacy Snapper snapshots**, their legacy prune timer/tool path, and native root-snapshot population; stop new root snapshot creation at the accepted cutover. Until then leave the legacy prune mechanism operational, subject to cutover plan and safeguards.
- The operator accepts irreversible loss of historical recovery points that exist exclusively in legacy trees, including pre-9-October-2026 points and potentially historical standalone Diaries generations. The native history begins 9 October 2026; no claim of older native recovery coverage is made.

## Mandatory safeguards not waived by approval

1. Protect held snapshots `20261013-171228Z` and `20261018-165453Z` and all other explicit holds; preserve current Diaries manifest verification and live backup collection on `mars`.
2. Never mutate received Btrfs subvolumes or identities; validate UUID/Received UUID, read-only flag, receipts, and latest viable common incremental parent before candidate deletion. Serialize pruning with native send/receive and checkpoint locks.
3. Do not infer physical reclaim from cumulative `du` output; measure true free space and provide a low-space guard.
4. Source review and adversarial regressions precede deployment. Stage and review Ansible `--check --diff`; keep source/receiver rollbacks. Avoid an expensive repeat full restore unless new risk warrants it.
5. **No deletion authorised yet.** Step 10 must regenerate a fresh path/subvolume-ID/UUID deletion manifest with coverage and writer checks; Step 11 requires a separately reviewed explicit go/no-go before irreversibly deleting anything.

## Close-out decision

All Step 2 policy questions are resolved. **Step 2 CLOSED. Step 3 OPEN.** Evidence basis: user approvals in the 0040-FEAT Step 2 conversation; raw approvals may be saved under `evidence/Step 02/` if exported by operator.
