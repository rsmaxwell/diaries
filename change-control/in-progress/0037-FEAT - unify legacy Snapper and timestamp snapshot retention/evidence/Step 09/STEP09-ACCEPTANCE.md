# Step 09 — Controlled deployment evidence

Status: **CLOSED (2026-10-20) — evidence reconciled; see STEP09-FORMAL-CLOSURE.md.**

Record the actual `mango` source SHA-256, `mars` pre/post deployed SHA-256, the Ansible backup filename, command outputs, differences in timers/services/configuration, native dry-run plan, legacy read-only plan, and any detected changes/errors.

## Acceptance gates

- Deployment affects **only** `/usr/local/sbin/btrfs-snapshot-manager` on `mars` with `backup=yes`, owner root, mode 0755. No full-role playbook.
- Before and after source/deployed manager SHA-256 equality verified against `mango` source; deliberate difference from the prior deployed file expected.
- New `legacy-delete` command is available, but no approval file is created and no `legacy-delete --execute` runs.
- Native `create` and `prune` systemd unit definitions and timer states are unchanged. `legacy-delete` does not occur in `ExecStart` definitions.
- Native `status`, `list`, `prune --dry-run`, and `legacy-plan` succeed. Review any changing counts in light of normal scheduler activity; do not expect identical snapshot lists across time.
- Existing Snapper snapshots/replication data are untouched. Off-site receiver path mismatch remains a known diagnostic limitation; do not run snapshot manager on `backup` or change its directory layout as part of this step.
- If any gate fails, **stop**, preserve evidence, and consider the operator rollback procedure. Do not automatically restore an older binary while a scheduled native job might be running.

No live legacy deletion in Step 9. Pilot approval belongs to Steps 10–11.
