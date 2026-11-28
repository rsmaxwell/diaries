# 0054 — Step 2 development acceptance and Step 3 handoff

**Date:** 2026-11-28  
**Step 2:** CLOSED (development implementation gate only)  
**Step 3:** OPEN  
**Feature:** IN PROGRESS; **production cutover has not been authorised or evidenced**.

## Accepted browser evidence (user reported)

- PREAMBLE/EPILOGUE editor Save works; when the development responder is stopped, an RPC failure produces temporary footer and persistent inline errors. The unsaved Quill draft is preserved. Restarting responder and pressing Save succeeds, clears errors and updates the Reader.
- DATED editor Save failure/retry after deliberately stopping and restarting responder succeeds; retained draft persists through failure.
- Both the DATED Day Reader and annual PREAMBLE/EPILOGUE lists reorder using CDK drag handles; both edited orders appear in the Reader after the shared `FragmentReorderService` refactoring.
- Temporary test EPILOGUE fragments **2355 and 2356** were deleted; the user confirmed disappearance in the Reader. (Prior temporary IDs in unit-test fixtures do not mean live records remain.)

## Consolidated Angular evidence

- Source: `note(20261128-114111).txt`, copied verbatim into `evidence/step-2/windows-angular-regression-20261128-114111.txt`.
- Windows Command Prompt: `diaries-client\scripts\windows\regression-tests.bat`.
- Karma/ChromeHeadless: `TOTAL: 289 SUCCESS`; `PASS: Angular unit tests`.
- Angular `npm run build`: successful; output `diaries-client/dist/diaries-client`.
- Batch completion: `PASS: All Diaries client regression checks`.
- Synthetic `RpcError` warnings in expected-failure test cases did not cause test failure. Prior annual own-property and DATED field-order regressions were fixed and the rerun passed.

## Remaining work moved into Step 3 (not accepted here)

1. Verify current Windows parent/submodule revisions and working-tree state before executing repository-based Java tests. Run responder and Reader suites/builds, retaining logs. Angular tests already accepted; do not rerun without affected changes.
2. Verify local PostgreSQL annual/dated counts and ID/content fidelity, the feature-local SQL migration audit and idempotency, and MQTT retained canonical year-only topics plus obsolete-topic tombstones across responder restart/replay. Preserve exact evidence rather than inferring from browser views.
3. Check annual-only year and empty physical Diary editing, shared annual collection from two physical Diaries, old physical Reader links and fragment links against the agreed 0054 contract. Accept previously completed checks rather than repeating them without cause.
4. Record the responder-start Paho `NullPointerException` in temporary subscriber shutdown separately: restart and RPC recovered, but the underlying exception has not been proven fixed.
5. Prepare production pre-cutover backup/manifest, deployed image and Git revision receipts, coordinated client/responder/Reader rollout and rollback evidence. **Obtain explicit authorisation before any production migration or deployment.**
6. Document the accepted final year-owned payload/topics/URL compatibility for 0053. Keep 0054 in progress until formal feature closure.

## Scope and decision

This document closes the **Step 2 development implementation** acceptance based on reported browser verification and successful consolidated Angular regression. It does not claim that all Step 3 or full-feature gates have passed, nor that production is migrated.
