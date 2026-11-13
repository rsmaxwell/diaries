# 0048 Step 2 disposable clean-clone test

Execute from the authoritative **Windows Cygwin** terminal after applying this Diaries-only ZIP in Beyond Compare 4. The tool is **streamed directly** to `mango`; no Diaries resynchronisation on `mango` is needed.

```bash
(
  cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries' || exit 1
  feature='change-control/in-progress/0048-FEAT - evaluate backup collection permissions and simplify tooling'
  output="$feature/evidence/Step 2/clean-clone-and-ansible-$(date -u +%Y%m%d-%H%M%SZ).txt"
  mkdir -p "$(dirname "$output")" || exit 1
  (
    set -o pipefail
    ssh mango 'bash -s' < "$feature/tests/verify-0048-step2-cleanclone.sh" 2>&1 | tee "$output"
  ) || exit 1
)
rc=$?
if [ "$rc" -eq 0 ]; then
  echo 'PASS: Diagnostic script completed (inspect Step 2 B3 result in the log)'
else
  echo "FAIL: Step 2 diagnostic script (exit $rc)"
fi
```

The script verifies all three controller Git checkouts are clean and that the Playbooks SHA matches the parent's submodule pin; clones the **published Playbooks remote** to a fresh temporary checkout at the pinned commit with umask `022`, without restoration; checks 14 source entry modes and nine hashes; then runs two consecutive **local-only**, unprivileged Ansible reproductions of the production `file` + `synchronize` options against a fresh temporary target. The temporary clone and target are deleted on exit. It does **not** deploy to `mars`, edit controller source, change inventory, touch Btrfs snapshots or write secrets.

If the second Ansible run reports `changed>0`, this is a **successful detection of a Step 2 B3 failure**, not proof of deployment readiness. The log will state `STEP2 B3: FAIL`; do not mark B3 PASS or run a production deployment. If the harness itself cannot run (e.g. remote clone unavailable or collection missing), it exits nonzero.

This fixture reproduces the two directory/synchronization portions, not the entire backup-collection role. Additional read/traverse/writer security checks and final mode disposition are still required before Step 2 can be accepted.
