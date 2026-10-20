#!/bin/sh
set -eu
[ -f roles/remote-backup/tasks/native.yaml ] || { echo 'Run from Playbooks repository root' >&2; exit 1; }
rm -f -- 'roles/remote-backup/files/btrfs-native-pull.py'
rm -f -- 'roles/remote-backup/files/whole-backup-pull.py'
rm -f -- 'roles/remote-backup/templates/whole-backup-pull.sh.j2'
rm -f -- 'roles/remote-backup/tests/verify-whole-backup-pull.py'
rm -f -- 'roles/remote-backup/tests/verify-native-btrfs-incremental.py'
