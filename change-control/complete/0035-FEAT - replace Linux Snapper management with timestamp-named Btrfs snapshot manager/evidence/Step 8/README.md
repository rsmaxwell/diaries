# 0035-FEAT Step 8 — Retention, restore and failure acceptance

**Status (2026-10-15): CLOSED — Gate A, Gate B1 and controlled Gate B2 acceptance PASS within documented scope; final decisions authorised.**

Step 7 verified installed parity on mars/pluto/backup (all 6 tasks per host, changed=0); Step 6 verified eight received snapshots/receipts with matching UUIDs, and zero differences. These are baseline inputs, not proof of all Step 8 scenarios.

## Gate A — Live non-destructive inventory

Run `verification/0035-step8/verify-acceptance.yaml` from mango (instructions in Playbooks). Attach output to this evidence folder. It must validate snapshot pins/holds, receipt/UUID/parent chain, passive backup timers, and ext4 no-op.

## Gate B — Controlled acceptance matrix

| Criterion | Evidence / status |
|---|---|
| Current timestamp sets and newest-set safety | Step 5/7 dry-runs, 52 of 52 kept at capture; broader GFS boundary exercise pending |
| Protected checkpoint and replication parent | Steps 2, 5, 6 and 7 live capture; source regressions passed |
| Legacy Snapper namespace untouched | Steps 1, 2 and 7 baseline; inventory only |
| Historical backup ID to real restore path | Step 4 history list; `path`, `show`, `verify` live commands not evidenced |
| Disposable schema-2 restore | 0034 disposable recovery evidence requires exact citation and scope reconciliation |
| Storage pressure and SSH loss | controlled tests not yet evidenced |
| Interrupted full/incremental streams | production interruption not exercised; disposable simulation evidence pending |
| Duplicate receive and unknown/stale parent | native regression coverage (Step 6), controlled test evidence pending |
| Last accepted receiver remains usable | Step 3/6 receipts consistent; controlled failure/recovery demonstration pending |
| Stream sizes and allocated space | measured evidence not yet reconciled |

No destructive tests or host configuration modifications are authorised by Gate A. Preserve `/@data/backup`, received snapshots and all holds.

### Gate B2 kernel loopback harness (completed; historical heading updated)

See `GATE-B-RECONCILIATION-20261015.md` and Playbooks `verification/0035-step8/README-GATE-B.md`. The real isolated Btrfs tests PASSED; see `FINAL-EVIDENCE-RECONCILIATION-20261015.md` and `STEP-8-CLOSURE-20261015.md`. No production hosts or snapshots were modified by the disposable harness.

## Final reconciliation (2026-10-15)

See `FINAL-EVIDENCE-RECONCILIATION-20261015.md` for the audited matrix, two real-failure transcripts and outstanding sign-off decisions. Earlier provisional Gate B entries above are historical and superseded by the final matrix and `STEP-8-CLOSURE-20261015.md`. Step 8 is **CLOSED** within its documented scope; no destructive production operations are authorised.
