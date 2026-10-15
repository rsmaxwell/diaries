# 0035-FEAT — Step 8 formal closure (2026-10-15)

**Decision: CLOSED.** Scope: *Step 8 — Retention, restore and failure acceptance*. This is **not** closure of 0035-FEAT overall or permission to change production timers, prune protected snapshots, reseed a receiver or delete historical data.

## Verified acceptance evidence

| Gate | Decision | Evidence / limitation |
|---|---|---|
| A — non-destructive three-host state | PASS | 52 paired source sets at capture, dry-run retaining 52/52, checkpoint and replication pins, eight accepted read-only receiver receipts/UUID chains, disabled backup-side timers, ext4 no-op; time-specific inventory |
| B1 — history resolution | PASS | `gate-b1-20261015-100244.txt`: historic and current snapshot/live restore paths, `production` manifest identity; no full-content hash or restore claimed |
| B2 — offline contract | PASS | 12 checks recorded in `note(20261015-100818).txt`: receiver/parent/receipt and retention policy |
| B2 — kernel Btrfs loopback | PASS | 5 corrected checks, `note(20261015-101627).txt`; earlier same-filesystem missing-parent test discarded |
| B2 — real Btrfs receive ENOSPC | PASS | `gate-b2-enospc-mango-20261015.txt`: received baseline survives candidate failure |
| B2 — transport/pin/receipt fault injection | PASS | `gate-b2-transport-mango-20261015.txt`: five scenarios, acceptance required before release of parent protection |
| B2 — isolated real SSH disconnect | PASS | `gate-b2-ssh-disconnect-mango-20261015.txt`: interruption before acknowledgement; not production sender over that daemon |
| B2 — real receipt-publication ENOSPC | PASS | `gate-b2-receipt-enospc-mango-20261015.txt`: old receipt intact, new receipt absent, temporary state cleaned |

Consult `FINAL-EVIDENCE-RECONCILIATION-20261015.md` for detailed evidence provenance and limitations.

## Explicit owner acceptance decisions

1. **Inherited 0034 disposable recovery accepted.** The formally accepted 0034 Gates A–D (backup generation `20261015-003023Z`, source snapshot `20261015-030004Z`) are sufficient; **no additional complete restore is required** for Step 8. Underlying 0034 original Gates A–D transcripts were not independently available/re-examined in this Step 8 review. Do not claim a new 0035 restore or independently reverified database/files content.
2. **Correctness evidence accepted.** Existing Gate A/B1/B2 tests provide sufficient assurance for Step 8's intended retention, historical location, failure-safety and restore-compatibility decisions within the recorded test boundaries.
3. **Quantitative measurements excluded.** Native stream sizes, transfer duration/throughput, physical allocation, capacity and performance benchmarking are **out of scope** for Step 8 by explicit owner choice; not outstanding closure blockers and no numeric efficiency claims are made. Any earlier Step 6/8 references to these as required acceptance are superseded **for Step 8 only**.
4. **Complementary tests accepted instead of one combined integration run.** Actual isolated SSH disconnect, sender protection/acknowledgement injection, real kernel receive interruption, and receipt ENOSPC have been evidenced separately. The owner explicitly accepts these as adequate, with **no further end-to-end run required**. They do not prove a single full production-equivalent failure exercise occurred.
5. **Retention test boundary retained.** GFS bucket selection was tested offline; live pruning was examined via dry-run and protection checks. No production destructive multi-bucket prune was performed or authorised as part of this closure. Legacy Snapper namespace and accepted/pinned snapshots must remain protected. This known limitation does not block Step 8 under the accepted non-destructive scope.

## Closure outcome

**0035-FEAT Step 8: CLOSED on 2026-10-15.** The three previously unresolved sign-off questions (inherited restore, quantitative metrics, combined failure test) have explicit decisions. No source runtime changes, Docker image rebuild, release, host deployment, activation, off-site reseed or destructive operation is required or authorised by this documentation-only closure. **Step 9 and feature-wide closure remain separate.**
