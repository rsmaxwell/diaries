# 0035-FEAT Step 8 — Gate B2 evidence decision record (15 October 2026)

**Decision: Gate B2 fault-injection evidence ACCEPTED; Step 8 remains OPEN.**

The operator executed `python3 verification/0035-step8/verify-gate-b2-transport-faults.py` on `mango`. Its five reported passes verify source replication pins on failed simulated SSH receive, simulated broken-pipe sender and missing independent acceptance; they also verify release of the old parent only after valid independent acceptance and preservation of the old receipt on injected receipt-publication `ENOSPC`.

Evidence files: `gate-b2-transport-mango-20261015.txt` and `GATE-B2-ENOSPC-AND-TRANSPORT-20261015.md`. Earlier Gate A, B1, offline, real Btrfs kernel, and real receive ENOSPC evidence are recorded separately under Step 8.

## Scenarios not accepted as newly demonstrated

- **Actual SSH disconnection / lost acknowledgement:** injection exercises error paths, but not a real broken network connection between isolated SSH endpoints.
- **Actual receipt-file ENOSPC:** injected write failure is separate from a real full filesystem at receipt publication. The Btrfs receive ENOSPC test does not cover this.
- **New disposable schema-2 restore:** 0034 closure attests to Gates A–D, but primary restore transcripts were unavailable in inspected source; record as inherited acceptance rather than a fresh execution.
- **Native transport bytes / on-disk allocation:** no new quantitative measurement supplied; retain as an explicit evidence gap if required for Step 8 acceptance.

## Sign-off choices for a subsequent decision

1. Run controlled tests on **fully disposable** SSH endpoints and receipt filesystem, or document explicit acceptance of their residual risk. Do not interrupt `mars` → `backup` production replication.
2. Locate and attach 0034 primary disposable recovery records if they are available; otherwise approve the scope of inherited 0034 closure evidence explicitly.
3. Reconcile native transport metrics if required by the published Step 8 acceptance criteria.
4. Only after those decisions, determine whether Step 8 can be marked CLOSED. Keep all historical Snapper snapshots, replication pins, receiver receipts, and production publications untouched.

No code or host deployment accompanies this documentation change; no Docker images need building.
