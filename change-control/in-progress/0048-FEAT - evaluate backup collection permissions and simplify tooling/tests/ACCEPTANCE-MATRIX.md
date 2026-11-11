# 0048 — Acceptance matrix

**All checks are NOT STARTED / BLOCKED until 0046 and 0047 are CLOSED.** Update each line with actual test commands, evidence paths, source SHA and PASS/FAIL. A planned command does not count as a result.

| Gate | Acceptance criterion | Status | Evidence |
|---|---|---|---|
| P0 | Formal 0046 and 0047 closure and published receipts verified | BLOCKED | Pending |
| A1 | Actual Windows Diaries/submodule and `mango` Playbooks baseline, inventory source and rollback SHA captured | OPEN | Pending |
| A2 | Complete affected path list (at least 14 historical mode entries), consumers, ownership, ACLs, security and role order audited | OPEN | Pending |
| B1 | Genuine fresh checkout tested **without** 0047 mode restoration or copied filesystem metadata | OPEN | Pending |
| B2 | Required read/write/traverse/execute access works; potential group-write removal and other-traverse exposure assessed per path | OPEN | Pending |
| B3 | Full Ansible create-directory + rsync sequence tested twice without permission oscillation | OPEN | Pending |
| C1 | Single coherent reviewed Playbooks change; no rsync `--chmod`/`--no-perms`; focused regression and syntax PASS | OPEN | Pending |
| C2 | Retire-or-retain decision made for `source-modes.json`, restoration preflight, regression and active docs; historical 0047 evidence preserved | OPEN | Pending |
| D1 | Controlled targeted deployment has no unapproved changes, errors or unreachable hosts | OPEN | Pending |
| D2 | Repeated production deployment yields `changed=0`, `failed=0`, `unreachable=0` | OPEN | Pending |
| D3 | Installed byte content, permissions, ownership, ACLs and approved access checks reconciled; timer/locks/pins/read-only health unchanged | OPEN | Pending |
| D4 | No destructive Btrfs exercise, data delete, credentials leak or unrelated system mutation | OPEN | Pending |
| D5 | Published Playbooks and Diaries revision receipts, rollback readiness, formal gate acceptance | OPEN | Pending |
| CLOSE | Change control fully accepted, moved to `complete/`, closure commit pushed | OPEN | Pending |

**Decision rule:** If special mode handling proves necessary, the feature may still close with a documented, minimized retained mechanism and proof of fresh-clone reproducibility. Closure does not require tool removal regardless of evidence.
