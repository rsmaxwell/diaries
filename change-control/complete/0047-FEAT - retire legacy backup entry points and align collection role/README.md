# 0047-FEAT — Retire legacy backup entry points and align the collection role

**State:** ACCEPTED — formal closure effective only after feature move, commit and push  
**Opened:** 2026-11-11  
**Owner:** Diaries parent change control; permanent implementation in Playbooks Git.

## Objective

Retire obsolete operator-facing names left after 0045 and make `backup-collection`
the actual `mars` collection role, without changing installed backup scripts,
permissions, credentials, snapshot operations or scheduled timers. Keep the
native sender/receiver and snapshot-specific entry points independently usable.

## Scope / exclusions

- Rename `roles/local-backup/` to `roles/backup-collection/` with its complete
  defaults, templates, tasks, metadata, handlers, files and regression tests.
- Remove `local-backup.yaml`, `remote-backup.yaml`, their corresponding
  `scripts/*.sh` launchers and obsolete one-off `diaries-user-backup-cron.yaml`.
- Remove the obsolete `roles/remote-backup` cache-only directory if it contains
  only generated Python bytecode; never delete unexpected files.
- Update `backup-collection.yaml`, `snapshots.yaml`, current role documentation,
  host-context guards and source tests. Historical `verification/` evidence and
  completed 0045 records remain unchanged.
- Retain `snapshots.yaml`, `scripts/snapshots.sh`, `btrfs-replication.yaml`,
  `roles/snapshots/`, `roles/btrfs-replication/` and generic `btrfs.yaml`/role.
- Retain the inventory groups `local_backup` and `remote_backup`, variables
  `local_backup_*`, existing Cron/systemd schedules, all installed scripts and
  `/root/scripts/backup/remote/` on `mars`.

## Evidence and acceptance

1. **Source rename + caller reconciliation**: 0045 inspected four hosts and 27
   live Jenkins job configuration files; no references to old operators were
   found. Jenkinsfiles loaded from SCM and external schedulers were outside the
   audit, documented as residual risk. This removal is now explicitly requested.
2. **Source regression and Ansible parse**: preserve source roles, dependency
   resolution and per-host snapshot protection; run the permanent source tests.
3. **Installed-state equivalence**: apply both supported playbooks once, require
   zero Ansible changes, compare both endpoint manifests with the accepted
   0045 Step 1 v2 static baseline using the corrected 0045 comparator; check
   Docker signing key identity separately.
4. **Closure**: record actual results and Git commits in this directory, then
   close and move the feature to `change-control/complete/` only after acceptance.

**Rollback:** Restore the Playbooks prior revision `9a21c69` (after confirming
current repository state) and reapply the pre-rename playbooks if needed. Do not
modify backup datasets, delete snapshots or revert 0045 acceptance evidence.

## Final acceptance — 11 November 2026

**Steps 1 and 2 technically ACCEPTED; Step 3 closure conditional on final Diaries
Git publication.** The Playbooks source at
`dca638c00cc3b0fe2f2a46ef01c060cb1a1f6296` is published on `main`.
Legacy entry points and launchers have been retired, `roles/local-backup/`
was replaced by `roles/backup-collection/`, and the supported
`snapshots.yaml` / `btrfs-replication.yaml` entry points remain.

The initial 0047 application exposed source-metadata drift caused by Git/ZIP
not preserving group-write or directory permissions. At `833da94` the first
collection apply reported two changed copy tasks; **that was not accepted as
an idempotent deployment**. The revised source-mode-preserving rsync approach
at `dca638c` has no `--chmod` override. On `mango` the 14 historical source
paths were restored (nine filter files `0664`, five directories `0750`),
with content-hash checks, and the corrected first apply changed only the two
expected metadata-copy tasks. The subsequent full apply returned
`changed=0, failed=0, unreachable=0` on all targeted plays.

The final static installed-state manifests on `mars` and `backup` match the
accepted 0045 baseline. Five `mars` systemd ExecStart digest differences are
execution-history only, not installed unit or loaded-property differences.
The Docker signing key was unchanged; read-only Btrfs health checks passed.
See `reports/STEP2-FINAL-ACCEPTANCE-20261111.md` and
`reports/STEP3-FINAL-CLOSURE-20261111.md`.

**Follow-up:** 0048-FEAT will determine whether all 14 exact source modes
are operationally required after a clean clone and may retire the restoration
script and `source-modes.json` contract if unnecessary. Keep 0048 blocked until
0046 and 0047 are formally closed. Do not remove the accepted 0047 evidence.

**Residual caller scope:** 0045 inspected four hosts and 27 Jenkins job
configurations without finding legacy callers. SCM-loaded Jenkinsfiles and
unmanaged external systems were not exhaustively checked. This residual
limitation was accepted when retirement was explicitly requested.

**Closure condition:** Move this feature, including its evidence, to
`change-control/complete/`, commit and push the Diaries parent `main` branch,
confirm the feature path is clean in Git, and record the resulting commit SHA
in the actual terminal output. A failed move/push leaves formal closure
incomplete; no new production deployment is required.
