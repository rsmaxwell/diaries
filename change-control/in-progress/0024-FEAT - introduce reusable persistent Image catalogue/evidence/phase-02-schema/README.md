# Phase 2 schema evidence

Completed on 2026-09-12. All three Phase 2 sections are implemented and the
additive migration is applied to the development-infrastructure database.
Production was not changed; deployment remains Phase 11.

## Development application

- Target: `diaries-development-db`, database/application role `diaries`.
- Server: PostgreSQL 18.6, `postgres:18-alpine`; immutable image ID is in
  [run-result.json](development-20260912/run-result.json).
- Apply: 2026-09-12 19:47:35–19:47:36 UTC, exit code 0.
- New `public.image` table is empty; its identity sequence, named checks,
  primary key and both secondary indexes match the exact catalogue contract.
- Preflight was read-only. Postflight passed inside the DDL transaction before
  commit and again in a read-only transaction after commit.

The [complete database log](development-20260912/preflight-apply-postflight.txt)
records unchanged counts and full-row SHA-256 digests for all four existing
tables:

| Table | Before | After |
| --- | ---: | ---: |
| diary | 10 | 10 |
| page | 683 | 683 |
| fragment | 2,329 | 2,329 |
| marquee | 2,269 | 2,269 |

Existing Fragment findings were preserved: 60 without a Page, 81 unclassified,
2,248 MARQUEE, zero IMAGE, zero invalid type, zero missing referenced Page,
and zero multiple-Marquee ownership cases. Marquee missing-parent and
Fragment/Page mismatch counts remain zero. The indicative HTML regex still
finds 72 possible embedded-image Fragments; it does not replace 0022's tolerant
HTML candidate inventory. No Fragment HTML, chronology, version or lock fields
were changed, as verified by the full-row digests.

## Backup

Created using the existing development backup script:

`data/database-backups/development-infrastructure/diaries-development-20260912-203528.dump`

Size: 277,932 bytes. SHA-256:
`fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86`.

The backup was successfully restored into new databases in an isolated
PostgreSQL container with no network/ports and storage in tmpfs. The original
development database was never restored or replaced. Its archive listing is
saved in [backup-archive-list.txt](development-20260912/backup-archive-list.txt).

## Validation

[test-results.json](integration-tests/test-results.json) and 24 named logs record
24 passing integration scenarios against restored data. They cover read-only
preflight, first apply, reruns, preservation of a populated catalogue, identity
and defaults, duplicate checksums at different paths, ASCII and Unicode case
collisions, 12 invalid-row cases, 12 incompatible-schema variants, orphan
sequence/view rejection, missing privileges, missing preflight, chronology
drift, and rollback when the actual apply script encounters an injected
postflight error. Case-only duplicates are rejected by the real unique index.
The isolated test container was stopped after verification.

The evidence runner was separately tested against the isolated restore before
the development application. The final SQL executed on development is copied
under [development-20260912/sql](development-20260912/sql/001-preflight.sql).
Its hashes are in the nested [SHA256SUMS.txt](development-20260912/SHA256SUMS.txt).

Responder validation from the Diaries repository root:

```powershell
.\gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain
```

Result: BUILD SUCCESSFUL in 12s, 14 suites / 127 tests, zero failures, errors or
skips. See [build log](responder-build.txt) and
[test totals](responder-test-results.json). Existing Shadow duplicate-service
warnings and Gradle deprecation warnings remain. An initial attempt used the
responder subdirectory, which has no wrapper; the successful command used the
repository-root wrapper shown above.

No client, responder runtime, MQTT, configuration, deployment or NAS files were
changed. Angular tests were not rerun for this SQL-only change. Production
backup/configuration checks and execution remain unperformed and are documented
in [the migration runbook](../../migration/README.md).

The top-level `SHA256SUMS.txt` freezes these evidence files and the reviewed
migration source snapshot, excluding only itself. All hashes were verified.
