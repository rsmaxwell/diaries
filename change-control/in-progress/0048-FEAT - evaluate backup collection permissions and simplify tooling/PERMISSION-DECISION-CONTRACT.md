# 0048 — Permission requirements, rsync behaviour and retirement decision

## Purpose

0047 preserved the **historic installed state**, not proof that every permission bit was necessary. 0048 tests that distinction only after 0046 and 0047 closure. Each source path must have a documented access requirement and an independently verified proposed mode, rather than an inferred "safe" global chmod policy.

## Grounded starting point (0047 planning/source-mode report)

| Source collection | Historical destination | Historical source-mode contract | Required question |
|---|---|---|---|
| `files/backup/home/{includes,excludes-1,excludes-2}` | normal-user `~/scripts/backup/home/` | three regular files `0664` | Does any required writer need group write? Which reader actually consumes these files? |
| `files/backup-machine/home/{includes,excludes-1,excludes-2}` | `/root/scripts/backup/home/` | three regular files `0664` | Is group write needed or safe in root-owned backup control files? |
| `files/backup-machine/remote/{includes,excludes-1,excludes-2}` | `/root/scripts/backup/remote/` | three regular files `0664` | Does disabled/rollback remote transport require special access? |
| `files/backup`, `files/backup/home`, `files/backup-machine`, `files/backup-machine/home`, `files/backup-machine/remote` | corresponding deployed directories | five directories `0750` | Are group traverse/other restrictions required, and does the role reapply them consistently? |

The 0047 `source-modes.json` records exact paths and SHA-256 contents for the nine files; re-read it from the actual **post-closure** Playbooks revision before relying on this list. These 14 paths are the minimum named audit set, **not** permission requirements proved in advance. Audit adjacent executable source files, copied scripts, and templates separately when the consumer analysis shows they matter.

## Fundamental constraints

- Git records ordinary file executability (e.g. `100644` vs `100755`), but does **not** record a group-write bit or Git directory modes. A fresh checkout's results can vary with filesystem, umask and Git settings; capture actual modes, do not assume values.
- For `ansible.posix.synchronize` in archive mode, rsync preserves source modes. Keep `--omit-dir-times` as appropriate; do not use `--chmod` or `--no-perms` to mask a source-permission defect.
- Existing `install_user_scripts.yaml` explicitly creates `/home/.../scripts/backup/` and child directories with `mode: "0750"`, then synchronizes `backup/`. If a clean checkout has `0755` directories, the subsequent sync may override those modes and the preceding file task may reset them on every subsequent run. **Testing the complete task sequence for two runs is essential.**
- The machine-script directory-creation tasks and separately templated `backup.sh` files have different ownership/mode contracts; a source-mode decision for synced filters must not silently alter templated scripts or `/root` access controls.
- Never infer secrecy just from a path name or assume `/root` ancestry compensates for every access-policy regression; check the actual effective users and ACLs.
- Preserve original installed byte content, scheduled behaviour, lock coordination, Btrfs retention and replication configuration unless a specifically accepted change is justified and evidenced.

## Required decision record for every affected source/deployed path

| Field | Evidence to capture |
|---|---|
| Source and destination | Repo-relative source path; absolute installed path and host |
| Before and clean-clone modes | `stat` mode, Git index mode where applicable, ownership/group, ACLs, umask/environment |
| Who uses it | Effective process UID/GID; necessary read/write/traverse/execute operations |
| Threat / exposure analysis | Whether adding `other` access or retaining group write broadens access |
| Proposed policy | Minimal justified mode and whether a plain Git clone can reproduce it |
| Idempotence | Behaviour of both Ansible directory task and rsync across two consecutive runs |
| Outcome | ACCEPT, RETAIN SPECIAL HANDLING, or BLOCKED with explanation and rollback |

## Retirement criteria

Retire active restoration tooling **only when all** the following are true:

1. A fresh clone at the accepted post-0046/post-0047 source revision works without source metadata restoration; source mode remains the authority for rsync-copied entries.
2. Required readers/writers/executors continue to work, and no unintended or unreviewed security/permission broadening is introduced.
3. Two consecutive applications converge without repeated changes, including possible `0750` versus `0755` conflicts.
4. Installed results match the accepted baseline except explicitly approved permission changes; content hashes, ownership, ACLs, schedule and operational safety remain accepted.
5. Active Playbooks docs, checks and source no longer require `source-modes.json` or the one-off restoration command; surviving tests still guard essential permission semantics.
6. The rollback and formal acceptance evidence are recorded, with the 0047 historical tools and evidence left untouched in `change-control/complete/`.

If any condition fails, **do not retire** the special mechanism. Prefer a minimal scoped alternative with explicit rationale over insecure defaults, a blanket `--chmod`, silent source changes or a tool that must be run manually without fail-closed verification.

## Rollback principle

The implementation stage must record the **actual** pre-change Playbooks commit and installed-mode evidence, not a planning-time SHA. A rollback should restore that revision and re-establish the accepted permission state without deleting source datasets or snapshots. Demonstrate enough to establish rollback viability; do not require a full restore or replication merely for this permissions exercise.
