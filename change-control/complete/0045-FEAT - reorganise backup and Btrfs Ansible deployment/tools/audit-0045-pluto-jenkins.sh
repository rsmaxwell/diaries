#!/usr/bin/env bash
# Windows Cygwin: read-only Jenkins live-pod scan using the existing SSH alias.
if ! cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'; then
  echo 'FAIL: Diaries checkout not found' >&2
  exit 1
fi
feature='change-control/in-progress/0045-FEAT - reorganise backup and Btrfs Ansible deployment'
script="$feature/tools/audit-0045-pluto-jenkins.py"
out_dir="$feature/evidence/Step 2"
out="$out_dir/pluto-jenkins-pod-$(date -u +%Y%m%d-%H%M%SZ).txt"
test -s "$script" || { echo "FAIL: Missing $script" >&2; exit 1; }
mkdir -p "$out_dir" || exit 1
if ssh -o BatchMode=yes -o ConnectTimeout=15 pluto 'python3 -' < "$script" > "$out" 2>&1; then
  cat "$out"
  echo "PASS: Jenkins audit evidence: $out"
else
  status=$?
  cat "$out"
  echo "FAIL: Jenkins audit returned $status; evidence: $out" >&2
  exit "$status"
fi
