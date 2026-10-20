#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
test -f roles/remote-backup/files/btrfs-native-push.py || { echo 'Not at Playbooks root' >&2; exit 1; }
for f in \
  roles/remote-backup/files/btrfs-native-pull.py \
  roles/remote-backup/files/whole-backup-pull.py \
  roles/remote-backup/templates/whole-backup-pull.sh.j2 \
  roles/remote-backup/tests/verify-whole-backup-pull.py \
  roles/remote-backup/tests/verify-native-btrfs-incremental.py; do
  if [[ -e "$f" ]]; then rm -- "$f"; printf 'REMOVED %s\n' "$f"; else printf 'ALREADY ABSENT %s\n' "$f"; fi
done
