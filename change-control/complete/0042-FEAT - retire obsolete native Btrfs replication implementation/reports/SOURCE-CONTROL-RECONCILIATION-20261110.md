# 0042-FEAT — Source-control separation plan (10 November 2026)

## Accepted operational baseline

Step 1 retired and archived 215 tracked legacy Playbooks files. Step 2 simplified-only Ansible deployment ran with 0 changes/0 failures on mars and backup. Step 3 host audit confirmed 39 and 35 obsolete host paths absent; protected parent equality, timer status and snapshot health verified. Final readback confirmed the 215-file archive SHA-256 and verified production backup. Existing evidence is held under this feature.

## Git reconciliation

Playbooks HEAD before the change was `e0da797310ab452ddc61e7368c50a444fe881e41`, with 215 deletions already staged. Six modified files belong exclusively to 0042. Two shared files (`roles/btrfs-replication/defaults/main.yaml` and `roles/btrfs-replication/tasks/native.yaml`) also contain 0039's appended qgroup integration. The feature-local `stage-0042-only.py` verifies the exact contents and prepares a 0042-only Git index: 215 deletions and eight modified files. It leaves the working tree untouched and leaves both 0039 portions unstaged. It refuses unexpected changes, a different Git HEAD, a different branch or missing manifest.

After reviewing the staged diff, the operator commits the 0042 Playbooks change, preserving all 0039 source changes for a separate commit. The independent 0042 Diaries feature evidence is committed on Windows only after verifying that only this feature is staged. Record both Git revisions and copy generated evidence to Windows. Do not move 0042 to `complete` or mark steps CLOSED without explicit acceptance and final Git receipts.

This separation does not invoke Ansible, replication, pruning, snapshot deletion or quota modification.
