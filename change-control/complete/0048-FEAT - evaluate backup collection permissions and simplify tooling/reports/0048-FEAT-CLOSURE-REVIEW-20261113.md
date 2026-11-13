# 0048-FEAT — Formal closure candidate

**Prepared:** 13 November 2026 (UTC)
**Formal status:** CLOSED — operator formally accepted; publication receipt is the Diaries closure commit.

## Outcome proposed for acceptance

**Disposition A — RETIRE the active 0047 source-mode restoration dependency.**

Normal Git-checkout modes are sufficient for the 14 synchronised backup-collection entries in the reviewed environment. The permanent Ansible role no longer requires a source-mode manifest or one-time chmod restoration. The Playbooks source change was published at `c5109340a2fe13296a2343c682e1079d1a212c8d`, and the parent Ansible controller pins that revision at `83cba342d9ffe7da51a97bda9231f32d02beb2e3`. The historical 0047 scripts and evidence remain archived in `change-control/complete/0047-FEAT...` and are not deleted.

The clean-clone, two disposable Ansible scenarios, live `mars` deployment and repeat application all passed. The targeted live second run was `changed=0`, with no errors. Installed modes, hashes, owners and ACLs were verified, backup scheduling remained present, and read-only backup/replication health checks passed.

## Non-blocking separate work

- 0039-DEF: monitor recurring stale Btrfs qgroups (2 reported; `qgroups_status=ok`).
- 0035-FEAT: status tool notes an already tracked history-verification configuration limitation.
- `mango` pending kernel reboot noted during unrelated `acl` package installation; schedule separately.

These are not additional 0048 deployment or closure tasks.

## Formal closeout gate

Before closing: confirm that successful publication/deployment/health logs exist in `evidence/Step 3/` and `evidence/Step 4/`; review the reconciled implementation steps and acceptance matrix; validate that only intended change-control files are staged; move the whole feature folder to `change-control/complete/`; commit and push on the authoritative Windows Diaries `main`. The operator's explicit execution of the final acceptance/closure command is the acceptance action. Do not claim a successful closeout until the Git push and final status check pass.
