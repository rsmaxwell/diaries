# 0029 Step 2 — Annual sequence RPC and deletion routing (candidate)

## Evidence and intent

The approved hybrid model has independent `(diaryId, year, placement)` editorial sequences. The earlier annual normaliser candidate implemented `normaliseAnnual`, but `DeleteFragment` and the `normaliseFragments` RPC still called `normaliseDate` unconditionally. This overlay routes year-owned fragments through the annual normaliser and preserves default dated behaviour.

## Changes

- `DeleteFragment`: after deleting a PREAMBLE/POSTAMBLE fragment, normalise only that Diary/year/placement, without perturbing 1 January or other dated fragments. DATED and legacy-null placement keep date normalisation. The existing transaction, retained-topic removal, and survivor publication are preserved.
- `NormaliseFragments`: accepts optional `placement`. When absent, retains the old year/month/day RPC contract. For PREAMBLE or POSTAMBLE requires positive `diaryId` and `year`, using independent annual normalisation; rejects invalid parameters before opening the transaction.

## Checks and integration

- Source-level brace balance and annual/date call-site checks passed.
- Full Java compilation and automated tests **not executed** in this environment.
- NOT DEPLOYABLE ALONE: overlay onto the consolidated Step 2 source candidate and annual-sequence-isolation package. Database migration and full cross-component acceptance remain pending.
- Consolidated verification must cover deletion and renumbering in both annual groups, ordinary date RPC compatibility, missing/invalid diaryId/placement, stale-version conflict rollback, and MQTT publication of re-numbered survivors.
- Before running the database migration, reconcile the 49 development-only 0028 legacy records and capture production backup evidence.
