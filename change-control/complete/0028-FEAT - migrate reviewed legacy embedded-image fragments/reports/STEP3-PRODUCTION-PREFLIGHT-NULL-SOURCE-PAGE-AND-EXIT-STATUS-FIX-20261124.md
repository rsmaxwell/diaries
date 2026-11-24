# 0028 Step 3 — production preflight false drift and false PASS correction (24 November 2026)

## Incident / evidence

The Windows Cygwin production-readiness run (private evidence `evidence/Step 3/private/20261124T094843Z-production-freshness`) completed an actual read-only production inventory (2,331 Fragments, 72 legacy occurrences), checked 70/70 catalogue files, observed zero locks and reported `SOURCE PREFLIGHT: BLOCKED_SOURCE_DRIFT` with exactly 50 `FRAGMENT_ID_VERSION_PAGE_TYPE_DRIFT` Fragment IDs. It then incorrectly printed `PASS` and exited successfully. **Do not accept that run as a production migration gate.**

All 50 IDs flagged in that log have `page_id: null` in the earlier 21 November frozen production inventory, including 84, 598, 606 and explicitly deferred 1564. The Step 1 prepared CSV correctly writes SQL `NULL` Page ownership as an empty `page_id` field. The first Step 3 comparator called integer conversion on both values; `int(None)` / `int("")` fails, causing a false drift even when both represent an unassigned source Page. This is a **code-level explanation**, not proof that no genuine production change has occurred. The new live run must decide that.

The wrapper also used `( ... ) && success || failure`. In Bash this suppresses `errexit` for the compound command, so a nonzero comparator result did not stop subsequent PASS messages. Historical evidence is retained; nothing is overwritten or deleted.

## Correction

1. `tools/0028-step3-freshness.py`: add a dedicated `same_nullable_integer()` for **source `page_id` only**. Match Python/JSON null to a blank manifest field, never to integer zero or another Page ID. Keep strict version, type, HTML, Image ID, identity, date/order, source occurrence, link, Marquee, catalogue, file hash and lock checks.
2. `tools/verify-0028-step3-production-freshness.sh`: make the fail-fast subshell a standalone command, capture its status afterwards, and print overall PASS only when the subshell succeeded. Continue to preserve the invoking interactive Cygwin shell.
3. `tests/test_step3_freshness.py`: add null Page acceptance and negative drift cases, including the deferred Fragment shape; exercise the actual wrapper result gate on synthetic success and failure. **23 regression tests pass offline.**

## Follow-up / acceptance

Apply the small ZIP in the Windows Diaries parent checkout, then rerun the **same read-only** production preflight. The new evidence run must show both `SOURCE PREFLIGHT: PASS_SOURCE_FRESHNESS` and `0028 FRESH SOURCE PREFLIGHT: PASS` and contain no blocker list before technical freshness is accepted. If it reports other blockers, stop and inspect the private `FRESH-PRODUCTION-PREFLIGHT.json`; never bypass checks or regenerate manifest values merely to force PASS.

Still **OPEN** after a fresh source PASS: Step 1 formal owner acceptance / historical 0022–0024 evidence limitation, runtime compatibility, stopping writers, fresh recoverable production backup/rollback verification, and separate explicit authorisation to apply. The corrected script performs no production writes, service restarts, MQTT operations or snapshot changes.
