#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
feature="$(cd -- "$here/.." && pwd)"
if [[ ! -f "$here/step04-timezone-regression.py" ]]; then
  echo "Missing feature regression script" >&2; exit 2
fi
ssh mango 'python3 - /home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py' \
  < "$here/step04-timezone-regression.py" \
  | tee "$feature/evidence/Step 04/step04-timezone-regression-output.txt"
