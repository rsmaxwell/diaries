# 0050-FEAT — Formal closure decision

**Feature:** Expose Diaries backup history on Btrfs receiver
**Owner decision:** APPROVED for formal closure on 17 November 2026, explicitly in the Diaries project conversation.
**Closure state in this package:** APPROVED; committed CLOSED status and archive relocation take effect when `tools/close-0050-feature.sh` successfully publishes the resulting Diaries commit.
**Change-control owner:** Diaries parent Git repository.

## Accepted scope

- Both `diaries-backup-status` and `diaries-backup-history` are installed on `backup`, using the receiver's own `/@data/mars-received/@data/<timestamp>/` snapshots.
- Read-only `diaries_history` metadata is separated from the receiver snapshot manager's source-side gate (`verification.required=false` remains unchanged).
- Existing source CLI semantics, retained marker/manifest identity checking, warnings, conflicts, JSON and full schema-2 verification behaviour are preserved.
- Receiver-only backup histories are demonstrated in both nine-case fixtures and live independently retained backup inventories: **11** receiver-only backup identities versus 19 shared and 3 source-only.
- A live received `production/20261116-003112Z` backup in snapshot `20261116-150008Z` passed full schema-2 verification of **128 files**.
- The receiver playbook's final reapply was strictly idempotent: `ok=37 changed=0 unreachable=0 failed=0`.
- Applicable 0041/0049 and replication regressions and the fixed-directory correction tests were accepted. No new destructive transfer, pruning or restore was required.

## Accepted published revisions

| Repository | Published `main` revision |
| --- | --- |
| Playbooks | `b0063d455faf4b264504405f9db72ab21c692741` |
| Ansible-controller | `28e394b48ba91479b147452d70adb39ff3b84559` |
| Private inventory (unchanged) | `ebcce026723db37b9b53b76ba21903a351d48466` |
| Diaries evidence baseline (before archival) | `06ae009f2b840a9021045a9da3266d022ab6c65d` |

Published remote-SHA readbacks are preserved in verbatim terminal logs under `evidence/Step 4/` and the source test/deployment evidence under earlier steps. The final archival commit SHA will be output and verified by the closure helper; do not invent or pre-record it.

## Boundaries and retained follow-up

- The 11 receiver-only identities passed manifest/marker inventory checks. They were **not each subjected to separate full-content scanning**; full validation was performed on a selected real receiver backup, and disposable tamper tests passed.
- The feature is a host-local reader; it does not merge the two repositories into one query or change their retention policies.
- No destructive recovery test or transfer was required for this read-only feature. Established snapshot checkpoints and dedicated-service security remain unchanged.
- Existing historical failure logs and dated pending-status notes are retained unmodified; the final accepted evidence supersedes those intermediate observations.

**Decision:** Mark Steps 1–4 CLOSED and archive the entire feature directory to `change-control/complete/` when the guarded Diaries closure commit and GitHub push succeed. Formal closure requires the final successful published readback, not merely this approval document.
