# 0047-FEAT — Implementation and acceptance steps

## Step 1 — Source interface replacement (CLOSED — 11 November 2026)

Source checkout on `mango` was verified against accepted Playbooks `9a21c69`.
The guarded cleanup removed `local-backup.yaml`, `remote-backup.yaml`,
`diaries-user-backup-cron.yaml`, the two `scripts/*-backup.sh` legacy
launchers, and the old tracked `roles/local-backup/` tree after preparing the
replacement `roles/backup-collection/`. No installed backup or snapshot data
was removed.

The consolidated collection, Diaries pull, snapshot manager/launcher,
replication, protection, retention and three Ansible syntax checks passed;
replication/protection unit tests passed 30/30. Source commit `b04de9e`
was published. Seven executable bits lost in the ZIP role move were
restored in a mode-only commit `833da94` (seven files, zero content changes).
The final source-mode contract, `rsync` source-mode preservation tests and
syntax check passed; source commit `dca638c00cc3b0fe2f2a46ef01c060cb1a1f6296`
was published and Playbooks `main` matched `origin/main`.

**Accepted evidence:** `evidence/Step 1/source-check-*.txt`, terminal
publication readbacks, `reports/SOURCE-RETIREMENT-DECISION-20261111.md` and
`reports/STEP1-FINAL-ACCEPTANCE-20261111.md`. Historical 0045 audit
limitations concerning SCM-loaded Jenkinsfiles and external callers remain.

## Step 2 — Controlled apply and static installed-state equivalence (CLOSED — 11 November 2026)

Initial application under `833da94` returned `changed=2` for collection on
`mars`, both changes limited to source-filter rsync tasks, with zero host
failures. This **did not** satisfy the initial zero-change gate and is
retained as failed first-attempt evidence.

The correction rejected blanket rsync `--chmod` policies. The source
checkout at `dca638c` has 14 verified historical modes and content hashes
(nine regular filter files at `0664`, five directories at `0750`). Native
rsync archive mode and `--omit-dir-times` preserve file-specific modes.

First corrective apply on `mars` changed only the two expected copy tasks;
afterward, both endpoint static installed-state fingerprints matched the
accepted 0045 schema-v2 baseline. The full second application produced:

| Playbook | Host | Changed | Failed | Unreachable |
|---|---|---:|---:|---:|
| `backup-collection.yaml` | `mars` | 0 | 0 | 0 |
| `btrfs-replication.yaml` | `mars` | 0 | 0 | 0 |
| `btrfs-replication.yaml` | `backup` | 0 | 0 | 0 |

The five `mars` systemd ExecStart differences were historical execution
metadata only, with unchanged installed units and loaded properties. Docker
signing-key SHA-256 was unchanged; read-only Btrfs health checks passed.
No restoration, manual replication, pruning or backup dataset modification
was required.

**Accepted evidence:** `evidence/Step 2/metadata-correction-20261111-160642Z/`,
`evidence/Step 2/deployment-20261111-160900Z/`, source-mode restoration
terminal log in `evidence/Step 2/` and
`reports/STEP2-FINAL-ACCEPTANCE-20261111.md`.

## Step 3 — Formal acceptance and closure (ACCEPTED — effective on final publication)

The Playbooks source is published at `dca638c` and its installed configuration
is equivalent to accepted 0045. Retired interfaces are not reintroduced;
current entry points remain `backup-collection.yaml`, `snapshots.yaml` and
`btrfs-replication.yaml`. The retained per-path source-mode restoration
contract is intentionally deferred for reassessment in 0048-FEAT after
0046 and 0047 close. Keep the accepted 0047 tools and evidence as historical
records even if 0048 later retires active restoration tooling.

**Formal closure gate:** apply this closure package in the authoritative
Windows Diaries repository; verify evidence and Playbooks published revision;
move the entire feature from `in-progress` to `complete`; stage only 0047
paths; commit and push; verify the destination exists, source absent and Git
HEAD equals `origin/main`. If this final action fails, formal closure is
not yet effective. See `reports/STEP3-FINAL-CLOSURE-20261111.md`.
