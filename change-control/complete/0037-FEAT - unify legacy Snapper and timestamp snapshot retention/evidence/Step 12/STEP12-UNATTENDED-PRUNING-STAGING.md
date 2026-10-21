# 0037-FEAT — Original Step 12 unattended retention (STAGED, NOT ACTIVATED)

Date: 2026-10-20. Operator elected to activate unattended legacy and native pruning; source changes staged but **production authorisation requires live acceptance**. This is separate from supplemental qgroup cleanup (already completed).

## Contract

- Native prune continues through `btrfs-snapshot-prune.timer` (mars; previously 08:15 UTC). No new timer.
- Explicit host opt-in adds a SECOND ExecStart to the existing oneshot service, only after native prune succeeds; default remains disabled. One oldest eligible legacy timeline-single per run; maximum 2 enforced in CLI.
- Reuse 0037 combined GFS selection; native keep floor, replication pins and holds; exclude manual/pre-post/non-timeline; protect latest legacy anchor; minimum age; fail closed on bad mapping/inventory/partial native pairs.
- Each delete repeats the full combined plan with source identity and candidate checks, verifies Btrfs UUID/subvolume ID stable and uses `snapper -c CONFIG delete NUMBER`. No quota cleanup, no full restore or remote deletions.
- Existing one-ID `legacy-delete` approval interface remains unchanged; `legacy-prune` is an independent explicitly opt-in unattended interface.
- Source baseline from `playbook-sources-20261020-144701.zip` overlaid with newer accepted `0037-qgroup-status-playbooks-20261020.zip` to avoid losing production qgroup status reporting.

## Acceptance gates

1. On mango, apply Playbooks ZIP, run `python3 -m py_compile roles/snapshots/files/btrfs-snapshot-manager.py`; `python3 roles/snapshots/tests/verify-unattended-legacy-prune.py`; existing native manager and qgroup-status regressions.
2. Inspect `ansible mars -m setup -a 'filter=ansible_hostname'` and staged role flags; verify mapping root=root, @data=@data and both Snapper configs.
3. Targeted install of manager on mars, with Ansible `copy backup=yes`, leaving systemd service/timer unchanged. Verify SHA, read-only `legacy-plan` and existing status, holds/pins, native dry-run, receiver receipts, no concurrent jobs.
4. Only after operator review, enable host-scoped opt-in in Playbooks configuration, render + inspect the service template, deploy ONLY that service unit and reload systemd. Never enable default Snapper cleanup/timeline timers. Do not manually start the destructive service during acceptance.
5. Allow scheduled run, capture journal, before/after legacy inventories, native state, receiver protection and rollback acceptance. If failures occur, immediately remove the second ExecStart via disabled template deployment, daemon-reload; retain the native prune command/timer.

## Status

**ORIGINAL STEP 12: IN PROGRESS — source staged; unattended activation NO-GO pending live acceptance.**
Do not mark Step 12 closed until unattended native+legacy execution and rollback are evidenced. No implicit authorisation for bulk/manual deletions.
