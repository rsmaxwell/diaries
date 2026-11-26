# 0029-FEAT — Step 2 responder test contract corrections (25 November 2026)

## Evidence

The Windows `:diaries-responder:test` run compiled production and test Java successfully and executed 369 tests: 5 failures, 37 skipped. Angular `npm run build` passed. The reader still has 12 test failures in the preceding integration run.

## Changes

- Update the repository positional SQL fixture for newly inserted `diary_id` and `placement` columns, retaining explicit assertions that the subsequent type/image/lock fields remain aligned.
- Update the retained Fragment DTO field-set expectations to include `diaryId` and `placement`, retaining exact key-set checks.
- Change historical JSON `MARQUEE` expectations to the new canonical `TEXT` value.
- Update the legacy addFragment test to assert the derived Diary ID and DATED placement.

These are test corrections only. Production source, database and migration scripts are unchanged.

## Verification

Source-level consistency checked against `diaries-sources-20261125-171359.zip`. ZIP integrity checked. Not compiled/tested in the packaging environment. Re-run Windows Gradle tests to establish results.

## Outstanding

Reader twelve failures require detailed JUnit XML diagnostic output. Do not deploy or execute migration SQL.
