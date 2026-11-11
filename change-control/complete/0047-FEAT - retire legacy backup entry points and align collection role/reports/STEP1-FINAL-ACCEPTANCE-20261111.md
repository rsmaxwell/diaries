# 0047-FEAT — Step 1 source retirement acceptance

**Decision:** ACCEPTED (11 November 2026).

- Accepted pre-0047 Playbooks source `9a21c69` on `mango`.
- Applied guarded source cleanup, retiring `local-backup.yaml`,
  `remote-backup.yaml`, `diaries-user-backup-cron.yaml` and old launchers;
  renamed `roles/local-backup/` to `roles/backup-collection/`.
- Completed source entrypoint, cron, Diaries pull, fixed receiver, snapshot
  manager/launcher, native replication and retention checks. Replication and
  protection unit tests: 25 + 5 passed. Three Ansible syntax checks passed.
- Published source retirement as `b04de9e`.
- Preserved seven previously executable source file modes in `833da94`
  (no content changes).
- Verified source-mode preservation/no rsync `--chmod`, 14 path modes and
  source hashes; rsync correctly propagated original modes on first run and
  was idempotent on the second. Ansible collection syntax check passed.
- Published source correction as
  `dca638c00cc3b0fe2f2a46ef01c060cb1a1f6296`; branch and origin
  matched, with a clean Playbooks working tree in the reported check.

**Caller-scope limitation:** The accepted 0045 read-only host and Jenkins
caller audit (four hosts, 27 Jenkins job definitions) found no references to
old operators within inspected scope. Dynamically loaded Jenkinsfiles and
external systems were not exhaustively audited. Retirement was expressly
approved with this understood limitation.

**Evidence:** `evidence/Step 1/source-check-*.txt` and user-supplied
publication terminal logs. This acceptance does not assert that all possible
external invocations have been tested.
