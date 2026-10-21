# Mandatory feature workspace / production-tree hygiene

## Location

The authoritative workspace is this **0037-FEAT directory** under `diaries/change-control/todo/` until closure, then the entire tree moves to `diaries/change-control/complete/`.

| Feature-specific content | Put it here |
| --- | --- |
| Ad-hoc scripts and temporary code | `tools/` |
| Test drivers, synthetic fixtures, temporary tests | `tests/` |
| Inventories, Snapper listings, dry-run plans, reconciliation reports | `reports/` |
| Raw shell output, command transcripts, runtime captures, approvals | `evidence/Step NN/` |
| Disposable intermediate work, extracted inputs, scratch | `scratch/` (do not commit sensitive/bulky items by default) |
| Adopted production files and justification | `PROMOTION-MANIFEST.md` |

Only deliberate long-lived utilities and regression tests belong in `playbooks/roles/snapshots/` or another production source location. Do not deposit evidence directories, temporary inventories, one-off scripts or fixtures in those paths merely because their subject is a snapshot role. Do not place feature-only listings in generic project roots or other features.

## On-host execution

Prefer generating scripts in this workspace and execute remotely via Ansible temporary transport, or copy to an explicitly bounded `/tmp/0037-feat-...` directory with ownership, restrictive permissions, cleanup on exit, and a documented removal check. Any required intermediate staging elsewhere must be logged as an exception and removed by Step 13. Keep outputs under the feature workspace, not permanently on `mango`, `mars`, `backup` or `pluto`.

## Before completion

Audit `git status`, generated files and host-side temporary paths; record all production promotions and cleanup actions. Check evidence for secrets, access tokens, personal file content or unnecessarily bulky snapshot listings before committing. Retain minimal redacted evidence needed for audit.
