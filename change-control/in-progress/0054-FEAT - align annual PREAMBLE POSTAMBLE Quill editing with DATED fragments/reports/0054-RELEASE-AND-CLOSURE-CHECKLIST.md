# 0054-FEAT — Release and closure checklist

**Status: OPEN.** This checklist supplements, but does not replace, the acceptance gates in `IMPLEMENTATION-STEPS.md`.

- [x] Development Angular final verification script reported PASS (27 Nov 2026).
- [x] Reader formatting regression tests and `installDist` passed (27 Nov 2026).
- [x] Owner reported browser formatting, hyperlink and paste/drop acceptance.
- [x] Cross-diary design consideration deferred and documented.
- [ ] Review full final logs and exact Git revisions in existing `evidence/step-3-final-verification/`.
- [ ] Confirm all feature changes are committed appropriately in Client and Reader submodules and parent pins the intended revisions; avoid clobbering other work.
- [ ] Owner explicitly approves production publication.
- [ ] Deploy through the standard pipeline; retain image tags, revisions, receipts and rollback versions under the feature directory.
- [ ] Run and capture production browser smoke and log checks.
- [ ] Owner explicitly accepts the production result and approves formal closure.
- [ ] Mark final gate CLOSED and move the feature directory to `change-control/complete/`.
