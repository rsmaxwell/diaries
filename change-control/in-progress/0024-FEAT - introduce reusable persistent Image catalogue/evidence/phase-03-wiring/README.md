# 0024 Phase 3.3: registration and wiring

Completed on 2026-09-13. All of Phase 3 is implemented in source; rollout to
production remains Phase 11 and Image retained replay remains Phase 4.

## Changes

- `utilities/GetEntityManager.java` registers Image exactly once in the actual
  persistence-unit class list. This replaces the duplicate Marquee registration;
  each existing entity remains registered.
- `Responder.java` extracts its existing context setup into package-private
  createContext, called by run and integration tests. It constructs
  ImageRepositoryImpl using the same EntityManager and installs it alongside
  the five existing repositories. Configuration and resource ownership are
  unchanged; the run method still closes its EntityManager/factory.
- `utilities/DiaryContext.java` exposes ImageRepository, adds inflateImage(Long)
  and inflateImage(ImageDBDTO), and adds focused saveImage/updateImage helpers.
- `utilities/DiaryContextImageTest.java` and `ImageWiringIntegrationTest.java`
  add eight unit tests and five real PostgreSQL integration tests.
- The responder README and change checklist document migration prerequisites,
  helper semantics and the remaining Phase 4 work.

Image inflation has no Diary, Page, Fragment or Marquee dependency. Missing ids
raise `Image not found: id: ...`, consistent with other context inflation helpers.

saveImage validates and copies the input, saves inside an owned transaction,
commits and returns the saved copy. The original object's id remains unchanged
on both success and failure. Callers must use the returned value. updateImage
also validates a copy and returns the affected-row count after commit; it
persists the supplied version, following the Phase 3.2 CRUD contract. Version
increment/conflict decisions remain with future service orchestration.

The helpers reject an existing transaction before beginning or writing. A
caller managing a wider transaction uses getImageRepository directly. Failures
during work/commit roll back an active transaction; rollback errors are attached
as suppressed exceptions so the original failure is preserved. A failed begin
does not trigger rollback. No helper publishes MQTT state, modifies files or
returns an uncommitted result. As elsewhere, a connection failure during commit
can have an uncertain database outcome; later upload compensation must account
for that rather than treating every commit exception as proof of no commit.

The existing context/EntityManager ownership and single-thread usage contract
remain in place. This change does not make a shared EntityManager thread-safe.
There is no new public DeleteImage handler or delete helper in this phase.

## Validation

The integration tests use the production GetEntityManager.adminFactory with
Hibernate `validate`, then invoke exactly the same Responder.createContext
method as startup. Image is present once in the metamodel; all repositories and
configuration remain wired. A separate EntityManager reads committed Image data.

The fixture is a new PostgreSQL 18.6 container with temporary storage and a
random loopback-only port. The existing verified backup
`diaries-development-20260912-203528.dump` was restored into the newly created
image_wiring_test database, followed by the Phase 2 Image schema. Backup SHA-256:
`fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86`.
A separate image_repository_test database enabled the ten Phase 3.2 tests.
Neither development nor production was modified or restored.

Tests verify successful commit/update/inflation, duplicate-path rollback and
subsequent reuse, rejection of nested transactions, invalid metadata, failed
begin, failed commit, rollback failure preservation and unchanged caller input.
Full-row JSON digests of Diary, Page, Fragment and Marquee are identical before
and after the integration suite. Existing retained replay maps are identical
before and after creating an unreferenced Image; Phase 4 replay is intentionally
not activated yet. The copied chronology is 10 Diaries, 683 Pages, 2,329
Fragments and 2,269 Marquees. Final fixture Image count is zero after cleanup.

Focused run: eight context unit tests plus five wiring integration tests passed.
Full run: **18 suites, 160 tests, zero failures/errors/skips**; responder build
successful in 55 seconds. The ten Phase 3.2 PostgreSQL tests were enabled too.
See [test-results.json](test-results.json), [responder-build.txt](responder-build.txt),
the two JUnit XML reports, and [database-fixture.txt](database-fixture.txt).
Existing Shadow duplicate-service and Gradle deprecation warnings remain.

Tests exercised the real factory and startup context assembly, not the live
MQTT listener loop. No real broker publication, application restart, frontend
build, NAS access or production deployment was performed. No RPC or client/web
contract changed. The temporary PostgreSQL container was stopped after evidence
capture. Earlier evidence packages were preserved.

## Repeating validation

Use a fresh disposable PostgreSQL 18 container, initialized as in the 3.2
evidence runbook. In addition to image_repository_test, create a new database
named image_wiring_test, restore the backup above into that empty database,
then apply migration/schema.sql to it. Never point these tests at normal
application databases. The two test classes accept only their named databases
on a loopback port and do not read user application configuration.

From the Diaries repository root in PowerShell, substituting the fixture's port:

```powershell
$env:DIARIES_IMAGE_REPOSITORY_TEST_URL = 'jdbc:postgresql://127.0.0.1:PORT/image_repository_test'
$env:DIARIES_IMAGE_WIRING_TEST_URL = 'jdbc:postgresql://127.0.0.1:PORT/image_wiring_test'
.\gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain
if ($LASTEXITCODE -ne 0) { throw 'Validation failed' }
```

Unset both variables and stop only the disposable fixture container afterward.
Without the opt-in variables, database integration tests are skipped; the logged
run enabled both and had no skips. Unit tests always run. Wiring integration
tests commit Image rows to test visibility and remove only those fixture Image
rows afterward; copied chronology tables are never modified.

Before deploying the newly registered entity, apply the explicit Phase 2
migration and keep Hibernate DDL action at validate or none. No configuration
override enabling automatic schema creation/update is introduced by this change.
Image catalogue replay is the next implementation phase.

SHA256SUMS.txt records hashes for this evidence and the changed-source snapshot.
No commit or push was performed.
