# 0028 Step 4 — final closure handoff (24 November 2026)

**Status: OPEN; feature remains `change-control/in-progress/`.** Step 3 was owner-accepted and closed 24 November 2026. This handoff does **not** request repeated migration, restore, production deployment or expensive GUI rehearsal.

## Accepted result to carry forward

The production 71-conversion apply and database postflight passed; responder startup synchronisation republished migrated IMAGE fragment records, Editor confirmed a retained Marquee and Reader confirmed image/transcription rendering. See `STEP3-PRODUCTION-ACCEPTANCE-20261124.md` and the two Step 3 screenshot files.

## Remaining Step 4 documentation and acceptance work

1. Reconcile the frozen 0022/0024/0028 manifest/decision identities, production journal and postflight record in the private feature evidence. Report verified completeness explicitly; distinguish confirmed counts from missing evidence.
2. Preserve **Fragment 1564 — DEFER** as a named outstanding compatibility case. Record why it remains deferred, its current source/current-version status and the precise constraints it imposes on 0029; do not assert that every legacy inline-image fragment has been migrated.
3. Record the exact production client/responder/web image versions, Git parent/submodule commits, staged migration JAR digest, manifest/plan/approval hashes and evidence retention locations. Previously observed client `0.0.9-build-79` and responder `0.0.9-build-86` in screenshots/logs are observations, not a full fresh deployment inventory.
4. Update long-lived responder/Editor/Reader operating documentation only where migration behaviour changed. Retain usable production rollback identities/instructions; any destructive restore requires separate explicit approval.
5. Review the exposed authentication credentials/tokens in the production responder log. Ensure committed evidence is redacted and deal with credential rotation/session revocation and the logging defect separately.
6. Produce a final acceptance matrix with actual evidence for each test. A successful `Synchronise - synchronise: ok` is evidence of the startup pass; it does not independently demonstrate a complete 71/71 retained-topic diff. Mark such narrower verification accurately.
7. Verify local Git status and submodule heads before any commits. Preserve unrelated uncommitted work; commit submodule implementation separately and update parent pin where applicable.
8. Obtain **explicit owner approval of formal feature closure** before marking Step 4 CLOSED or moving `0028-FEAT` to `change-control/complete/`.

## Execution policy

No production re-apply or restore is required for this documentation handoff. Retain Step 3 private logs/receipts in the feature directory; keep portable ZIPs free of raw authentication material.
