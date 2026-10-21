# Step 05 — Controlled reconciliation acceptance

**Decision: CLOSED — 20 October 2026.**

- `note(20261020-203555).txt` — on `backup`: four rollback copies SHA-256 equal previous originals; 14 received Btrfs subvolumes; create/prune timers disabled/inactive, legacy-prune timer not yet installed.
- `note(20261020-203837).txt` — on `mango`: explicit `./scripts/remote-backup.sh --apply` succeeded; `backup: ok=27 changed=5 unreachable=0 failed=0 skipped=8`; real manager preflight succeeded and obsolete Diaries verification disabled. Five approved changes were installation of manager, backup-history, schema-2 manifest verifier, corrected JSON, and legacy-prune service/timer unit files (single loop task).
- `note(20261020-203934).txt` — on `backup`: manager status successful; old `diaries-mars-replica` error absent; writer lock empty; verification required false; three local timers disabled/inactive; 14 preexisting received Btrfs subvolumes with identical IDs 55593 through 55792, newest `20261020-030026Z`; replication-state directory still present (`richard:richard`, mode 0700).
- `note(20261020-205235).txt` — on `mango`: default Ansible check/diff after deployment, `backup: ok=22 changed=0 unreachable=0 failed=0 skipped=12`; no remaining configuration drift predicted.

**Exceptions:** optional status diagnostic `qgroups_status=unavailable;reason=unexpected_output` (no fatal status error). Do not claim receiver receipt *content* verified, no-full-transfer regression, or a new restore. Those have separate gates. Retain root-owned rollback copies until feature closure.
