# 0048 — Planning source review (2026-11-11)

**Classification:** planning evidence only. Neither 0046 nor 0047 closure is asserted here; no on-host modes, deployments or tests for 0048 have been executed.

## Sources available when the plan was authored

- `0047-FEAT-diaries-change-control-and-verification-20261111.zip`: 0047 original scope, entry-point migration and acceptance gates.
- `0047-FEAT-diaries-source-mode-verification-20261111.zip`: 0047 source-mode restoration and reconciliation tools, and Step 2 permission-preservation report.
- `0047-FEAT-playbooks-preserve-source-modes-20261111.zip`: `roles/backup-collection/source-modes.json`, source-mode regression, source-copy tasks and role documentation.
- `0046-FEAT-diaries-inventory-migration-revised-acceptance-20261110.zip`: deferred inventory migration plan and all-host installed-state contract.
- User's explicit requirement: source-file modes are authoritative; rsync must preserve them without `--chmod`. After 0046 and 0047 closure, inspect whether historically restored precise modes are actually required, and retire the restoration tool if safe.

## Confirmed design tension

The 0047 source-mode contract records nine include/exclude filters as `0664` and five source directories as `0750`, corresponding to the accepted 0045 installation. These modes are not fully represented by Git. The existing `install_user_scripts.yaml` gives target directories `0750` via Ansible's file task; archive-mode rsync subsequently adopts source directory permissions. A normal fresh clone may give source directories different modes, potentially causing permission widening or idempotence churn. This must be explicitly tested.

`install_machine_scripts.yaml` also copies source entries using rsync and separately renders executable templates with explicit `0744` mode. Thus, the review must not conflate copied filter files with templated launchers. No claim is made that `0644`/`0755` is adequate or inadequate until the actual effective users, parents, access policies, and consecutive deployments have been examined.

## Sources to refresh when 0048 starts

Read both closed 0046/0047 feature records from `change-control/complete/` and obtain a fresh Playbooks checkout at its actual published revision. Inspect the implemented task order and the post-0046 inventory configuration. The named ZIPs are historical planning inputs and must not override later accepted local changes. Preserve the 0047 historical source-mode tooling even if its active dependency is subsequently retired.
