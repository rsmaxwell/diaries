# 0051 Step 2 — persistence, responder and retained contracts

**Status: Verification PASSED on 20 November 2026; formal owner acceptance pending.**

## Final verification evidence

- Windows Cygwin `./gradlew --no-daemon :diaries-responder:test` completed **BUILD SUCCESSFUL** at approximately 11:43 UTC on the third run. The first two attempts failed (two missing/incorrect test-source types, then one outdated IMAGE/Marquee expectation); all corrected without requiring production deployment.
- Frozen 0024 fixture `diaries-development-20260912-203528.dump` was verified against SHA-256 `fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86`.
- Initial isolated test run `3e52218d5880` failed before 0051 migration because 0025 preflight and migration were issued as separate `psql` sessions. Corrected runner preserves the accepted single-session sequence; original failed run is preserved.
- **Successful isolated run `c1759df22f5f`**, 2026-11-20 12:25:17Z–12:27:02Z, with two actual PostgreSQL/MQTT integration JUnit tests, 0 failures, 0 errors, 0 skipped; migration twice, schema assertion and existing-value hashes all passed.
- Owner inspected `result.json`, `ImageWiringIntegrationTest.xml` and checked `SHA256SUMS.txt` in the private evidence directory; all recorded checksums matched.

See [the full acceptance review](STEP2-ACCEPTANCE-REVIEW-20261120.md) for exact receipts, scope and outstanding later-stage checks.

## Private evidence retained in Windows working copy

`evidence/Step 2/private/step2-responder-tests.log`

`evidence/Step 2/private/step2-responder-tests-rerun.log`

`evidence/Step 2/private/step2-responder-tests-third-run.log`

`evidence/Step 2/private/isolated-integration-3e52218d5880/`

`evidence/Step 2/private/isolated-integration-c1759df22f5f/`

These ignored logs and receipts are not included in publicly distributed ZIP packages. Preserve them as evidence; do not rerun accepted tests merely to regenerate output.

## Implemented scope

- Nullable `fragment.image_link_url VARCHAR(4096)` and repeatable additive migration; persistence and native DTO mappings.
- URL set/preserve/explicit-clear contract, HTTP(S) URL validation, independent extension-write gate disabled by default.
- IMAGE Fragments may carry one same-Page Marquee; MARQUEE compatibility and catalogue Image independence retained.
- RPC and retained canonical/date/Marquee publications, replay, removal tombstones and denied-operation preservation.
- Java synthetic regression suite and two disposable DB/MQTT integration cases.

## Scope boundary and remaining steps

This validates the **Step 2 responder/persistence** acceptance gate on the tested working copy, not the entire feature. It does not establish full client/web behaviour or production rollout acceptance. Step 3 implements both UIs and their tests; Step 4 addresses 0028 handoff, compatible rollout and production E2E checks. No live schema migration, production activation, or production legacy conversion is authorised by this record.

The static Step 1 source-characterisation test expects old behaviour and must not be rerun against Step 2 as an acceptance test. Feature-wide acceptance remains OPEN; 0028 remains paused.

The source bundles cannot establish current working-tree byte identity or Git commit IDs. Owner-provided submodule revision during implementation: responder `bd65d08435c0f5d240337cd6479cb41befe4d8c1` with uncommitted Step 2 modifications; preserve unrelated 0028/0029 edits.

Formal closure is recorded in [STEP2-CLOSURE-20261120.md](STEP2-CLOSURE-20261120.md). The earlier evidence, review and manifest remain as historical records.
