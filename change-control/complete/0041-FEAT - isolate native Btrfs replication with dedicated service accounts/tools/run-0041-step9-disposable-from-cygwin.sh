#!/usr/bin/env bash
# 0041 Step 9 disposable Btrfs fixture launcher. Run in Windows Cygwin.
# This script does not change production replication state, service or timer.
set -euo pipefail
repo='/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
feature='change-control/in-progress/0041-FEAT - isolate native Btrfs replication with dedicated service accounts'
script="$repo/$feature/tests/verify-0041-step9-disposable-on-mars.sh"
output="$repo/$feature/evidence/Step 9/disposable-native-transfer-$(date -u +%Y%m%d-%H%M%SZ).txt"
cd "$repo"
test -f "$script"
mkdir -p "$(dirname "$output")"
printf '0041 Step 9 evidence: %s\n' "$output"
set +e
( set -o pipefail; ssh -T mango 'ssh -T mars "sudo -n bash -s"' < "$script" 2>&1 | tee "$output" )
rc=$?
set -e
if (( rc == 0 )); then
  echo "PASS: 0041 Step 9 isolated native Btrfs test (log: $output)"
else
  echo "FAIL: 0041 Step 9 isolated native Btrfs test (exit $rc, log: $output)" >&2
fi
exit "$rc"
