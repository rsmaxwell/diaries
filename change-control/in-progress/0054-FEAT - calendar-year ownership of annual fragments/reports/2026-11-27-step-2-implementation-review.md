# 0054 Step 2 — Source implementation review (NOT ACCEPTED)

Source basis: user-uploaded `diaries-sources-20261127-204710.zip`; Windows checkout was verified clean at parent `e817acc0eb37`, client `aa6493557771`, responder `a49c6abd0ce0`, Reader `18b18c2c090e` before this package, but live repository was not modified.

This package changes the annual ownership contract and includes a transaction-wrapped SQL migration and audit inventory. It must be reviewed and applied to the relevant repositories before local build, unit tests, migration dry run and broker/Reader integration. Do not deploy any part independently.

The SQL migration deliberately does not publish MQTT messages. After the schema and aligned applications are installed, the responder normal startup sync should converge retained MQTT topics, deleting obsolete diary/year aliases. Capture before/after broker inventories to confirm.

**Gate: OPEN.** No local development DB, production DB, MQTT broker or application has been changed by this package. Test results are not implied.

## Source review in this environment

- Changed files packaged: 37 (client, responder, Reader, architecture and feature-local tools/report).
- PASS: strict standalone TypeScript compilation of annual model modules with `tsc --noEmit --strict --target es2022` (does not compile Angular application).
- PASS: standalone Java compilation of `FragmentPlacement` and `FragmentOwnership` with `javac` (does not compile Spring Boot application).
- BLOCKED: Gradle responder/Reader compilation: Gradle wrapper requires `gradle-9.6.1-bin.zip`, which is not cached; environment has no outbound access (`UnknownHostException: services.gradle.org`).
- NOT RUN: Angular full build, Java unit tests, database migration (including repeat run), integration tests, browser tests, MQTT retained reconciliation and production rollout.

## Application sequence and regression prerequisites

Apply all source changes as one coherent set to the verified checkouts. Run complete Java and Angular builds and unit tests on the Windows checkout or on `mango` (with repository revisions confirmed). Run the feature-local SQL only on the **development** PostgreSQL container initially, after recording the original annual inventory and verifying the development recovery point. It drops `fragment.diary_id` NOT NULL for annual fragments, converts `POSTAMBLE` to `EPILOGUE`, clears their physical ownership and synthetic date fields, then establishes new checks; the SQL is designed to be repeatable. No production cutover before the integrated acceptance gate.

After the coordinated app change, restart the development responder and inspect `diaries/years/#` in MQTT Explorer. Verify 9 canonical year-owned topics and zero legacy diary-owned annual topics, then re-run the sync to verify convergence. Browser-test empty Diary manual year selection, PREAMBLE/EPILOGUE CRUD, two physical Diaries showing identical annual objects, sequence operations and unchanged DATED entries; verify Reader annually rendered content at existing Diary URLs. Use the pre-cutover matching database/files recovery point plus previous application versions for rollback; responder startup reconciliation regenerates retained topics. Record outputs under `evidence/step-2/` and close the gate only after acceptance.

## File manifest

- `ARCHITECTURE.md`
- `change-control/in-progress/0054-FEAT - calendar-year ownership of annual fragments/reports/2026-11-27-step-2-implementation-review.md`
- `change-control/in-progress/0054-FEAT - calendar-year ownership of annual fragments/tools/0054-audit-annual-fragments.sql`
- `change-control/in-progress/0054-FEAT - calendar-year ownership of annual fragments/tools/0054-migrate-annual-fragments.sql`
- `diaries-client/src/app/diary/annual-editor/annual-editor.component.html`
- `diaries-client/src/app/diary/annual-editor/annual-editor.component.spec.ts`
- `diaries-client/src/app/diary/annual-editor/annual-editor.component.ts`
- `diaries-client/src/app/fragment/quill-text-toolbar.ts`
- `diaries-client/src/app/model/annual-fragment-request.spec.ts`
- `diaries-client/src/app/model/annual-fragment-request.ts`
- `diaries-client/src/app/model/annual-fragments.spec.ts`
- `diaries-client/src/app/model/annual-fragments.ts`
- `diaries-client/src/app/model/fragment.ts`
- `diaries-client/src/app/mqtt/rpc.service.ts`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentPublishDTO.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddAnnualFragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/DeleteFragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/NormaliseFragments.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateFragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/Fragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/FragmentOwnership.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/FragmentPlacement.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repository/FragmentRepository.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repositoryImpl/FragmentRepositoryImpl.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/sync/Synchronise.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/DiaryContext.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentSequenceNormaliser.java`
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/dto/FragmentAnnualTopicTest.java`
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/model/FragmentOwnershipTest.java`
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/FragmentSequenceNormaliserTest.java`
- `diaries-web/src/main/java/com/rsmaxwell/diaries/web/http/WebServer.java`
- `diaries-web/src/main/java/com/rsmaxwell/diaries/web/model/FragmentItem.java`
- `diaries-web/src/main/java/com/rsmaxwell/diaries/web/model/FragmentPlacement.java`
- `diaries-web/src/main/java/com/rsmaxwell/diaries/web/projection/DiaryYearPlacementKey.java`
- `diaries-web/src/main/java/com/rsmaxwell/diaries/web/projection/ProjectionSnapshot.java`
- `diaries-web/src/main/resources/templates/month-reader.peb`
- `diaries-web/src/test/java/com/rsmaxwell/diaries/web/projection/ProjectionServiceTest.java`
