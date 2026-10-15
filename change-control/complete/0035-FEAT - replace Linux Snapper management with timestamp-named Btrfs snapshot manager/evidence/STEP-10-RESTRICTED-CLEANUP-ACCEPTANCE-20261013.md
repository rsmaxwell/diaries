# 0035-FEAT Step 10 — Restricted cleanup and checkpoint-hold acceptance

**Status: CLOSED for the agreed restricted cleanup and live hold acceptance (13 October 2026).**

The `roles/snapshots/` role remains the permanent timestamp-named Btrfs snapshot manager. Its temporary hold feature was implemented and deployed **before** this restricted cleanup. No obsolete-code cleanup was performed in `roles/snapshots/`, and no removal of legacy numeric Snapper snapshots is claimed. `roles/local-backup/` is preserved.

## Verified execution evidence — 13 October 2026

### Source regression and syntax (`mango`)

- `verify-native-btrfs-push.py`: PASS — full/incremental planning, verified parent, reseed and receipt guards.
- `verify-native-btrfs-static.py`: PASS — source-initiated native Btrfs safety contract.
- `verify-replication-protection.py`: PASS — invalid/missing protection fails closed; push pin lifecycle wired.
- `verify-native-btrfs-mounts.py`: PASS — pinned filesystem/mount UUID checks.
- `ansible-playbook --syntax-check native-btrfs.yaml`: PASS; `remote-backup.yaml`: PASS (prior source validation).
- `verify-btrfs-snapshot-manager.py`: PASS; `verify-checkpoint-holds.py`: PASS after fixing a test-only root-ownership fixture; `snapshots.yaml` syntax PASS.

### Live deployment and host checks

- `ansible-playbook native-btrfs.yaml --ask-vault-pass`: `mars ok=11 changed=0 failed=0 unreachable=0`; `backup ok=11 changed=1 failed=0 unreachable=0` on the final helper-retirement run. Only reported change: remove `/usr/local/libexec/whole-backup-pull.py` on `backup`.
- `backup`: confirmed `/usr/local/bin/btrfs-native-pull` and `/usr/local/libexec/whole-backup-pull.py` absent; `/usr/local/bin/btrfs-native-push-receiver` executable; accepted receipt `20261013-180016Z.json` intact. Earlier inspection found no configured helper references in scanned systemd/cron/`/usr/local` paths and no running helper process. `rsync.service` was not removed.
- `mars`: `/usr/local/bin/btrfs-native-push` installed; post-cleanup preflight for `20261013-190026Z` selected accepted parent `20261013-180016Z`, `action=incremental`, `dry_run=true`, receiver `10.254.22.1:39263`.
- Source protection after cleanup: `CHECKPOINT-HELD: ['20261013-171228Z']`; `REPLICATION-PROTECTED: ['20261013-180016Z']`; pruning dry-run proposed zero deletions; `btrfs-snapshot-prune.timer` active.

### Pre-cleanup rollback checkpoint

- `mango` and `mars` machine-backup scripts exited `0`; mirrored Playbooks checked on `mars`.
- `mars` manager created complete `root`/`@data` timestamp set `20261013-171228Z`, with verified Playbooks and machine-backup files.
- Incremental push of this checkpoint accepted by `backup` (`btrfs-incremental`, source/received UUID `340674cc-d02c-244e-b7ec-e3ea5a6b151f`, readonly, both send/receive exit `0`); recipient file existence checked for Playbooks and `mars` backup.
- Independent `hold-add` with reason `0034/0035 pre-cleanup recovery checkpoint` retained timestamp `20261013-171228Z` after promotion of `20261013-180016Z` to replication parent.
- Scheduled 13 October 19:15:18 UTC pruning reported both `CHECKPOINT-HELD` and `REPLICATION-PROTECTED`, deleted one other complete timestamp set, and completed successfully.
- **Do not release the checkpoint hold during closeout**. This hold is enforced on `mars`; no new receiver-side hold/interlock is claimed for `backup`.

### Git evidence and scope qualification

- On `mango`, commit `5d3b2b3` (`0034-FEAT Step 10.P9`) was pushed to `origin/main` (`rsmaxwell/ansible-playbooks`); subsequent `git status` showed a clean working tree.
- The operator ran **`git add -A`**, so this commit includes **97 files / 8,968 insertions / 339 deletions**, including separate ongoing bootstrap, Diaries, local-backup and snapshot-manager work. It is **not a role-only cleanup commit**; no assertion is made that those unrelated changes have been independently accepted by the cleanup tests. The restricted Ansible deployment and host checks above remain the evidence of what actually changed on `mars`/`backup`.
- The final `native.yaml` supplied by the operator uses `when: btrfs_native_endpoint_role == 'receiver'` and `tags: [native-btrfs]` for both installed obsolete-helper removal tasks; its deployment evidence documents successful removal of the rsync helper. No additional redeployment is claimed solely for the final cosmetic condition/tag edit.

### Closure decision

**Restricted Step 10 cleanup/hold acceptance CLOSED.** Keep other 0035 objectives (e.g., host-specific Snapper retirement and any unapproved `backup` timers) separately gated; do not interpret this narrow sign-off as feature-wide closure.
