#!/usr/bin/env bash
# 0028: read-only, bounded paired-backup content-presence and identity inspection.
# Run from Windows PC Cygwin Diaries parent checkout. No snapshots/restores/mutations.
set -euo pipefail
umask 077
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
check="$feature/tools/step3_retained_dataset_check.py"
if [[ ! -f "$check" || ! -f "$feature/IMPLEMENTATION-STEPS.md" ]]; then
  echo 'FAIL: run from the Windows Diaries parent repository root, after applying 0028 package' >&2
  exit 2
fi
for cmd in ssh python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then echo "FAIL: missing $cmd" >&2; exit 2; fi
done
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="$feature/evidence/Step 3/private/${stamp}-retained-components"
mkdir -p "$out"
echo "Private read-only retained-pair evidence: $out"
for host in mars backup; do
  echo "=== ${host}: privileged manifest-history status (READ-ONLY) ==="
  if ssh -o BatchMode=yes -o RequestTTY=no -o ConnectTimeout=15 "$host" \
     'sudo -n /usr/local/sbin/diaries-backup-status --json' > "$out/$host-status.json" 2>"$out/$host-status.err"; then
    echo "PASS: $host host-local status collected"
  else
    code=$?
    echo "FAIL: $host status returned $code; inspect private $out/$host-status.err" >&2
    exit 2
  fi
done
if backup_id=$(python3 "$check" --select "$out"); then
  echo "PASS: both hosts report the same latest healthy production backup: $backup_id"
else
  echo 'FAIL: backup identity/health mismatch (no content inspection attempted)' >&2
  exit 2
fi
for host in mars backup; do
  echo "=== ${host}: retained dataset components, sizes and small metadata hashes (READ-ONLY) ==="
  # The local tool is piped directly to remote Python; nothing is installed there.
  # sudo -n is necessary to read Btrfs snapshot metadata; it is never used for writes.
  if ssh -o BatchMode=yes -o RequestTTY=no -o ConnectTimeout=15 "$host" \
       "sudo -n python3 - '$backup_id'" < "$check" > "$out/$host-contents.json" 2>"$out/$host-contents.err"; then
    echo "PASS: $host retained components inspected"
  else
    code=$?
    echo "FAIL: $host component inspection returned $code; see private $out/$host-contents.err" >&2
    exit 2
  fi
done
python3 "$check" --summarize "$out"
