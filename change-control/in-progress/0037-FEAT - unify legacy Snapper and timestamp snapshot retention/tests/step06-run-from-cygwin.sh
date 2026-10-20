#!/usr/bin/env bash
set -euo pipefail
base="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source="$base/tests/step06-guarded-regression.py"
output="$base/evidence/Step 06/results.txt"
mkdir -p "$(dirname "$output")"
ssh mango 'python3 - /home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py' < "$source" 2>&1 | tee "$output"
