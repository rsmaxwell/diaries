# 0024 Phase 7 — protect generic DeleteFile

Implemented and validated 2026-09-13. Phase 7 is complete. Earlier Phase 6
working changes and frozen evidence were preserved. Reconciliation (Phase 8)
and deployment checks remain later work; no live deployment was changed.

## Changed files

| Responder file | Purpose |
| --- | --- |
| handlers/DeleteFile.java | Authenticate, canonicalize, require the catalogue guard, return relative-path conflicts and preserve the successful response shape |
| utilities/ImageCatalogueService.java | Add JPA exact/descendant guard and non-recursive deletion under the shared upload lock |
| handlers/DeleteCatalogueTest.java (tests) | Ownership, missing bytes, aliases, traversal, symlink/junction, idempotence, ordinary deletion and fail-closed behaviour |
| utilities/ImageCatalogueServiceTest.java (tests) | Verify deletion overlapping upload commit cannot delete its committed winner |
| ImageWiringIntegrationTest.java (tests) | PostgreSQL Unicode/literal-prefix behaviour and retained MQTT state preservation after rejected deletion |

Responder documentation and the parent change checklist/README describe the
completed protection. No client runtime source, database schema, broker ACL or
deployment configuration changed in this phase.

## Behaviour

The handler reuses ImagePathPolicy and the existing ImageRepository
`existsAtOrBelow` query through a fresh EntityManager. Exact paths and
slash-delimited descendants use the same PostgreSQL `pg_unicode_fast` lowercase
identity as uploads/uniqueness. SQL wildcard and escape characters are literal.
Case, separator and Unicode normalization aliases cannot bypass the guard.

Ownership is checked before resolving filesystem aliases or returning missing
path success. A missing catalogued file, or a missing directory with catalogued
descendants, still conflicts. Before a real deletion, ownership is checked again
under the same process critical section and filesystem lock used by upload
promotion/commit. An unavailable/unconfigured catalogue cannot permit deletion.
Other catalogue writers must use the same integrity protocol; arbitrary external
filesystem writers/direct database changes are outside this locking guarantee.

The operation remains non-recursive. It deletes unrelated regular files and
empty uncatalogued directories. Nonempty directories return conflict, and
uncatalogued missing paths remain idempotent without creating requested
directories or a staging directory. Actual deletions may initialize the private
shared lock directory after passing the initial ownership check.

Catalogue conflicts return status 409 and the normalized relative path, not an
absolute host path. Successful responses retain `name`, `subdir`, `path`, with
portable `/` subdirectory separators and the existing absolute compatibility
path. The handler no longer logs request arguments or absolute storage paths.
It never inserts/deletes Image rows or publishes retained messages/tombstones.
There is no public DeleteImage operation.

## Validation

`responder-build.txt` records:

```text
gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain
BUILD SUCCESSFUL in 2m 10s
25 suites; 216 tests; zero failures, errors or skips
```

All Image PostgreSQL/MQTT opt-ins were enabled. Nine new tests cover the seven
handler cases, an upload/delete concurrency case and a PostgreSQL handler case.
The existing real-broker upload test additionally rejects a DeleteFile request,
checks original bytes/row count and verifies that the observer receives no
retained-state mutation.

The PostgreSQL handler test covers a file and its parent directory, decomposed
Unicode/uppercase/backslash aliases, literal `%`, `_` and `!`, absent backing
files/directories, and unrelated prefix-similar names. Metadata remains exactly
unchanged. The concurrency test holds an upload between file promotion and
commit; a deletion initially sees no row, waits for the shared lock, then sees
the committed row and rejects without removing its file. Windows junction or
symlink tests preserve an external temporary sentinel.

`client-tests.txt` records **10 passing** ChromeHeadless file-RPC compatibility
tests, including captured DeleteFile success/error handling through the shared
reply decoder. `client-build.txt` records the successful Angular production
build. The current client has no separate active DeleteFile RPC wrapper to
change. Database/broker tests invoke the authenticated Java handler directly;
they do not send that request through the MQTT RPC dispatcher.

Tests used disposable PostgreSQL 18 and Mosquitto 2.0.22 containers
`diaries-0024-phase7-db` and `diaries-0024-phase7-mqtt`, with random loopback ports
and no application volumes. The wiring database was restored into tmpfs from
the frozen development backup and given the additive Image schema. The broker
used the current repository ACL. Both fixtures were stopped after validation.
Final wiring counts: 10 Diary, 683 Page, 2329 Fragment, 2269 Marquee, zero Image
after cleanup. The suite also checks complete chronology table digests.

The first full-run attempt was blocked by an automatic approval usage limit;
the resumed run above succeeded. Existing Gradle/Shadow warnings remain. No
live database, broker or NAS content was changed. Deployment mount permissions,
locking reliability and separately managed HTTP serving still require the
Phase 11 checks. No commit or push was made.

## Frozen evidence

`source/` contains the five changed Java implementation/test files under short
names. `reports/` contains all JUnit reports, with logs and summary alongside.
SHA256SUMS hashes every evidence file except itself; `.gitattributes` prevents
text conversion. Earlier phase evidence remains unchanged.
