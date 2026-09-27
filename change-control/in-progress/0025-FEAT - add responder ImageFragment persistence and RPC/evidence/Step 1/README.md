# 0025 Step 1 — Frozen pre-0025 responder baseline

Recorded 2026-09-27. Step 1 complete. No application code, schema, data, RPC shape or production configuration was changed.

## Identity and scope

baseline.json records the full responder and parent Git identities. The responder working tree was clean at capture and remained unchanged by validation. The parent is intentionally dirty: it contains the previously authorized 0030 close-out/move, 0024 link corrections, and the user's 0025 planning move/documents. parent-status.txt preserves that context. No commit, reset, stash or tag was created.

source-sha256.csv fingerprints all current responder main/test files and build.gradle. Together with the clean responder commit it defines the source to compare after 0025. The active workspace remains authoritative for implementation; this record is a historical comparison baseline.

Existing state: Fragment has page_id and type but no Image relationship/image_id; FragmentPublishDTO has pageId/type but no imageId; AddFragment creates MARQUEE plus Marquee; no addImageFragment handler is registered. Existing recoverable DeleteImage is present, without Fragment reference checking. This is a source baseline, not a newly inspected live database schema or backup.

## Compatibility behaviour matrix

| Behaviour | Baseline observation and evidence |
| --- | --- |
| addFragment creates MARQUEE and Marquee | Source inspected: AddFragment constructs FragmentDBDTO with pageId and MARQUEE, builds the associated Marquee, saves the pair and publishes both. No dedicated addFragment handler execution was added or claimed in this step. |
| updateFragment edits date/text/sequence, preserving ownership/type | Source inspected: UpdateFragment copies pageId/type from the loaded original, requires caller lock, checks version, updates within a transaction, clears lock and normalises affected dates before publication. FragmentSequenceNormaliserTest independently verifies sequence/date behaviour, unchanged other fields and concurrent-version rejection. |
| Fragment lock/unlock publication | Source inspected: LockFragment and UnlockFragment commit changes then use FragmentLocking.publish with an optional Marquee. RetainedStateDtoContractTest executes locked/unlocked Fragment serialization and publication/tombstone conventions. This is not a fresh live lock/unlock RPC test. |
| Normalisation uses all Fragment rows and stable ordering | FragmentRepositoryImpl declares ORDER BY year, month, day, sequence, id; FragmentSequenceNormaliser operates on Fragment rows, not geometry. Five normaliser tests passed; repository mapping tests retain page/type/lock positions and legacy nulls. |
| DeleteFragment removes Fragment and optional Marquee | Source inspected: conditionally deletes Marquee, deletes Fragment in the same transaction, commits, conditionally tombstones Marquee and tombstones Fragment. No dedicated live DeleteFragment execution is claimed. |
| Replay independent of Marquee | DiaryContext.loadFromDatabase iterates FragmentRepository.findAll independently, looks up optional Marquee and publishes Fragment. DiaryContextTest.databaseReplayPublishesAFragmentWithoutDependingOnAMarquee passed. |
| Generic DeleteFile protection | DeleteCatalogueTest: 7 passed, retaining catalogue ownership rejection. |
| Recoverable unreferenced DeleteImage | DeleteImageTest (7), ImageCatalogueDeletionTest (14), ImageDeletionConcurrencyTest (3) passed: authorization/statuses, stable identity, staging/rollback/unknown outcomes, post-commit tombstone failure diagnostics/backups, duplicate delete and both upload/delete orders. |

The matrix deliberately distinguishes executable tests from inspected handler control flow. Later steps should extend handler/integration tests when those paths change; this baseline does not overstate existing coverage.

## Frozen contract anchors

Authoritative source paths, all included in source-sha256.csv:

- model/Fragment.java; dto/FragmentDBDTO.java; dto/FragmentPublishDTO.java
- handlers/AddFragment.java; UpdateFragment.java; DeleteFragment.java; LockFragment.java; UnlockFragment.java
- utilities/FragmentAndMarquee.java; FragmentLocking.java; FragmentSequenceNormaliser.java; DiaryContext.java
- repository/FragmentRepository.java; repositoryImpl/FragmentRepositoryImpl.java
- handlers/DeleteFile.java; DeleteImage.java; utilities/ImageCatalogueService.java; dto/ImagePublishDTO.java

These paths are relative to src/main/java/com/rsmaxwell/diaries/responder. RetainedStateDtoContractTest fixes the exact existing Fragment JSON field set, optional marquee/lock representation and canonical/date topic conventions; its test source is fingerprinted as part of the baseline.

## Validation performed

Command from diaries:

```text
gradlew.bat :diaries-responder:test --tests '*FragmentRepositoryImplTest' --tests '*FragmentSequenceNormaliserTest' --tests '*DiaryContextTest' --tests '*RetainedStateDtoContractTest' --tests '*DeleteImageTest' --tests '*ImageCatalogueDeletionTest' --tests '*ImageDeletionConcurrencyTest' --tests '*DeleteCatalogueTest' :diaries-responder:build --rerun-tasks --console=plain
```

**47 tests passed, zero failures/errors/skips; responder build passed.** All seven suites required by the plan were run, plus DeleteCatalogueTest for the explicitly required generic-file guard. See test-summary.csv, test-reports and gradle-test-build.log. Existing Gradle deprecation/Shadow resource warnings remain.

No fresh database/broker fixture or client run was needed for this source/focused-test freeze. Prior cross-layer evidence remains in completed 0030: Step 9 verified-run, Step 10 restart integration, and Step 11 user-confirmed production Image 84 deletion. Those historical checks are not represented as newly executed here.

## Guardrails for subsequent steps

- Compare MARQUEE behaviour and retained fields against this baseline after introducing imageId; additive changes must not alter existing lock/version/date/sequence semantics.
- Step 2 schema work has not started; no migration or live-data mutation was performed.
- Add reference-aware DeleteImage conflict protection before production ImageFragment authoring.
- 0025 capability alone must not enable production authoring. Verify/deploy 0026 consumers before 0027 authoring; legacy conversion remains 0028.

No failing baseline was found in the required tests. This record is not production ImageFragment enablement approval.
