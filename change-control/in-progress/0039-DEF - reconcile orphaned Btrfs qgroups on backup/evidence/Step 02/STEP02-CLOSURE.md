# Step 02 — Final evidence and closure

**Decision:** CLOSED, 2026-10-21. Root-cause *diagnostic* accepted; future Btrfs accounting remediation remains out of scope pending Step 3 approval.

## Accepted evidence chronology

| Evidence | Host | Accepted result |
|---|---|---|
| `note(20261021-095715).txt` | mango → mars | Initial dry-run exposed dangerous writer-lock and Diaries verification config drift; deployment blocked |
| `note(20261021-100132).txt` | mango | Role-scoped variables in local-backup explained drift |
| `note(20261021-100750).txt` | mango | Corrected launcher/host-context regression, Ansible syntax and diff tests pass |
| `note(20261021-101108).txt` | mango | Revised mars dry-run: exactly one executable change; configuration unchanged |
| `note(20261021-101417).txt` | mango | mars --apply: ok=30 changed=1 failed=0 |
| `note(20261021-101500).txt` | mars | Running executable syntax OK, all three timers enabled, 61 complete/0 incomplete, valid production verification, 41 stale |
| `note(20261021-101725).txt` | mango | mars check-mode idempotency: changed=0 failed=0 |
| `note(20261021-101854).txt` | mars | Native delete subvol_id=20920 (@data), 20919 (root); both subsequently `<stale>`; stale 41→43 |
| `note(20261021-102648).txt` | backup | btrfs-progs 5.16.2 lowercase `qgroupid rfer excl`, original unexpected_output, no quota rescan |
| `note(20261021-102841).txt` | mango | Parser source requires uppercase Qgroupid; existing regression inspected |
| `note(20261021-103130).txt` | mango | Parser and native prune regressions, syntax and diff check pass |
| `note(20261021-103354).txt` | mango | backup check-mode: exactly one executable change; no config or timer change |
| `note(20261021-103619).txt` | mango | backup --apply: ok=24 changed=1 failed=0; preflight parses 29,571 qgroups |
| `note(20261021-103721).txt` | backup | Runtime syntax OK, 29,571 qgroups, zero explicit stale, no rescan, all local snapshot timers disabled |
| `note(20261021-103828).txt` | mango | backup check-mode idempotency: changed=0 failed=0 |

Earlier exact Snapper legacy deletion correlations: subvolumes 20189, 20237, 20261 match stale qgroups, from `note(20261021-092113).txt` and `note(20261021-092525).txt`.

## Scope and interpretation

- **Demonstrated:** native *and* legacy successful snapshot deletion on `mars` can leave an exact-ID stale qgroup; the old `backup` parser failed on header case/version differences; corrected program deploys idempotently.
- **Not demonstrated:** why the kernel retains the qgroups, whether delayed cleanup eventually occurs, that all zero-used/unmatched records can safely be destroyed, or that the OS upgrade will fix recurrence.
- **No destructive remediation:** no quota disable, destroy, rescan initiation, snapshot deletion performed to reproduce the defect, or upgrade. Normal scheduled native prune on mars continued.
- **Remaining:** Step 3 version-independent reconciliation, candidate safety/relationships, controlled rollback limits, independent maintenance and supported-upgrade decisions.
- **Revision evidence:** Playbooks changes are present in working-tree `git status` captures; no post-change Git commit hash or push is established in this evidence. Do not claim a commit.

**Acceptance outcome:** Step 2 CLOSED; 0039-DEF remains IN PROGRESS at Step 3.
