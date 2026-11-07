# 0040-FEAT — Retire superseded Playbooks verification scripts

This is the **feature-local** cleanup tool. It changes only historical test and
experiment files in `/home/richard/playbooks/roles/btrfs-replication/tests/`.
Archive bytes and manifests belong in the Diaries parent repository under
`0040-FEAT/tests/retired-step12-3/`, never permanently in Playbooks or `/home/richard`.
The authoritative Diaries working copy is on Windows; explicitly synchronise
the feature tool to `/home/richard/diaries` on `mango` before executing it.

## Scope and safeguards

- Retire obsolete `verify-0040-agreed-parent-*` tests and superseded Step 12.3
  staged/transaction/scope/receipt-promotion tests, plus their historical test
  guides. This includes tracked files, untracked files and working-tree
  modifications, **after** archiving their exact bytes.
- Preserve `verify-0040-simplified-replication.py`,
  `verify-0040-simplified-protection.py`, and the active
  `verify-0040-step12-3-shared-retention.py`, plus selected older safety guards,
  Step 3 tests, general native-Btrfs tests and all snapshot-manager tests.
- Check the actual Playbooks branch and revision. Refuse staged changes to a
  candidate, symlinks, conflicting archival bytes or executable references
  from files that would remain active. Never delete first and archive later.
- `--plan` is read-only. `--apply --expect-count N` copies every selected file
  into `tests/retired-step12-3/playbooks/roles/btrfs-replication/tests/`,
  verifies SHA-256, writes the manifest, then unlinks only those source files.
  It refuses a changed candidate count. It does not run Ansible or touch Btrfs.
- The 7 November 11:33 uploaded Playbooks bundle had **146 archive candidates**:
  138 Python tests and eight historical guides, leaving 46 Python tests in the
  role. The **live** `mango` plan is authoritative if different.

## Procedure on `mango` — read-only plan

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage'
TOOL="$FEATURE/tools/retire-obsolete-playbooks-step12-tests.py"
LOGDIR="$FEATURE/evidence/Step 12/raw-logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/step12-test-retirement-plan-$(date -u +%Y%m%d-%H%M%S).txt"
python3 "$TOOL" --playbooks /home/richard/playbooks --plan > "$LOG" 2>&1
rc=$?
head -8 "$LOG"
tail -10 "$LOG"
echo "Plan exit status: $rc; evidence: $LOG"
```

Review the candidate count, names, Playbooks Git status and any refusal.
If the live plan matches the reviewed bundle (**146 candidates**), execute the
bounded archive-and-retire operation. If the count or files differ, inspect
before applying and use that reviewed count rather than assuming 146.

## Archive + retire, then verify retained suites — `mango`

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage'
TOOL="$FEATURE/tools/retire-obsolete-playbooks-step12-tests.py"
LOGDIR="$FEATURE/evidence/Step 12/raw-logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/step12-test-retirement-apply-$(date -u +%Y%m%d-%H%M%S).txt"
(
  set -euo pipefail
  echo '=== Archive historical scripts from the actual Playbooks checkout ==='
  python3 "$TOOL" --playbooks /home/richard/playbooks --apply --expect-count 146
  cd /home/richard/playbooks
  echo '=== Review Git removals (not committed) ==='
  git status --short
  git diff --check
  echo '=== Validate retained simplified replication regressions ==='
  sudo -n env PYTHONDONTWRITEBYTECODE=1 python3 roles/btrfs-replication/tests/verify-0040-simplified-replication.py
  sudo -n env PYTHONDONTWRITEBYTECODE=1 python3 roles/btrfs-replication/tests/verify-0040-simplified-protection.py
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-shared-retention.py
  python3 roles/snapshots/tests/verify-0040-simplified-receiver-retention.py
  echo 'PASS: archived test retirement and retained suite'
) > "$LOG" 2>&1
rc=$?
tail -75 "$LOG"
if [ "$rc" -eq 0 ]; then echo 'PASS: test retirement'; else echo "FAIL: test retirement (exit $rc)"; fi
echo "Evidence: $LOG"
```

**Do not repeat `--apply --expect-count 146` after success.** A rerun will
see zero candidates; use `--plan` for status. Do not run if the reviewed count
is different. Even if later suite execution fails, the archived copies will
remain; do not automatically restore/repeat everything. Fix only the failed
check. Uncommitted tracked removals will show as `D` in Playbooks Git status;
these are intended but not yet accepted as a repository commit.

## Evidence reconciliation and closure

Synchronise the entire feature-local `tests/retired-step12-3/` directory and
new raw logs from `mango` back to the authoritative **Windows Diaries repo**
(using Beyond Compare 4). Check manifest/checksum parity before accepting the
Playbooks deletion commit. Preserve accepted historical reports and logs.
Do not remove live `roles/btrfs-replication/files/` modules or change Ansible,
systemd, snapshots, parent state or timer schedules as part of this cleanup.
Step 12 remains OPEN until the separately scheduled 8 November receiver-prune
run is verified and formally accepted.
