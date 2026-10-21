# 0038-FEAT — Production promotion manifest and close-out

**Status: CLOSED — 21 October 2026.** Production promotion was performed through the existing Playbooks `remote-backup.yaml` configuration, not the Diaries change-control tree.

## Provenance

- Playbooks `main`: `fc8233da3464aa114d69a2e34bd8990f96daf281` (clean, synchronized with origin/main, `note(20261021-074040).txt`). The earlier SHA `908509ec57e06f972b4412fae8f98b7a4f4edc1f` was superseded by a commit-message amendment.
- Diaries `main` pre-archive documentation baseline: `e69e08b2ff100b7d2afcf8458e9cb9204bc6be5a` (clean, synchronized, `note(20261021-073700).txt`). The eventual archival commit will receive a new SHA, to be recorded after the move.

## Approved installation scope

| Managed destination on `backup` | Ansible source / role | Purpose | Rollback |
|---|---|---|---|
| `/usr/local/sbin/btrfs-snapshot-manager` | Playbooks `roles/snapshots/files/btrfs-snapshot-manager.py` | Install manager with corrected receiver-only config support | Preserved pre-change executable |
| `/usr/local/sbin/diaries-backup-history` | Playbooks `roles/snapshots/files/diaries-backup-history.py` | Maintain history utility | Preserved pre-change executable |
| `/usr/local/lib/diaries-backup/complete-dataset-manifest.py` | Playbooks `roles/diaries/files/sync/scripts/complete-dataset-manifest.py` | Schema-2 verifier | Preserved pre-change executable |
| `/etc/btrfs-snapshot-manager.json` | Playbooks `roles/snapshots/templates/btrfs-snapshot-manager.json.j2` | Disable obsolete writer lock and verification on receiver; retain `/@snapshots` local root | Preserved pre-change JSON |
| `btrfs-legacy-prune.service` and `.timer` | Playbooks `roles/snapshots/templates/` | Install dormant units; activation disabled | Removal / Ansible-managed revision |

The four original files remain under root-owned `/root/remote-backup-pre-reconcile/` on `backup` as the accepted retained emergency rollback. Their SHA-256 hashes are documented in Step 2 evidence. No changes to `/@data/mars-received`, replication receipts, backup schedules or retention were approved.

## Test and deployment record

- Approved check/diff: `note(20261020-203011).txt`, 5 proposed changes; `backup` only.
- Real deployment: `note(20261020-203837).txt`, `ok=27 changed=5 failed=0`.
- Post-install manager/configuration, timers and received Btrfs IDs: `note(20261020-203934).txt`.
- Installed program checks and receipt inventory: `note(20261021-071157).txt`.
- Received new incremental read-only snapshot `20261021-030006Z` and matching receipt: `note(20261021-071328).txt`.
- Negative checks and real-run idempotency `changed=0`: `note(20261021-072024).txt`, `note(20261021-072206).txt`, `note(20261021-072739).txt`.

**Known exclusion:** qgroup status returns `unavailable;reason=unexpected_output` (non-blocking parser diagnostic); no fix was deployed in this feature.
