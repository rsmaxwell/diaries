#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/step04-empty-snapper-regression.py"
SSH_TARGET="${STEP04_SSH_TARGET:-richard@mango}"
MANAGER="${STEP04_MANAGER:-/home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py}"
ssh "$SSH_TARGET" "python3 - '$MANAGER'" < "$SCRIPT"
