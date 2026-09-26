# 0024 Phase 3.2: Image repository

Implemented on 2026-09-12.

## Source changes

- `repository/ImageRepository.java`: extends the existing CRUD interface and
  adds findByRelativePath, findAllOrderedByRelativePath and existsAtOrBelow.
- `repositoryImpl/ImageRepositoryImpl.java`: implements all CRUD operations
  with bound PostgreSQL queries; no caller-provided values are interpolated
  into SQL. This includes paths, checksum, captions, filenames and identifiers.
- `model/Image.java`: extracts the existing canonical-path syntax validation
  into validateCanonicalRelativePath, shared by metadata and lookup validation.
  The accepted path rules are unchanged; this avoids a second copy in the repository.
- `repositoryImpl/ImageRepositoryIntegrationTest.java` in test sources:
  ten opt-in tests using actual PostgreSQL 18 and Hibernate.

The repository implements the CRUD interface directly rather than inheriting
AbstractCrudRepository's value-to-SQL quoting. Its legacy find(String where)
method throws UnsupportedOperationException; callers must use the bound lookup
methods. No existing repository or generic CRUD implementation was changed.

## Contract

All reads explicitly project the ten Phase 2 columns and return ImageDBDTOs.
Malformed rows fail validation rather than silently creating partial DTOs.
Path lookup uses exactly the index expression:

```sql
lower(relative_path COLLATE pg_catalog.pg_unicode_fast)
```

The bound lookup argument is lowercased with the same database collation.
Original path case is preserved. A lookup returns Optional.empty for no match
and fails on multiple results instead of choosing an arbitrary row. Ordered
listing uses the folded path, original path under C collation, then id as a
stable tie-breaker; findAll delegates to this ordering.

existsAtOrBelow checks the exact path or descendants beginning with path plus
`/`. Thus `album` covers `album/photo.png`, but neither `albums/photo.png` nor
`album-other/photo.png`. Percent and underscore are escaped as literals using
`!`, with the escape marker itself escaped. The final descendant wildcard is
the only wildcard introduced by the repository. SQL-looking text and apostrophes
remain bound data. Empty String represents Files root for this ownership check;
it returns whether any catalogue row exists. Empty String is invalid for exact
file lookup and for persisted Image metadata.

All writes require an existing resource-local EntityManager transaction, owned
by the caller. Save requires a new Image with no id, validates metadata, inserts
with bound values and assigns the returned identity. Update validates metadata
and persists the supplied version, matching existing CRUD semantics; it does
not increment version or add optimistic compare-and-swap semantics. Later
services own version/conflict handling. Update/delete return affected-row
counts, including zero for an absent row. Rollback removes all transaction
changes; callers must discard/reload an inserted model after rollback because
its assigned identity is not cleared automatically.

No operation publishes MQTT state or changes Files-root contents. Catalogue
deletion through these internal CRUD methods does not add a public DeleteImage
operation or change generic DeleteFile handling.

## Validation

The fixture was a new postgres:18-alpine container with tmpfs storage and a
random loopback-only port. Its database was named image_repository_test and
initialized using the actual Phase 2 migration/schema.sql. No development or
production database was used. The tests bootstrap Hibernate with only Image
registered and hbm2ddl.auto=validate; schema validation passed, including the
CHAR(64) checksum mapping. A JPA read of a repository-inserted Image also passed.

The ten PostgreSQL tests cover:

- all-column save/find/update/delete round trips and JPA readback;
- ASCII and Unicode case aliases, and duplicate insert/update rejection;
- directory boundaries and exact file matches;
- literal percent, underscore and escape-marker paths;
- apostrophes and SQL-looking text, and rejection of raw SQL predicates;
- deterministic ordering and permitted duplicate checksums;
- empty catalogue, root checks and missing paths;
- invalid path, metadata and identifier rejection;
- caller rollback and refusal to write without a transaction.

Both focused tests and the complete responder suite/build passed. Full result:
16 suites, 147 tests, zero failures/errors/skips, including all ten integration
tests. See [test-results.json](test-results.json),
[repository-tests.xml](repository-tests.xml) and [responder-build.txt](responder-build.txt).
The fixture contained zero Image rows after the tests and was stopped;
[database-fixture.txt](database-fixture.txt) records version/image and final count.

An initial compile used a transaction-status method unavailable on the installed
Hibernate Session API; the implementation now uses the established
EntityManager.getTransaction().isActive() check. Compilation reports a Hibernate
API deprecation note; existing Shadow service-duplicate and Gradle deprecation
warnings remain. There are no failing tests.

## Repeat the tests

From the Diaries repository root in PowerShell, use a new disposable container:

```powershell
docker run --detach --rm --name diaries-0024-repository-test --tmpfs /var/lib/postgresql -p 127.0.0.1::5432 -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_USER=diaries -e POSTGRES_DB=image_repository_test postgres:18-alpine
# Wait until pg_isready succeeds before continuing.
docker exec diaries-0024-repository-test pg_isready -U diaries -d image_repository_test
docker cp 'change-control/in-progress/0024-FEAT - introduce reusable persistent Image catalogue/migration/schema.sql' diaries-0024-repository-test:/tmp/image-schema.sql
docker exec diaries-0024-repository-test psql -X -U diaries -d image_repository_test -v ON_ERROR_STOP=1 -f /tmp/image-schema.sql
if ($LASTEXITCODE -ne 0) { throw 'Fixture setup failed' }
$binding = docker port diaries-0024-repository-test 5432
$port = ($binding -split ':')[-1]
$env:DIARIES_IMAGE_REPOSITORY_TEST_URL = "jdbc:postgresql://127.0.0.1:$port/image_repository_test"
try {
    .\gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain
    if ($LASTEXITCODE -ne 0) { throw 'Validation failed' }
} finally {
    Remove-Item Env:DIARIES_IMAGE_REPOSITORY_TEST_URL
    docker stop diaries-0024-repository-test
}
```

Check every setup command succeeds. The environment variable is opt-in: without
it these integration tests are skipped. The test rejects URLs other than the
loopback image_repository_test database and never reads normal application
configuration. Every test transaction rolls back, including expected database
constraint failures. The logged full-suite run had the fixture enabled and no
skipped tests.

Runtime registration, DiaryContext wiring and transaction helpers remain 3.3.
The full application was not restarted and retained replay was not exercised.
No client/web, deployment, NAS or schema changes were needed; existing consumer
contracts remain unchanged. SHA256SUMS.txt freezes this evidence and a snapshot
of the changed Java sources. No commit or push was performed.
