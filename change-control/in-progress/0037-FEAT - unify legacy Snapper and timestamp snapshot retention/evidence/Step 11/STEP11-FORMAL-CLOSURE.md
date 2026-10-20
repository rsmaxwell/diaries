# 0037-FEAT — Step 11 formal closure

**Date:** 2026-10-20  
**Decision:** **CLOSED — PASSED** (the approved one-snapshot controlled deletion pilot only).  
**Target:** `mars`, Snapper `@data`, snapshot `19605` (created 2026-09-28T00:00:38Z).

## Authorisation and preconditions

The operator explicitly approved deletion of **only** `19605` following Step 10 acceptance. Before executing, the operator independently confirmed Btrfs subvolume UUID `489332dc-3b48-eb40-b59a-d9bd86cc9915`, ID `20165`, read-only flag `ro=true`, and `WOULD-DELETE` in the fresh combined retention plan. The manager checked the strict, temporary root-owned one-ID approval, host/source/config/ID and twice revalidated the current retention plan. No scheduled or general legacy cleanup was enabled.

## Corrective action that preceded pilot

Ordinary Snapper `list` timed out while used-space accounting was enabled. `snapper --no-dbus ... list --disable-used-space` returned the expected legacy inventory. A narrow correction to the common `legacy_snapper_inventory()` command was installed in Playbooks; source SHA-256 and deployed `mars` executable SHA-256 both `200998f4bdf129637025fd94730735d27919d48b1f47941b58846e408f2692c5`. Focused parser check, native regression suite, 20/20 adversarial tests, 14/14 guarded-deletion mocked tests and isolation checks passed on `mango`. Deployment used one targeted Ansible copy rather than reapplying the broader role.

## Destructive action and evidence

The operator's `mars` execution transcript (`execution/operator-execution.txt`) records:

```text
Executing guarded deletion: mars @data/19605
LEGACY DELETE approved host=mars source=@data config=@data id=19605 timestamp=2026-09-28T00:00:38+00:00
LEGACY DELETE completed config=@data id=19605
Guarded deletion completed successfully
```

The post-execution independent Snapper CSV excludes `19605`; `legacy-plan` excludes it too. The remaining 24 numbered snapshots (excluding Snapper virtual/current number 0) comprise **16 KEEP, 8 WOULD-DELETE**. No other disappearance was observed when comparing the supplied pre/post lists.

## Post-deletion acceptance

| Requirement | Evidence/result |
| --- | --- |
| Only operator-approved snapshot removed | PASS — `19605` absent; 24 remaining |
| Protected legacy retention representatives | PASS — 16 KEEP, including newest ID `19886` |
| Native complete-set history | PASS — 58 complete, 0 incomplete |
| Native deletion dry-run | PASS — 0 proposed sets |
| Checkpoint holds | PASS — `20261013-171228Z`, `20261018-165453Z` |
| Source replication pin | PASS — `20261020-030026Z` |
| Production dataset verification | PASS — marker valid, backupId `20261020-003106Z` |
| Btrfs device error counters | PASS — read/write/flush/corruption/generation all zero |

Source-side replication protection remained in place; the post-delete transcript does **not** claim a new independent receiver or restore test was performed after the pilot. Earlier Step 10 receiver evidence is relied on for context. The earlier quoted `snapperd` process was its D-Bus service, not by itself an observed competing destructive operation.

## Scope, exceptions and next work

This closure is strictly Step 11 **single-snapshot pilot** acceptance, not approval for further deletions or unattended legacy retention execution. The eight remaining WOULD-DELETE IDs are advisory only. Approximately 16,000 stale Btrfs qgroups were observed during diagnosis; no qgroup deletion, quota disablement, filesystem repair or scheduler change occurred during this pilot. Perform qgroup cleanup only under its own maintenance assessment, checks and explicit decision.

**Evidence:** `execution/operator-execution.txt`; `execution/operator-post-verification.txt`; `execution/manager-source-and-regressions.txt`; `execution/manager-deployment-and-live-plan.txt`; `execution/manager-final-preflight.txt`; `execution/SHA256SUMS.txt`. Historical read-only Step 11 baseline remains in `pre-execution/` and `operational-check/`.
