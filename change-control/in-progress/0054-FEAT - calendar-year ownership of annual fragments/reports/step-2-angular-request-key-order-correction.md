# Step 2 — Angular request field-order regression correction

Date: 2026-11-28

## Evidence

Windows `diaries-client/scripts/windows/regression-tests.bat` ran 289 Karma/ChromeHeadless specs: 288 passed and one failed. `Fragment compatibility helpers keeps ordinary updateFragment requests free of Image identity fields` failed because `Object.keys(request)` returned `id,year,sequence,version,text,month,day` instead of the existing expected `id,year,month,day,sequence,version,text`. This followed the annual null-key correction. The annual null-date test passed.

## Correction

In `UpdateFragmentRequest`, declare all seven fields without runtime initialisation and assign them in the constructor's established order. This preserves DATED request property ordering, omits annual null month/day keys, and retains existing RPC semantics. No responder changes.

## Verification status

Source package prepared. Angular tests and build must be rerun on Windows; no pass asserted yet. Step 2 remains OPEN.
