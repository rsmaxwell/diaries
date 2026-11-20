# 0051 Step 3 — RPC sequence type correction (20 November 2026)

## Observed evidence

- Original run: `integrated-20261120T135937Z-1138028d` (FAILED).
- Candidate responder/web JARs built and disposable PostgreSQL/MQTT/browser test reached the four-IMAGE scenarios.
- Retained snapshot acknowledged an independent barrier: 2,334 Fragment topics and one Image topic.
- First `updateFragment` returned status 500 and `unexpected type for key: sequence, String`.

## Cause and correction

`fragmentRow()` explicitly selected `sequence::text AS sequence` from PostgreSQL. The generic `rows()` helper serialises with `json_agg` and parses JSON into JavaScript. Casting `sequence` to `text` therefore made the RPC request field a string. `UpdateFragment` calls `Utilities.getBigDecimal(args, "sequence")`, which correctly rejects strings.

Remove `::text` from this one fixture query. PostgreSQL `json_agg` serialises its `NUMERIC` column as a JSON number; add guards that assert the decoded value is a finite JavaScript number. Both normal edits and the rejected-unsafe-URL case use `fragmentRow()`, so the correction covers both request paths. Existing fixture sequences have four decimal places, matching `SequenceNumber.SCALE = 4`.

The responder and production code are **unchanged**. Do not weaken RPC type validation. The failed run remains historical evidence under `evidence/Step 3/private/`.

## Verification and acceptance

- Package: Node.js `--check`, static source assertions, ZIP integrity and SHA-256 verification.
- Windows runtime verification still required: rerun `verify-step3-isolated-ui.ps1` with the already configured PowerShell 7, Playwright `NODE_PATH` and the previously approved frozen fixture.
- Preserve all previous Step 1/2 and Step 3 unit-test evidence; no need to rerun those suites.
- **Step 3 OPEN** until the integrated test and separate Angular editor visual acceptance pass.
