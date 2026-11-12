# Step 2 repository staging commands (Windows Cygwin terminal)

Apply this ZIP to the **Windows Diaries repository root** with Beyond Compare 4. It adds only feature-local tool, test and documentation files. Do not copy prepared inventory, encrypted files or the Vault password into this ZIP or into the Diaries repository.

Use the following one command block exactly as shown; it runs preflight and, only if preflight passes, apply. `if ( ... ); then` keeps failures isolated from the interactive Cygwin shell.

```bash
if (
  cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries' || exit 1

  feature='change-control/in-progress/0046-FEAT - move non-sensitive Ansible inventory into Playbooks Git'
  script="$feature/tools/establish-0046-three-repositories.sh"
  evidence="$feature/evidence/Step 2"

  test -f "$script" || exit 1
  mkdir -p "$evidence" || exit 1
  bash -n "$script" || exit 1

  echo '=== Read-only repository preflight ==='
  preflight="$evidence/repository-preflight-$(date -u +%Y%m%d-%H%M%SZ).txt"

  ssh mango 'bash -s -- --preflight' < "$script" 2>&1 | tee "$preflight"
  test "${PIPESTATUS[0]}" -eq 0 || exit 1

  echo '=== Establish private repositories and submodules ==='
  log="$evidence/repository-assembly-$(date -u +%Y%m%d-%H%M%SZ).txt"

  ssh mango 'bash -s -- --apply' < "$script" 2>&1 | tee "$log"
  test "${PIPESTATUS[0]}" -eq 0 || exit 1

  echo "Evidence: $log"

); then
  echo 'PASS: 0046 three-repository staging completed'
else
  echo 'FAIL: 0046 repository staging requires review'
fi
```

If the preflight says `gh` is missing or unauthenticated, stop; do not start apply manually. If apply reports an error, retain the partial state and the evidence log and investigate before another attempt. Avoid committing files from `evidence/Step 2` until reviewed for accidental sensitive output.
