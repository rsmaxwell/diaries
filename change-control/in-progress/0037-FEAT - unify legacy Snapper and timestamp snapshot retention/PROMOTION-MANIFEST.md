# Production promotion manifest — 0037-FEAT

**Step 13 formal reconciliation — CLOSED (2026-10-20); outstanding source commit and retained-helper disposition carried to Step 14.** Permanent implementation is maintained in the **Playbooks** repository, not copied out of the feature workspace at closure. Paths listed below are present in the latest supplied `playbook-sources-20261020-165232.zip`. SHA-256 hashes are of those source-bundle entries, not independent readings of deployed hosts. Git commit revisions and on-host cleanup remain to be recorded before final Step 13 closure.

## Permanent source and regression inventory

| Playbooks relative path | Source SHA-256 |
| --- | --- |
| `roles/snapshots/files/btrfs-snapshot-manager.py` | `dc7dc489a7f8a0683224eaf426a1d70f34c1cf794744ddf5e4860bab4e8f1e4c` |
| `roles/snapshots/tasks/main.yaml` | `f72142f426540a683d6a073b7e7d33403c217a63c8d9cff18b31c8d9cc97a5ae` |
| `roles/snapshots/tasks/retire-legacy-snapper-timers.yaml` | `24251642575bebf5df1c13504f5008c8b0e0930bc866dbe4241a41a2f21a060b` |
| `roles/snapshots/defaults/main.yaml` | `f95c45f67bd60e3d61ca4c1dd4bfbcf41f97091eacc6a5173407363af6faa5c0` |
| `roles/snapshots/templates/btrfs-legacy-prune.service.j2` | `23230191a3f9e139a48073d969148949ebc73846e44a733266d2fe5751b623ca` |
| `roles/snapshots/templates/btrfs-legacy-prune.timer.j2` | `c408c0bd66c1ab67d5bb7ef04848442755cd2087162fdb16342fd36e5d654f36` |
| `roles/snapshots/templates/btrfs-snapshot-prune.service.j2` | `aff547c857a47c68aeb32adeff6c7b8cd1b5dab86421e9a81306f51107e67710` |
| `roles/snapshots/templates/btrfs-snapshot-prune.timer.j2` | `3a2ad313b26ac6a57b903d4f7d56cf030f9809bdc00f371f782cd2766c73f515` |
| `roles/local-backup/tasks/main.yaml` | `7b63515d522b9fd2f2be1cf4a14ed417f5c94ecfd02a08c65b32d2536a2979f2` |
| `roles/snapshots/tests/verify-local-backup-legacy-unit-deploy.py` | `ccdf7d911dbf9dade0b2b57b4469bf2204c6a81d12ab50b34d2038858464a88c` |
| `roles/snapshots/tests/verify-legacy-prune-preview.py` | `9454c02cfc0ab23a80d95727e6d1655b8d164b09c25a85c147a3a07388571ff6` |
| `roles/snapshots/tests/verify-unattended-legacy-prune.py` | `093e4ac68fc4f94cc38b296cf7ec4069dff29de2f4acec741e979cd8b8b89151` |
| `roles/snapshots/tests/verify-qgroup-status.py` | `8e481da31e05e315c3ce381fec83aac376c0f8a0ac05254de86d88f38dfa69d1` |
| `roles/snapshots/tests/verify-btrfs-snapshot-manager.py` | `b56d0ae73edff408053ff34d910e070f3473e16cd258e6e4451b828843a9dcf5` |

## Promotion decision

- `roles/snapshots/files/btrfs-snapshot-manager.py`: native timestamp snapshot lifecycle, combined legacy Snapper planning/guarded pruning, read-only qgroup status. Permanent production manager.
- `roles/snapshots/tasks/main.yaml`, `defaults/main.yaml`, `templates/btrfs-legacy-prune.*.j2`: install and manage the separate daily guarded legacy prune timer; default disabled; host opt-in required. Existing native hourly timer preserved.
- `roles/local-backup/tasks/main.yaml`: permanent `local-backup.yaml` deployment entry point, including focused `--tags legacy-prune-units` operation.
- `roles/snapshots/tests/verify-*.py`: permanent executable/source regressions used in Step 12 acceptance.
- Snapper timer retirement tasks remain shared permanent role logic; no feature-numbered permanent deployment playbook is required.
- Host-specific opt-in is configured in `/etc/ansible/host_vars/mars/backup.yaml` (inventory outside this source bundle). **Operator-reported** Boolean values: `btrfs_snapshot_activation_enabled: true`, `btrfs_snapshot_retire_legacy_snapper_timers: true`, `btrfs_snapshot_snapper_handover_enabled: false`, `btrfs_snapshot_unattended_legacy_prune_enabled: true`, `btrfs_snapshot_unattended_legacy_prune_max_delete: 1`. Do not claim inventory file contents independently audited from these ZIPs.

## Deployment evidence

Step 12 acceptance records a successful permanent tagged deployment, repeat run `changed=0`, daily legacy timer at 08:20 UTC, hourly native pruning at `*:15`, and successful systemd deletions of `@data` IDs `19629` and `19677`. See `evidence/Step 12/STEP12-SCHEDULER-FORMAL-CLOSURE.md`.

## Source/workspace disposition

- `tools/`, `tests/`, `reports/` and `evidence/` within the feature are **not** runtime dependencies. Retain feature-local historical scripts, test drivers and logs for audit; do not deploy or delete them merely because implementation has been promoted.
- `tools/btrfs-snapshot-manager.py` is a feature-local historical/staging copy: **not** the authoritative runtime source. Do not overwrite Playbooks with it. Retain or archive deliberately at Step 14; never deploy it.
- No production changes to the Diaries client, responder or web images were required.

## Pending Step 13 acceptance fields

- [ ] Record `git rev-parse HEAD` and `git status --short` for Playbooks and Diaries once files are applied.
- [ ] Review untracked/generated/temporary files and explicitly approve any deletions; none is authorised here.
- [ ] Audit host-side temporary 0037 workspaces on `mango`, `mars`, `backup` without removing them automatically.
- [ ] Inspect source evidence for credentials, secrets or unnecessarily large material before committing.
- [ ] Demonstrate full untagged `local-backup.yaml --limit mars --check --diff` deployment has no unexpected drift; an unrelated manifest-verifier change appeared during earlier tagged `snapshots` dry run and is **not resolved** by focused Step 12 acceptance. Do not run untagged production deployment until reviewed.
- [ ] Record full (not only focused-tag) deployability outcome and classify any deferred findings for Step 14.

## Step 13 closure addendum — 2026-10-20

The previous *Pending Step 13 acceptance fields* checklist is preserved as the initial plan. Production full-playbook drift was reconciled, newer publisher/verifier utilities installed and hash-verified, and a real full `./local-backup.sh` completed with `ok=64 changed=0 failed=0`. The normal-user script directory is `0750`. Natural retention timer/calendar execution and final git commit IDs were not re-proven here. `mars` contains three root-owned legacy pull helpers; no removal authorised. See `evidence/Step 13/STEP13-FORMAL-CLOSURE.md`.

### Source-bundle hash inventory for Step 14 reconciliation

These hashes are from `playbook-sources-20261020-181155.zip`, not the live host or Git HEAD. They supplement, and may supersede older values in the table above:

| Permanent file | SHA-256 (uploaded source bundle) |
| --- | --- |
| `roles/local-backup/tasks/install_user_scripts.yaml` | `6317e61c383f3ef833125eb25cc0dafaf001a1ef8fcd8ca0114a3417d910d423` |
| `roles/local-backup/tasks/install_machine_scripts.yaml` | `449449e0d7cd9dc1000591118f5c41c24f449676e88400f07f72ec49afff0cd1` |
| `roles/diaries/tests/verify-production-complete-dataset-tooling.py` | `31a224c23f35c751fba223cdb2aacf25bf114a6e9dd7f58ffdc75eab9b4e44d9` |
| `roles/diaries/files/sync/scripts/complete-dataset-manifest.py` | `d9490f706f427b11a5b5758b9a818e3218aa0624e5e659ea6187b2518fdfbc73` |
| `roles/diaries/files/sync/scripts/complete-dataset-publisher.py` | `ae5431fdc56eba7fea4411103d869f6f913e87f91c0c4500a4cc5185e89b64ea` |
| `roles/snapshots/files/btrfs-snapshot-manager.py` | `dc7dc489a7f8a0683224eaf426a1d70f34c1cf794744ddf5e4860bab4e8f1e4c` |
| `roles/snapshots/tasks/main.yaml` | `f72142f426540a683d6a073b7e7d33403c217a63c8d9cff18b31c8d9cc97a5ae` |
| `roles/local-backup/README.md` | `2da9530ea0be2b084c23b46d3651d3206f27de6744857fd6a51c6d18e86608b2` |
| `roles/snapshots/README.md` | `caea2089de83c46e44bb96465f2075db3a94eae2ef528be054786ac60180e224` |
