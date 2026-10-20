# 0037-FEAT Step 4 — Snapper timezone-less CSV date correction (19 October 2026)

The installed `snapper --csvout --iso -c @data list` on `mars` returns dates such as `2024-05-26 13:00:20` without timezone offsets. `mars` was independently verified as `Timezone=Etc/UTC`.

The read-only `legacy-plan` inventory parser now treats offset-less dates as UTC **only if** `timedatectl show -p Timezone --value` confirms `Etc/UTC` or `UTC`. Unknown/non-UTC timezone fails closed. Explicit offsets are still converted to UTC. No `create`, `prune`, `run`, scheduler, Snapper configuration or deletion path was changed.

Tests: Python compilation; modern/historical CSV header regression; installed-format timezone-less UTC acceptance; non-UTC and unknown timezone rejection; explicit-offset conversion. All passed locally.

## Operator procedure

1. Extract the corrected manager into the feature's `tools/` folder on Windows and the test and launcher into `tests/`.
2. From Cygwin in the feature `tools/` folder: `scp ./btrfs-snapshot-manager.py mango:/home/richard/playbooks/roles/snapshots/files/`.
3. From the Diaries root in Cygwin: `bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tests/step04-run-timezone-regression-from-cygwin.sh"`.
4. When PASS, on `mango`: `cd ~/playbooks && ansible mars -b -m ansible.builtin.copy -a "src=roles/snapshots/files/btrfs-snapshot-manager.py dest=/usr/local/sbin/btrfs-snapshot-manager owner=root group=root mode=0755 backup=yes"`.
5. From Cygwin: `ssh mars 'sudo btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data'`.

This remains a read-only Step 4 verification. Do not run native `prune`, Snapper `delete`, or scheduler changes as part of this validation. Step 4 remains OPEN pending review of the live plan.
