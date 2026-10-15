# 0035 Step 8 — Gate B2 SSH interruption and receipt ENOSPC acceptance

**Status (15 October 2026): IMPLEMENTED, LIVE DISPOSABLE EXECUTION PENDING; Step 8 OPEN.**

## Accepted evidence to date

- Gate A three-host live inventory: PASS, no changes.
- Gate B1 history `show`/`path`: PASS, on `mars` and `pluto`.
- 12 offline fault-injection contracts: PASS on `mango`.
- Five disposable kernel Btrfs send/receive checks: PASS on `mango` after corrected independent-filesystem missing-parent test.
- Four actual Btrfs receive ENOSPC checks: PASS on `mango`, preserving previous accepted baseline.
- Five transport/acknowledgement and simulated receipt-ENOSPC checks: PASS on `mango`, from `note(20261015-102748).txt`; no independent real SSH disconnection claimed.

## New isolated tests supplied (not yet executed)

| Scenario | Method | Current result |
|---|---|---|
| Actual SSH interruption | Temporary loopback-only sshd with short-lived credentials; kill SSH client before remote acknowledgement; assert no `ACCEPTED` | PENDING |
| Real receipt publication ENOSPC | Disposable Btrfs loopback filesystem; test production receiver's `atomic_receipt()` with redirected temporary `STATE`; retain existing receipt on actual ENOSPC | PENDING |

These complement, but do not replace, sender pin lifecycle regression and receiver validations. The SSH test establishes an actual transport drop without claiming end-to-end pin checks; the ENOSPC test exercises actual receipt-writer I/O but not the full production receiver CLI. Do not promote either to PASS before inspecting the test transcripts.

## Remaining Step 8 decisions

- Reconcile the 0034 Step 11.3 disposable off-site schema-2 restore primary transcripts if available; current 0034 closure summary is inherited evidence, not independently re-executed recovery.
- Assess quantitative Btrfs transfer size and disk allocation acceptance; no 0035 measured evidence yet.
- A deliberate production failure, production snapshot pruning or off-site receiver reinitialisation is **not authorised**.

Operator instructions: `verification/0035-step8/README-GATE-B2-ISOLATED.md` in the Playbooks patch. Store completed transcripts in Step 8 evidence after execution and reconcile before closure.
