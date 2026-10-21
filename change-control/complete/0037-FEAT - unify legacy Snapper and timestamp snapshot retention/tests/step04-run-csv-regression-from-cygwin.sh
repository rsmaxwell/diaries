#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ssh "${STEP04_SSH_TARGET:-richard@mango}" \
  "python3 - '${STEP04_MANAGER:-/home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py}'" \
  < "$HERE/step04-csv-header-regression.py"
