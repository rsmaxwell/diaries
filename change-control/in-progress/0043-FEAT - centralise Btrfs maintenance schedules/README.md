# 0043-FEAT — Centralise Btrfs maintenance schedules

**Status:** IN PROGRESS — source package implemented and offline verified;
production inventory and timer deployments must be proven by operator logs.
**Opened:** 10 November 2026.

## Goal

Maintain all relevant 0035/0039/0040 Btrfs systemd schedules in one
version-controlled Playbooks file, with both source and receiver snapshot
pruning at **04:15 UTC once per day**, and all current activation/safety gates
intact. Keep the effective schedule in Ansible inventory, not hard-coded into
Btrfs managers or systemd templates.

## Source of truth

- Version-controlled: `/home/richard/playbooks/inventory/diaries-maintenance-schedule.yaml`
- Effective inventory: `/etc/ansible/group_vars/all/diaries-maintenance-schedule.yaml`
- Guarded installer: `/home/richard/playbooks/scripts/maintenance-schedule.py`
- Operational guide: `/home/richard/playbooks/MAINTENANCE-SCHEDULE.md`

The source `btrfs-snapshot-prune.service` will use `--max-delete 32` rather
than 10, solely via inventory. The manager's supported bounded cap is raised
to 32, and all source candidate/hold/parent validation remains in place.
Existing default cap remains 10. Receiver cap remains 10.

## Relationship to other features

- **0042-FEAT:** CLOSED. Preserve simplified-only runtime and agreed-parent
  protections. The existing `btrfs-native-push` unit names stay unchanged.
- **0039-DEF:** OPEN Step 11. Do not change the 05:30 qgroup maintenance time,
  disable its timer or repeat accepted cleanup/restores. Capture scheduled
  recurrence evidence on 11 November after this schedule change.

## Change-control steps

1. **Inventory/source baseline and isolated regression:** verify Git
   revision, clean working tree, expected schedule, no conflicting host/group
   overrides, and cap/protection/inventory tests. OPEN until evidence captured.
2. **Install central inventory and deploy Ansible timers:** use the guarded
   installer, run dry-run deployment previews, then one actual source/receiver
   playbook deployment. OPEN until accepted host logs.
3. **Host verification and rollback assurance:** prove both effective
   04:15 prune timers, unchanged other schedules and enabled states, guarded
   source cap, snapshot health and verified agreed parent. OPEN.
4. **Git/evidence reconciliation and formal closure:** source and inventory
   commit receipts, evidence in this feature, formal acceptance, move to
   `change-control/complete/`. OPEN.

No production host operations have been performed when this package is first
prepared. See `IMPLEMENTATION-STEPS.md` for commands and rollback guidance.
