# 0048 — Acceptance matrix (reconciled 13 November 2026)

**Disposition:** Technical acceptance PASS. Operator closure accepted; this record is included in the Diaries closure commit. Historical 0047 design failure is recorded, not repeated in the corrected production implementation.

| Gate | Acceptance criterion | Status | Supporting evidence |
|---|---|---|---|
| P0 | Formal 0046/0047 closure and published receipts verified | PASS | Step 1 read-only Git/closure logs; completed feature directories |
| A1 | Actual Windows Diaries/submodule, `mango` controller/inventory/Playbooks revisions and rollback SHA | PASS | `reports/STEP1-ACL-RECONCILIATION-20261112.md`; Step 1 logs; Step 3/4 publication and rollback receipts |
| A2 | 14-path modes, consumers, ownership, ACLs, ancestry and Ansible ordering reviewed | PASS | Step 1 report and `acl-and-access-*.txt` |
| B1 | Genuine fresh checkout without restoration | PASS | Step 2 clean-clone log at historical Playbooks `df68a0e` |
| B2 | Required reader/traversal/executor access and exposure assessed | PASS for reviewed scope | Step 1 ACL matrix, Step 3 read-only access checks, Step 4 installed ACL and ancestry checks |
| B3 | Full create-directory plus rsync sequence idempotent | PASS for corrected design | Historical failing `RUN2_CHANGED=2`; Step 3 `FRESH_RUN2_CHANGED=0`, `EXISTING-0750_RUN2_CHANGED=0`; Step 4 live second run `changed=0` |
| C1 | No synchronized-directory mode overrides; isolated cron/log `0750`, launcher `0744` preserved | PASS | Revised source preflight/syntax and Step 3/4 logs |
| C2 | Special restore dependency retired; 0047 historical evidence preserved | PASS | Published Playbooks `c510934`, controller pin `83cba34`, unchanged completed 0047 evidence |
| D1 | Live targeted deployment contains only approved changes | PASS | Step 4 corrected `deployment-*.txt`: preview/live `changed=2`, `failed=0`, `unreachable=0` |
| D2 | Second application is fully idempotent | PASS | Same Step 4 log: `changed=0`, no failed/unreachable tasks |
| D3 | Installed hashes, modes, ownership, ACLs, access, schedules and health reconciled | PASS for 0048 scope | Step 4 verifier checks nine hashes, 14 modes/owners, seven launchers, no extended/default ACL; `final-backup-health-*.txt` |
| D4 | No destructive Btrfs exercise, backup data, credential or unrelated sudo changes | PASS within captured 0048 scope | Source/deployment scripts and Step 4 logs; read-only health report |
| D5 | Published source/rollback receipts and formal evidence | PASS for Playbooks/controller and rollback; Diaries closure commit included in this publication | Publication log, fallback Playbooks `df68a0e`, Step 4 report |
| CLOSE | Operator accepts record, feature moved to `complete/`, closure commit pushed | ACCEPTED (publication subject to successful push) | `reports/0048-FEAT-CLOSURE-REVIEW-20261113.md` and final commit receipt |

**Residual observations, not new 0048 failures:** two stale Btrfs qgroups (`qgroups_status=ok`) belong to 0039-DEF; a pre-existing history-verification configuration limitation is tracked under 0035-FEAT. These remain distinct from the accepted permission implementation.
