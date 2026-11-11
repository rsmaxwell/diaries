# 0047 — Source retirement decision (2026-11-11)

The 0045 acceptance kept the legacy operator entry points deliberately while
caller audits were reviewed. The four-host read-only inspection found zero
references; the Jenkins pod inspection checked 27 job configurations with zero
references. The audit did **not** cover dynamically loaded SCM Jenkinsfiles or
external systems. The user has now explicitly requested removal.

| Old | New / disposition |
|---|---|
| `roles/local-backup/` | Rename to `roles/backup-collection/` (no installation path changes) |
| `local-backup.yaml` / `scripts/local-backup.sh` | Delete; use `backup-collection.yaml` / `scripts/backup-collection.sh` |
| `remote-backup.yaml` / `scripts/remote-backup.sh` | Delete; use `snapshots.yaml --limit backup --tags snapshots` for the former generic snapshot route |
| `roles/remote-backup/` | Previously renamed to `roles/btrfs-replication/`; clean generated-bytecode-only remnant |
| `diaries-user-backup-cron.yaml` | Delete historical isolated scheduler correction; `backup-collection` still manages the cron |

Native Btrfs transport installation must continue through `btrfs-replication.yaml`
(`tasks_from: native.yaml`), not the default generic role task path. Both host
contexts of `snapshots.yaml` remain required. Generic `btrfs.yaml` and the
`btrfs` role serve another purpose and are **not** legacy cleanup candidates.

Historical source maps in closed 0045 and the Playbooks `verification/` archive
remain historical records, even if their quoted paths use former names. There
is no intent to retest the 0034 or 0035 destructive integration fixtures.

The latest source snapshot used for packaging is
`playbook-sources-20261111-111917.zip`, overlaid with the accepted 0045 Step 2
refactor, launcher fix and README consolidation. The operator's subsequent
`mango` log confirmed Playbooks `main` at `9a21c69`; preflight must verify
that baseline on the real checkout before applying or committing the package.
