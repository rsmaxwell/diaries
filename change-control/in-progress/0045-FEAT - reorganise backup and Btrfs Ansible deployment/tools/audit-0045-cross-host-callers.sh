#!/usr/bin/env bash
# Run from Windows Cygwin. Captures evidence in authoritative Windows Diaries repo.
# Purely read-only on mango, mars, backup, and pluto.

if ! cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'; then
  echo 'FAIL: Windows Diaries checkout not found' >&2
  exit 1
fi

feature='change-control/in-progress/0045-FEAT - reorganise backup and Btrfs Ansible deployment'
remote="$feature/tools/audit-0045-host-callers.py"
base="$feature/evidence/Step 2"
when=$(date -u +%Y%m%d-%H%M%SZ)
out="$base/caller-audit-$when"
mkdir -p "$out" || exit 1

test -s "$remote" || { echo "FAIL: Missing $remote" >&2; exit 1; }
python3 -c 'import ast, sys; ast.parse(open(sys.argv[1], encoding="utf-8").read())' "$remote" || exit 1

echo "0045 read-only external caller audit UTC $when"
echo "Evidence: $out"
failed=0
for host in mango mars backup pluto; do
  echo "=== Inspect $host ==="
  # Avoid sudo prompts/hangs; report failures rather than treating missing access as no callers.
  if ssh -o BatchMode=yes -o ConnectTimeout=15 "$host" 'sudo -n python3 -' \
       < "$remote" > "$out/$host.json" 2> "$out/$host.stderr.txt"; then
    if ! python3 - "$out/$host.json" "$host" <<'PYJSON'
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    d=json.load(f)
assert d['schema']=='0045-legacy-caller-audit-v1'
assert d['host']==sys.argv[2], (d['host'],sys.argv[2])
assert not d['unreadable_paths'], d['unreadable_paths']
print(f"PASS: {d['host']} audited; matching files: {len(d['matching_files'])}; oversize files skipped: {len(d['large_files_skipped'])}")
for p in d['matching_files']:
    print(f"  MATCH: {p}")
if d['host']=='pluto' and not d['jenkins_filesystem_visible']:
    print('  NOTE: Jenkins job files NOT visible in standard host paths; separate Jenkins audit required')
PYJSON
    then
      echo "FAIL: invalid or incomplete response from $host" >&2
      failed=1
    fi
  else
    echo "FAIL: SSH/sudo/audit failed for $host (see $out/$host.stderr.txt)" >&2
    failed=1
  fi
done

if test "$failed" -ne 0; then
  echo "FAIL: Caller audit incomplete; inspect $out" >&2
  exit 1
fi
echo "PASS: Four-host filesystem caller audit finished. Review matches and Jenkins/external limitations before retiring any launcher."
echo "Evidence: $out"
