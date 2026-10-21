# Step 4 — Final rehearsal: acceptance record

**Status: CLOSED. Date: 20 October 2026.**

## Provenance

- Host/terminal: `mango` SSH; repository: `/home/richard/playbooks`.
- Operator transcript: `note(20261020-203011).txt` (reviewed; not copied or fabricated).
- Commands: `git status --short`, `git diff --check`, `ansible-playbook remote-backup.yaml --list-hosts --vault-password-file ~/.vault_pass.txt`, syntax check and `./scripts/remote-backup.sh` default check mode.
- Git status: five locally modified files — `local-backup.yaml`, `remote-backup.yaml`, `scripts/diaries.sh`, `scripts/local-backup.sh`, `scripts/remote-backup.sh`. Whitespace check passed. Latest previously recorded Playbooks committed HEAD: `6a80d4f4160574b243a3d1e73e2f8b0fac767846`; do not equate this with uncommitted working tree.

## Observations and acceptance

- Target only `backup`; valid syntax; no inventory warnings.
- Check-mode recap: `ok=22 changed=5 unreachable=0 failed=0 skipped=13`.
- Planned replacements: `/usr/local/sbin/btrfs-snapshot-manager`, `/usr/local/sbin/diaries-backup-history`, `/usr/local/lib/diaries-backup/complete-dataset-manifest.py`, `/etc/btrfs-snapshot-manager.json`.
- Planned addition: `btrfs-legacy-prune.service` and `.timer` unit files in one changed installation task; no timer activation.
- Configuration: remove stale `diaries-mars-replica` writer-lock/verification paths, set verification not required; root remains `/@snapshots`, protection and checkpoint holds disabled for local `backup` manager.
- No planned writes to `/@data/mars-received/@data` or `/@data/mars-received/.replication-state`. Snapshot creation, prune, and legacy-prune timer activation tasks skipped. Retired Snapper timers already disabled.
- Four verified root-owned rollback copies are available on `backup` from Step 2.

**Decision:** Accept only the scoped five-change deployment prediction, and advance to Step 5. No authorization to prune/delete/reseed received subvolumes, change retention or schedules, or run a fresh transfer/restore.

**Limitation:** `--check --diff` does not prove actual post-deployment results or immutable receiver state. Steps 5–6 must verify these.
