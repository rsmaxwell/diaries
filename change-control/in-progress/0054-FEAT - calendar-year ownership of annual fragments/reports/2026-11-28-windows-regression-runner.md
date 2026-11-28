# 0054 Step 2 — Windows regression runner and test compilation correction

Date: 2026-11-28

## Evidence and findings

- User confirmed deletion of development test EPILOGUE fragments 2355 and 2356, absent from Reader.
- User confirmed DATED fragment Save failure with responder stopped and successful retry after restart.
- Responder log: startup `synchronise: ok`, followed by Paho `CommsSender` NullPointerException for ephemeral `syncronise-sub-*` subscriber in `ClientState.get` (`pendingFlows == null`); normal responder and RPC listener connected afterwards. Nonfatal for this run; investigate if repeatable. This report does not certify the exception fixed.
- First Angular regression attempt did not execute tests: TypeScript TS2345 in fragment-reorder.service.spec.ts line 38 (`number | null` given to `Expected<number>`).

## Changes

- New Windows batch runner `diaries-client/scripts/windows/regression-tests.bat`: invokes ChromeHeadless Angular tests and `npm run build` from its own resolved client root; stops and reports nonzero status on failure.
- Regression assertion changed to explicit `toBeNull()` for annual fragments and `toBe(1)` for DATED fragments.
- Obsolete initial Bash runner `diaries-client/scripts/regression-tests.sh` should be removed after package application, if present; this ZIP does not automatically delete user files.

## Pending

Run the Windows batch runner and retain its output in the 0054 evidence directory. Step 2 remains OPEN until regression tests pass and remaining checks accepted.
