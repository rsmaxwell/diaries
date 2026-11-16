# 0049-FEAT — First mango source and Ansible preview review (16 November 2026)

**Stage:** Step 3 preliminary validation, before live installation. **Not CLOSED.**

## Grounded evidence

Received read-only terminal log: `evidence/Step 3/MANGO-SOURCE-AND-ANSIBLE-CHECK-20261116.txt`.

- Working copy: `/home/richard/ansible-controller/playbooks`, branch `main`, HEAD `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532`.
- Applied 0049 Playbooks implementation visible as 23 tracked changed files and 9 untracked new files in `git status --short`. Treat all as local uncommitted state; inspect before any checkout/reset.
- New 0049 source tests: 19/19 passed. Expected `ERROR:` lines are explicit refusal cases.
- 0041 restricted identity tests: 8/8 passed.
- Replication protocol regression tests: 25/25 passed.
- Ansible check-mode preview: `backup ok=30 changed=6 unreachable=0 failed=0 skipped=47`; `mars ok=22 changed=6 unreachable=0 failed=0 skipped=55`.
- Top-level reported `0049 SOURCE AND ANSIBLE PREVIEW: PASS`.
- Preview creates new `btrfs-push` source units using `User=btrfs-send` and existing 0041 restricted wrapper; receiver prune service remains bounded at 10. Configured calendars observed: 03:30 UTC push, 04:15 UTC receiver prune.
- Check-mode deliberately skipped stopping old timers, activating new timers, removing old service files, and deleting the obsolete runtime. No host migration was demonstrated.
- Two independently held receiver checkpoints were validated in Ansible check-mode (record details retained in raw log).

## Review finding and correction

The receiver timer description in the first package still included the historical phrase `0040 Simplified`. A focused Playbooks naming-corrections ZIP changes only operator-visible help/error text, the timer description and tests; persisted `.simple-*` state paths, actual Btrfs replication protocol, privileges, retention, clocks and deletion caps remain unchanged.

Correction regressions run against the 12/16 November source overlay: 0049 (19), 0041 (8), replication (25), 0040 receiver retention (17), 0040 source prune cap and Diaries report test all passed. The correction ZIP must still be applied to the user's current Playbooks checkout and tested there.

## Next action and acceptance limits

Apply naming corrections with Beyond Compare, then deploy **receiver `backup` first** using the approved `btrfs-replication.yaml` on `mango`. Check actual systemd transition, local parent state, bounded prune preview and report health before deploying `mars`. Follow with sender deployment, cross-host agreement and full feature read-only verification; capture resulting evidence under `evidence/Step 4/`.

No live deployment, snapshot deletion, transfer, or state migration has been established by this report.
