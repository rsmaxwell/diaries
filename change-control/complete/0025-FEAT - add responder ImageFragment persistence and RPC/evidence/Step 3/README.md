# 0025 Step 3 — Fragment persistence model and repository contract

Completed 2026-09-27 against responder baseline `810444eb37289dd16a9fb3a317358c1a21b6cdcf` plus the local changes captured in `source-sha256.csv`. No commit or deployment was performed.

## Implementation

- `Fragment`: nullable JPA Image relationship without cascade; transient persisted Image id; getter/setter and both DTO constructors preserve Image identity alongside Page/type/lock state.
- `FragmentDBDTO`: nullable `imageId`.
- `FragmentPublishDTO`: internal `imageId` and constructor copying satisfy the Step 3 reconstruction contract. Temporary `@JsonIgnore` keeps the existing retained JSON shape; Step 5 must remove it and update the boundary test.
- `FragmentRepository`/`FragmentRepositoryImpl`: bound `existsByImageId` lookup; null returns false. `image_id` is inserted after `type` in fields, values, positional mapping and all three handwritten projections; all five lock positions shift together.
- `FragmentRepositoryImplTest`: non-null Image/Page/type round-trip, complete lock mapping, relation replacement/clearing, null migration fields, field/value alignment and typed unreferenced fragments.
- `ImageWiringIntegrationTest`: real repository and production JPA factory integration. `FragmentSequenceNormaliserTest` fake implements the added interface method and fails explicitly if unexpectedly called.
- Responder README documents the migration prerequisite and pre-0025 backup restore implications.

## Validation

`gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain` passed.
266 tests discovered: **239 passed, 27 environment-gated tests skipped, zero failures/errors**.
See `responder-test-build.log`, `unit-results.json` and the focused `unit-reports/`.
Existing Gradle deprecation and Shadow service-resource duplication warnings remain.

The database test was separately enabled and **passed, 1 test, zero skips**:
`ImageWiringIntegrationTest.fragmentImageRepositoryRoundTripsAndCountsReferences`.
The final evidence is [verified-run/result.json](verified-run/result.json) and
[verified-run/integration-test.xml](verified-run/integration-test.xml).
`run-01` also passed before reference-clearing assertions were added.
An initial runner invocation failed at PowerShell parameter parsing before creating
any container; the parameter declaration was corrected before these runs.

The runner starts a new PostgreSQL 18 container with ephemeral storage and a random
loopback-only port, restores the frozen 0024 backup (SHA-256
`fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86`), installs the Image
schema and Step 2 migration, and verifies:

- zero, one and two references to the same Image;
- native insert/read/update and JPA relationship loading;
- `findAll`, date, no-Marquee, stale-lock and joined-Marquee projections;
- existing MARQUEE rows keep null Image references and unchanged DTO values;
- text/sequence updates retain the Image reference, Page and lock data;
- clearing/restoring a reference changes lookup results;
- deleting one/both fragments leaves the reusable Image intact.

All fixture mutations are rolled back. Before/after row counts and hashes match
for Diary, Page, Fragment, Marquee and Image. The disposable container was removed
successfully. PostgreSQL sequences may advance inside the disposable fixture;
row-hash equality does not claim sequence rollback.

## Scope and next steps

No live database, broker, NAS files, client code or web code was changed. Client
`model/fragment.ts` and web `FragmentItem` already permit nullable Image IDs; the
retained wire format is unchanged in Step 3, so client/web builds were not rerun.
The retained DTO regression suite passed.

Step 4 aggregate/service inflation remains next. Step 5 owns retained publication;
later steps own RPC authoring and reference-aware DeleteImage behaviour. The new
lookup is a primitive, not a complete concurrency-safe deletion guard.
Apply the reviewed Step 2 migration before starting this source against an existing
database, including one restored from the frozen backup. No live migration was run.

To repeat the isolated test with fresh evidence:

```powershell
pwsh -NoProfile -File './run-integration.ps1' -EvidenceDirectory './new-run'
```
