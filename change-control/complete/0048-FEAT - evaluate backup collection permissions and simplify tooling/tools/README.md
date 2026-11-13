# 0048 — Feature-specific tools

## `collect-step1-acls.sh`

Read-only Step 1 collector. It expects to run **on `mango`** with the live controller at `/home/richard/ansible-controller`, verifies clean parent and submodule working trees and post-0046 inventory entry point, then gathers mode/owner/group/ACL metadata from the fourteen 0047 mode-contract paths and corresponding installed paths on `mars` via `ssh mars 'sudo -n bash -s'`.

It does not print filter contents or decrypted inventory, modify any permissions, or run Ansible deployments.

For convenience, after applying this package to the authoritative **Windows** Diaries working copy, run from a **Windows Cygwin terminal**:

```bash
(
  cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries' || exit 1
  feature='change-control/in-progress/0048-FEAT - evaluate backup collection permissions and simplify tooling'
  output="$feature/evidence/Step 1/acl-and-access-$(date -u +%Y%m%d-%H%M%SZ).txt"
  ( set -o pipefail
    ssh mango 'bash -s' < "$feature/tools/collect-step1-acls.sh" 2>&1 | tee "$output"
  ) || exit 1
)
rc=$?
if [ "$rc" -eq 0 ]; then
  echo 'PASS: ACL evidence captured in authoritative Windows Diaries feature directory'
else
  echo "FAIL: ACL evidence collection (exit $rc); review the saved log"
fi
```

The remote Bash process is a non-interactive launched script and may use `set -Eeuo pipefail`; the local Cygwin interactive shell retains its settings. The evidence file is written to the Windows change-control feature directory, so there is **no need to synchronise the Diaries checkout to `mango` merely to run this collector**. Review the generated log before committing it (metadata only, but contains usernames and paths).

If `getfacl` is unavailable on either host, the collector stops with `INCOMPLETE`; do not install packages or alter the host merely to make this audit succeed without reviewing the missing evidence first.
