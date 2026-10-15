# 0035-FEAT Step 8 — Gate B2 ENOSPC and transport-failure evidence

**Status: ACCEPTED for actual kernel-receive ENOSPC; transport and receipt-publication tests implemented, live execution pending. Step 8 OPEN.**

## Actual ENOSPC capture (15 October 2026)

Operator output from `mango` running `verify-gate-b2-enospc-loopback.sh --run-disposable`:

- PASS: actual Btrfs ENOSPC on disposable receiver
- PASS: previously accepted baseline remains readable and read-only under ENOSPC
- PASS: attempted new receive not accepted; prior baseline intact
- PASS: previously accepted baseline survives ENOSPC recovery

The complete operator transcript is included as `gate-b2-enospc-mango-20261015.txt`.

**Scope limitation:** this was an ENOSPC condition during Btrfs receive, not ENOSPC during receiver receipt-file publication.

## Additional disposable acceptance tooling

`verification/0035-step8/verify-gate-b2-transport-faults.py` injects transport return codes, a missing receipt acknowledgement and receipt-publication `ENOSPC` directly into the existing sender/receiver modules. It is an *offline code-path test*. Do not label it a real SSH disconnect or a real disk-fill receipt failure. The runtime result must be attached before these checks are marked PASS in this document.

## Inherited restore evidence

The 0034 feature closure reports disposable Gates A–D were accepted. The underlying restore transcripts are not included in the source bundle used for this update. Keep this as inherited acceptance, not independent 0035 re-verification.

## Outstanding for full Step 8 closure

- Execute and capture the new transport/receipt fault-injection harness on `mango`.
- Determine whether a real SSH disconnect / lost acknowledgement on isolated endpoints needs explicit demonstration.
- Decide whether kernel ENOSPC during receipt publication requires separate isolated testing (distinct from actual receive ENOSPC and simulated receipt-publication failure).
- Reconcile the original 0034 schema-2 disposable restore transcripts or explicitly accept the closure record as inherited evidence.

## Transport and receipt-publication fault-injection capture (15 October 2026)

**ACCEPTED — five code-path fault-injection scenarios passed on `mango`.** The operator transcript is `gate-b2-transport-mango-20261015.txt`.

1. Simulated SSH receive failure: source candidate and incremental parent remained pinned — PASS.
2. Simulated sender broken pipe: candidate and parent remained pinned — PASS.
3. Stream success but absent independently visible receiver acknowledgement: pins remained retained — PASS.
4. Independently verifiable accepted receipt: prior parent became eligible for release — PASS.
5. Injected `ENOSPC` during atomic receipt publication: previous accepted receipt remained intact and no new receipt was accepted — PASS.

The run concluded `GATE B2 isolated transport/acknowledgement and receipt-publication fault injection PASS`.

These are isolated injections into the real sender/receiver Python code, **not** observed network disconnects or Btrfs receipt-file exhaustion. This distinction is a closure constraint.

## Acceptance disposition / outstanding scope (15 October 2026)

| Scenario | Evidence | Disposition |
| --- | --- | --- |
| Live retention, receipt lineage and protected source | Gate A three-host capture | PASS |
| `show` and `path` restore-source selection | Gate B1 `mars`/`pluto` capture | PASS; full hashes not claimed |
| Retention, parent/UUID, duplicate and publication-failure logic | Twelve offline contract tests | PASS, simulated |
| Kernel full and incremental send/receive; truncated streams; missing parent | Five disposable Btrfs tests | PASS, disposable |
| Kernel receiver filesystem exhaustion and preservation of accepted baseline | Four ENOSPC checks | PASS, disposable |
| Simulated transport failures, missing acknowledgement, receipt-publication ENOSPC | Five `mango` code-path scenarios above | PASS, injected |
| Real SSH session loss or lost acknowledgement across isolated endpoints | No matching transcript | NOT TESTED — defer only with explicit risk acceptance, or implement test before final sign-off |
| Real `ENOSPC` while writing the independent receipt file | Only injected error; kernel receive ENOSPC separately proven | NOT TESTED — defer only with explicit risk acceptance, or implement isolated receipt-filesystem test |
| Disposable schema-2 restoration from received dataset | 0034 feature closure records accepted Gates A–D; primary transcripts not available in examined sources | INHERITED 0034 ACCEPTANCE — not independently reverified for 0035 |
| Quantitative native stream sizes and receiver storage allocation | No measurements in this Gate B2 transcript | NOT MEASURED — retain for final evidence review |

**Decision:** retain 0035 Step 8 as **OPEN**. The code-path failure scenarios can be accepted now; neither the absence of live SSH/receipt-filesystem tests nor the missing primary 0034 recovery transcripts is silently waived. A later explicit approval must determine whether each remaining test is required or formally deferred. This evidence update does not authorize transfers, snapshot deletion, timer changes or modifications to the production receiver.
