# 0051 Step 2 — historical 0025 migration session correction

**Date:** 20 November 2026  
**Status:** Corrective package prepared; rerun OPEN  
**Affected run:** `isolated-integration-3e52218d5880`

## Evidence received

The owner's Windows Cygwin output reports `PASS: Frozen database backup verified`.
The disposable runner created its run-specific Step 2 evidence directory and
then reported:

```text
FAIL: docker exited 3; see 0025-migration.log.
psql:/tmp/0025-migration/002-add-fragment-image-reference.sql:4:
ERROR: Run 001-preflight.sql in the same session first
Result: FAILED
```

This is a harness sequencing failure, not evidence of an invalid backup or
application regression. The original 0025 preflight executes successfully, but
its `preflight_ok`, `preflight_integrity`, `preflight_database` and
`preflight_user` values are local to the `psql` process. The original runner
started a new `psql` process for each SQL file, discarding those values.
The earlier accepted 0025 `migration/tests/run-tests.ps1` instead executes
all three files with `-f ... -f ... -f ...` on **one** `psql` invocation.
The 0025 `002-add-fragment-image-reference.sql` also includes `003-postflight.sql`
inside its transaction; the final explicit `-f 003` verifies after COMMIT.

## Correction

- Use one `docker exec ... psql -X -v ON_ERROR_STOP=1` command for
  `001-preflight.sql`, `002-add-fragment-image-reference.sql` and
  `003-postflight.sql`, in that order, with log `0025-apply-session.log`.
- Verify the expected SHA-256 of the frozen 0024 fixture **inside the runner**
  before starting any containers, in addition to the caller's previous check.
- Keep the 0051 migration idempotency, row hashes, real PostgreSQL/MQTT tests,
  run-unique logs and cleanup unchanged.

## Acceptance boundary and next run

Apply the two amended documentation/runner files in the small correction ZIP,
then invoke the same feature-specific runner with the existing, verified dump.
The runner creates a **new** run-specific evidence directory and leaves the
failed run untouched. Inspect `result.json`, `0025-apply-session.log`, 0051 SQL
logs, JUnit XML and Docker cleanup evidence before accepting Step 2. Nothing
in the supplied terminal excerpt establishes whether cleanup succeeded; check
that original run's `result.json` if needed. Do not apply migrations to pluto.

The correction has been inspected against the source scripts; it has **not**
been executed against Docker/PostgreSQL/MQTT in the assistant environment.
**Step 2 remains OPEN**, and Step 1 remains CLOSED.
