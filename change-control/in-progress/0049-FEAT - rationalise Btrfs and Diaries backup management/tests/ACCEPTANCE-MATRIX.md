# 0049 — Acceptance matrix

**Technical result (16 November 2026): PASS.** Application/infrastructure reporting, formatted tables, JSON, renamed units, 0041 identity preservation, receiver holds, live replication, independent receiver read-back and Ansible `changed=0` were verified in source/live evidence. Git revision/publishing and formal feature closure (OP-04 and administrative part of CC-01) remain open. See `reports/FINAL-TECHNICAL-ACCEPTANCE-20261116.md` and `reports/REPOSITORY-FINALISATION-20261116.md`. The following matrix remains the original acceptance contract rather than an invented individual signed-off test record.

| ID | Acceptance condition | Expected evidence |
| --- | --- | --- |
| CC-01 | Current Windows Diaries parent, submodules and `mango` Ansible-controller/Playbooks/inventory revisions, dirty states and deployed scripts/units frozen before modifications | Baseline revisions, `git status`, live installed hashes and host inventory |
| CC-02 | No widening of 0041 sender/receiver SSH, sudo, identities, wrappers, privilege boundary or secret exposure | Effective unit, account and policy comparison, negative tests |
| DI-01 | `diaries-backup-status` contains **only Diaries dataset** backup/history/verification content | Text + JSON fixture and `mars` read-back; excluded-field assertions |
| DI-02 | Most recent and previous backup IDs, logical dataset, retained occurrences, first/last snapshots, conflict and evidence states computed accurately | Synthetic grouped/ungrouped history tests |
| DI-03 | `diaries-backup-history list`, `--all`, `show`, `path`, `verify` retain their intended selection, conflict and full-verification semantics | Regression log incl single-line `path` output |
| BS-01 | `btrfs-backup-status` installs on **both** hosts; renders only host-applicable sections | Host-mode fixture tests plus read-only mars/backup output |
| BS-02 | Last pull, accepted marker, agreed parent/prior, received inventory, last completed cycle and last verified transfer cannot be mislabeled or inferred from one another | Source-failure, no-transfer-success and receiver-ahead fixtures |
| BS-03 | `--local-only` does not execute SSH or other remote probes and labels remote values `not checked` appropriately | Mocked transport-call count = 0 and host test |
| BS-04 | Required check failure/degraded status produces documented nonzero exit; success/no remote check does not falsely fail | Exit 0/1/2 table, stdout/stderr capture |
| NM-01 | Active CLI, help, status labels, systemd units, timers, Ansible defaults/inventory and current docs use neutral names, with old historical scheme references limited to justified internal/history records | Source/install grep audit with explained exceptions |
| NM-02 | Legacy receiver commands and `receiver-prune --approval-file` are retired/reserved safely with callers audited; no name collision | Cross-reference map and negative tests |
| NM-03 | Only one enabled push timer on `mars`, one receiver prune timer on `backup`; original schedule and limit preserved | Before/after `systemctl list-timers`, unit contents and Ansible read-back |
| NM-04 | Old path/unit cleanup is source-controlled and idempotent; rollback cannot activate duplicate writers | `--check --diff`, deployment cleanup, rollback proof |
| FM-01 | All list-like human output (Diaries recent/history, Btrfs snapshot list, receiver prune plan and expanded status tables) has section title, column headers, aligned numeric fields and UTC timestamps | Golden text output fixtures and representative live output |
| FM-02 | Empty lists, long names/IDs/paths, missing values, lots of rows, odd Unicode and wide values do not misalign or truncate critical content | Boundary/empty/golden tests |
| JS-01 | Every operator-facing JSON response is a **single indented document** (2-space indent, newline), valid to a standard parser and `jq .` when installed | JSON parser/test comparison + exact stdout/stderr assertions |
| JS-02 | Report JSON schema/types are stable/documented; empty collections are arrays; warnings not interleaved with JSON | Schema/fixture regressions and stderr checks |
| JS-03 | Internal sender/receiver protocol JSON framing, byte stream and RPC handling remain compatible and are **not** reformatted for presentation | Protocol fixture, dispatcher/wrapper integration regression |
| SM-01 | Generic snapshot-manager `status` drops app-specific **display** but snapshot-create verified marker and source eligibility checks still run unchanged | Negative incomplete/invalid marker fixtures |
| SM-02 | Both hosts support `prune --dry-run` with identical selection to endpoint-specific pre-change plans, without mutation | Fixture comparison and before/after state hashes |
| SM-03 | Bounded prune retains endpoint-specific max validation, receiver gate, lock, UUID, readonly, parent/prior, hold, journal and recovery protections | Negative and positive disposable-fixture tests; no production deletion |
| SM-04 | Receiver `create`, source-only hold and unbounded deletion never become available accidentally | Negative endpoint-mode tests |
| ST-01 | Any `.simple-*` state migration is guarded, reversible, preserves parent/prior identity and file modes; or its exception is documented | Old/new hash and identity read-back, rollback proof or exception decision |
| OP-01 | Read-only commands make no snapshot, marker, parent, journal, service or timer changes | Before/after state and read-only fixture evidence |
| OP-02 | Installation and rollback keep accepted retention, calendar, max deletes and backups intact | Before/after config/unit inventory and protected snapshot read-back |
| OP-03 | Source regressions, controlled integration tests and Ansible checks pass; repeat only affected failures | Captured consolidated test report with explicit PASS/FAIL |
| OP-04 | Relevant code and documentation published to the proper repositories; all feature evidence stored under this Diaries feature | Commit/revision manifest, final acceptance report and closure record |

## Minimum final evidence summary

The final report must explicitly identify:

1. The old and new command/installed unit mapping, with **no duplicate active timers** and all normal callers updated.
2. The exact contents/exclusions of `diaries-backup-status` and both `btrfs-backup-status` host modes.
3. Representative formatted tables and JSON parsed successfully, including failures and empty lists.
4. Agreed-parent and prior identities, source/receiver retention safeguards and 0041 privilege boundary unchanged or safely migrated with recorded hashes/read-back.
5. Exact before/after source and deployment revisions, regression outcomes, schedule/max-delete preservation, rollback result/readiness and formal operator acceptance.

**Explicitly excluded as routine evidence:** production destructive prune, root snapshot removal, full backup restore, rebootstrap or duplicate live replication of a previously accepted transfer. If genuinely necessary for a newly changed behaviour, get specific approval and document recovery implications first.
