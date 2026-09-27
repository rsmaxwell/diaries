# 0025 Step 7 — Type-aware and Image-aware UpdateFragment

Completed 2026-09-27. Existing uncommitted work preserved. No deployment or commit.

## Changed files

- `handlers/UpdateFragment.java`: carries persisted imageId into the incoming DTO; distinguishes absent/null/value; rejects invalid/nonexistent references and Image assignment to MARQUEE/legacy rows; rejects changed Page/type identity; prevents IMAGE+Marquee edits. Uses the existing transaction-scoped Image lookup/lock for explicit selection. Locks the Fragment row before loading lock/version state and requires exactly one updated row. Rejects joining a caller transaction.
- `handlers/UpdateFragmentImageTest.java`: four tests cover selection semantics, legacy/MARQUEE compatibility, malformed/nonexistent IDs and immutable ownership.
- `ImageWiringIntegrationTest.java`: real PostgreSQL handler verification with a recording MQTT client that independently reads committed database rows at publication time.
- Responder README and feature plan/README describe the public patch semantics and mark Step 7 complete.

Existing ordinary field parsing, edit-lock rules, stale-version response, response payload (Fragment ID), normalisation and publication order remain. Image-only edits increment version once and do not renumber siblings. Date/sequence edits retain existing normaliser version increments on rows whose sequences change; no alternate IMAGE chronology or second edit protocol was introduced.

## Validation

Responder full tests and build passed: **283 discovered, 252 passed, 31 environment-gated skips, zero failures/errors**. See `responder-test-build.log`, `unit-results.json`, `handler-tests.xml`.

Separate database integration: **one passed, zero skipped**, in `verified-run/result.json` and `verified-run/integration-test.xml`. It verifies:

- text-only preservation, replacement, explicit clear and attachment;
- successful edits clear locks, bump version once when chronology is unchanged, and do not change sibling versions;
- missing Image, stale version, wrong lock owner, changed type and changed Page reject without DB or retained-state changes;
- a date/sequence/Image change normalises both dates in the same transaction;
- an injected updateSequence failure rolls back the already-written Image/date/lock/version changes and publishes nothing;
- successful date moves remove the old alias and publish identical canonical/new-date state;
- MARQUEE edits without imageId remain compatible, and non-null imageId is rejected;
- publications occur outside the write transaction and match committed rows read through an independent EntityManager.

The fixture uses the frozen 0024 backup plus 0024/0025 schemas in an owned disposable PostgreSQL container. Row counts/hashes match after cleanup and the container is removed. No live DB/broker/NAS was modified. This run uses a recording MQTT client, not a live broker; real broker/registered creation coverage remains Step 6 evidence.

`run-01` preserves the initial failed integration: its date-move fixture supplied a string sequence, whereas the existing UpdateFragment contract requires a numeric value. Corrected to BigDecimal and strengthened the rollback probe to require the exact injected failure before the final passing run. No production parsing was changed for the fixture. The final test-source change was validated by the integration rerun after the full regression/build.

Existing Gradle/Shadow/native-query warnings remain nonfatal. Client request code was inspected: it omits imageId today, which now safely preserves IMAGE references. No client or web source/retained schema changed, so their builds were not repeated; retained payload compatibility was verified in Step 5.

## Remaining scope

Step 8 audits/generalises remaining lock/delete/normalisation paths. Reference-aware Image deletion and production authoring prerequisites still apply. This does not provide automatic retries or guarantee delivery after post-commit broker failure; existing replay/publication semantics remain. No additional database migration is required.
