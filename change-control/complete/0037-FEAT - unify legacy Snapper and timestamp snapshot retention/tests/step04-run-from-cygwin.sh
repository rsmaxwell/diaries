#!/usr/bin/env bash
# 0037-FEAT Step 4: execute feature-local regression against Playbooks on mango.
# Run from the Diaries repository root with:
# bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tests/step04-run-from-cygwin.sh"
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
test_script="$script_dir/step04-plan-regression.py"

if [[ ! -r "$test_script" ]]; then
  printf 'ERROR: regression script not found: %s\n' "$test_script" >&2
  exit 2
fi

# Override these if your SSH alias or remote project path differs.
remote_host="${STEP04_SSH_HOST:-richard@mango}"
remote_playbooks="${STEP04_PLAYBOOKS_DIR:-/home/richard/playbooks}"

# Quote the remote directory for POSIX sh. A newline is not supported.
if [[ "$remote_playbooks" == *$'\n'* ]]; then
  echo 'ERROR: remote Playbooks path must not contain a newline' >&2
  exit 2
fi
quoted_remote_path="'${remote_playbooks//\'/\'\\\'\'}'"
remote_command="cd -- $quoted_remote_path && python3 - roles/snapshots/files/btrfs-snapshot-manager.py"

printf 'Running 0037-FEAT Step 4 regression on %s (Playbooks: %s)\n' "$remote_host" "$remote_playbooks"
# The regression source is sent on stdin. No files are copied to mango.
ssh -o BatchMode=yes "$remote_host" "$remote_command" < "$test_script"
printf 'PASS: remote Step 4 regression finished successfully\n'
