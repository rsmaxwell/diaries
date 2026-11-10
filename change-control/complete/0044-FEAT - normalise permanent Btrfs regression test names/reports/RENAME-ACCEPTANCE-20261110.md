# 0044-FEAT — Rename and regression acceptance — 10 November 2026

**Acceptance status:** PASS for source renames and all retained regression tests; Playbooks Git commit and formal closure pending.

## Verified source isolation

- Playbooks `main` at `6d7f397048b8ed47c94f973a98096fc6e806e4e8` before rename.
- Five Python scripts renamed through `git mv` without modifying their contents (`0` line changes each).
- Updated only the executable filename references in `roles/btrfs-replication/tests/README-0040-SIMPLIFIED.md` and `roles/snapshots/tests/README-0040-SIMPLIFIED-RECEIVER-RETENTION.md`.
- Git reported seven staged changes, six additions and six deletions confined to the two README files, and no staged whitespace errors.
- The rename preflight reported no file changes; applying the tool staged, but did not commit, the source changes.

## Accepted tests

| Test | Result |
|---|---|
| `verify-simplified-replication.py` | PASS, 25 cases |
| `verify-simplified-protection.py` | PASS, 4 cases |
| `verify-simplified-cutover-readiness.py` | PASS, 5 cases |
| `verify-shared-retention.py` | PASS |
| `verify-legacy-retirement-source.py` | PASS |
| `git diff --cached --check` | PASS |

No deployment or changes to inventory, replication, snapshots, or host services were required or performed.

## Evidence

- `evidence/Step 1/transfer-20261110-143831.txt` — unmodified Windows transfer log.
- `evidence/Step 2/rename-and-regressions-20261110-143920.txt` — unmodified `mango` rename and regression log.

## Remaining acceptance

Commit the seven staged files on `mango` as one isolated 0044 change. Capture its commit SHA and clean-working-tree evidence in `evidence/Step 3/`. Once the commit is verified, update the feature state to CLOSED and move its directory from `in-progress` to `complete` in the authoritative Windows Diaries repository.
