# 0036-FEAT Step 8 — Gate D unattended acceptance

**State: OPEN — evidence collection implemented, unattended acceptance not yet established.**

Gate C was formally closed on 2026-10-16. Its fixed capture (`20261016-152236Z`) and immutable snapshot (`20261016-153727Z`) are **manual cutover evidence, not unattended cycles**.

Gate D acceptance requires two independent, timer-triggered production capture → guarded receive → eligible read-only Btrfs snapshot chains, plus a fresh off-site received snapshot and successful receipt. Preserve the legacy rollback aliases and generations. The first two expected unattended cycle dates are 2026-10-17 and 2026-10-18 UTC, subject to observed runtime evidence; check receipt after the next eligible native push. No synthetic marker, receipt or extra full restore is required.

## Evidence collection

Use `playbooks/verification/0036-gate-d/collect-gate-d.sh` from `mango`. Its README gives commands and checks. Collector is read-only against hosts; stored evidence may contain path or operational metadata and should be reviewed before sharing. A command exit code of zero is not proof of application-level acceptance. No production process was run or checked by this documentation change.

## Acceptance ledger (fill using observed evidence)

| Criterion | Cycle A | Cycle B | Decision |
|---|---|---|---|
| Scheduled capture UTC time and exit 0 | Pending | Pending | OPEN |
| Distinct verified production backup ID | Pending | Pending | OPEN |
| Scheduled guarded fixed receive, matching ID | Pending | Pending | OPEN |
| Read-only `@data` snapshot with matching manifest | Pending | Pending | OPEN |
| New off-site Btrfs received snapshot and successful receipt | Pending | Pending/if later push | OPEN |
| No legacy fallback or unsafe failure | Pending | Pending | OPEN |

**No minimum quantitative transfer-savings threshold** is imposed. Do not close Gate D on the basis of the prior accepted 0034/0035 receipt, source compatibility tests, current mutable directory alone, or the Gate C manual snapshots.

**Formal closure decision: DEFERRED.** Gate D and Step 8 remain open; Gate E legacy retirement is not authorised.
