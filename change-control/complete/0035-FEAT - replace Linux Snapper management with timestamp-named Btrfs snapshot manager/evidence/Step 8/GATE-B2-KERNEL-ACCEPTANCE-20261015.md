# 0035-FEAT Step 8 — Gate B2 kernel evidence and next controlled test

**15 October 2026. Step 8 OPEN.** This addendum records the actual `mango` disposable loopback execution; it does not supersede the earlier Gate A/B1 and offline B2 evidence.

## Confirmed Gate B2 kernel checks (executed, PASS)

Log uploaded as `note(20261015-101627).txt`, from `verify-gate-b2-btrfs-loopback.sh --run-disposable` on `mango`:

1. Full kernel Btrfs send/receive, payload and read-only/received UUID — PASS.
2. Truncated full stream rejected; accepted baseline remained — PASS.
3. Incremental send/receive with valid parent, payload and read-only properties — PASS.
4. Missing parent on **third independent** Btrfs loopback filesystem rejected — PASS.
5. Truncated incremental rejected; accepted incremental remained — PASS.

The first run's `wrong-parent` directory was on the same Btrfs filesystem as the accepted parent, so Btrfs could resolve the parent. That failure was an **invalid test design**, fixed by using a separate third filesystem. Do not record the first run as a product defect or as a passing missing-parent test.

## Additional disposable kernel ENOSPC harness (prepared, NOT RUN)

Playbooks companion: `verification/0035-step8/verify-gate-b2-enospc-loopback.sh` and `README-GATE-B2-ENOSPC.md`. The harness creates its own independent filesystems, establishes a read-only accepted baseline, forces actual ENOSPC in the disposable receiver, requires a new receive to fail, and checks existing accepted data before and after space recovery. Evidence remains **PENDING** until the resulting log passes. A real Btrfs ENOSPC failure does **not** itself prove the production receiver's receipt failure path; that is currently covered by offline fault injection only.

## 0034 recovery evidence reconciliation

The 0034 complete feature README records successful disposable off-site restore Gates A–D, using production schema-2 backup `20261015-003023Z` and accepted native receipt `20261015-030004Z`. The bundled source contains that closure summary but **not the full Gate A–D execution transcripts**. Classification: **previously accepted via 0034, not independently revalidated** in Step 8. Do not claim a new restore has been performed. The latest Gate B1 `show`/`path` checks identify matching manifest hashes on `mars` and `pluto`, but do not hash the entire dataset or perform a restore.

## Outstanding gates

- Real SSH transport drop and lost acknowledgement on an isolated host pair: **not executed**. Existing offline tests exercise receipt/acknowledgement decision logic, not real SSH.
- Actual ENOSPC kernel harness: **prepared, not executed**.
- Production-receiver independent receipt persistence during real kernel ENOSPC: **not tested**; avoid running fixed-path receiver against disposable volumes.
- Full manifest verifier / repeat disposable schema-2 recovery: **not rerun**; 0034 acceptance summary inherited.
- Stream byte counts and receiver disk allocation: **not measured**.

**Do not run destructive tests or interrupt production `mars` → `backup`. Step 8 remains OPEN.**
