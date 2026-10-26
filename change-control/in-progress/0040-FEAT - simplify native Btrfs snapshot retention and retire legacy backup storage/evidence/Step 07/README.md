# 0040-FEAT — Step 07 evidence register

**Status: CLOSED — 25 October 2026 (accelerated acceptance).**

## Acceptance scope

Original Step 7: Ansible `--check --diff` and rollback preparation, explicitly approve the proposed changes. The subsequent non-destructive deployment/verification was carried out early and is also recorded here as supporting evidence; it does **not** independently close Step 8.

## Recorded evidence — 25 October 2026

1. `native-btrfs.yaml` syntax check passed, targeted `--check --diff` against `mars,backup` completed without failed tasks. The first dry run proposed removal of `richard`'s constrained receiver-delete sudo permission; this was rejected by the operator, and the Playbooks template was corrected.
2. Corrected dry run: `mars` proposed two changes (snapshot-manager JSON serialization, native-push script); `backup` proposed two changes (sudoers comment/formatting while **retaining** the permission, updated receiver manager). No receiver configuration change, timers change or destructive action was proposed. Both hosts had `failed=0`.
3. Rollback copies created, preserving source directory hierarchy:
   - `mars`: `/home/richard/rollback/0040-step07-20261025-073634Z/` — native push executable, snapshot manager, sudoers and snapshot-manager JSON.
   - `backup`: `/home/richard/rollback/0040-step07-20261025-073636Z/` — snapshot manager, sudoers and snapshot-manager JSON. Native push executable not installed here (expected).
   These are host-local rollback copies; no restore has been attempted. File existence was listed in terminal output; no independent hash comparison was recorded.
4. The controlled `native-btrfs.yaml --limit mars,backup` apply completed successfully: `mars ok=15 changed=2 failed=0`, `backup ok=20 changed=2 failed=0`. This is an *early execution of Step 8-type work* rather than a prerequisite to Step 7 closure.
5. Post-deployment checks: `mars` 63 complete paired timestamp sets and zero incomplete; Diaries verification valid, backup ID `20261025-003218Z`; installed config still requires and creates `['root','@data']`. `backup` receiver recovery `CLEAN` and `receiver_prune_enabled=false`; retained sudoers line for `richard` matched and `visudo` parsed OK. No snapshot deletion was requested.
6. Repeated `native-btrfs.yaml --check --diff`: `mars ok=15 changed=0 failed=0`; `backup ok=20 changed=0 failed=0`.
7. Accepted source revision on `mango`: `a8f857c` (`0040-FEAT Step 7: preserve receiver-delete sudo permission`), based on `b51a5b0`; Git working tree clean immediately after commit.

## Explicit limitations and outstanding work

- The agreed accelerated path waives another full cross-host deletion rehearsal; this test is **not** claimed as passed.
- The 234 stale qgroups reported on `mars` remain tracked separately; `qgroups_under_deletion=0`.
- The dry run includes only the existing paired-source production configuration; the future `@data`-only cutover has **not** been activated.
- Retaining the manual `delete-receiver` sudo permission is an explicit operator decision; it does not enable automatic receiver pruning.
- Step 8 requires its **own** acceptance check and record, reconciling the already-deployed components; this register does not authorise destructive legacy cleanup or further cutover.

## Decision

**Step 07 CLOSED (25 October 2026)** on accepted Ansible diff, confirmed rollback copies, and source revision `a8f857c`. This record is an interpreted evidence summary of terminal outputs supplied in the chat; raw logs should be archived separately if required by the project retention policy.
