#!/usr/bin/env bash
# 0037-FEAT Step 1: read-only captures from Cygwin on Windows.
# Run: bash tools/step01-capture-from-cygwin.sh
set -uo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
feature_dir="$(cd -- "$script_dir/.." && pwd)"
capture="$script_dir/step01-readonly-capture.sh"
output_dir="$feature_dir/evidence/Step 01"

if [[ ! -r "$capture" ]]; then
  printf 'ERROR: Missing capture script: %s\n' "$capture" >&2
  exit 2
fi
if ! command -v ssh >/dev/null 2>&1; then
  echo 'ERROR: ssh is not available in this Cygwin shell.' >&2
  exit 2
fi
mkdir -p -- "$output_dir" || exit 2

failed=0
for host in mars backup; do
  output="$output_dir/${host}-capture.txt"
  printf 'Capturing %s -> %s\n' "$host" "$output"
  # The Linux capture script is piped via stdin, without copying it to the host.
  # BatchMode avoids hanging waiting for SSH passwords; ensure key access first.
  if ssh -o BatchMode=yes -o ConnectTimeout=15 "richard@$host" 'bash -s' \
      < "$capture" > "$output" 2>&1; then
    printf 'OK: %s (%s lines)\n' "$host" "$(wc -l < "$output")"
  else
    rc=$?
    printf 'FAILED: %s (ssh exit status %s). See %s\n' "$host" "$rc" "$output" >&2
    failed=1
  fi
done
printf '\nCapture files are under: %s\n' "$output_dir"
exit "$failed"
