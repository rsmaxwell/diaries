# 0025 exact implementation file scope

The Step 14/15.1 frozen working-tree evidence identifies the following responder implementation/test changes for 0025. This list separates the feature from unrelated top-level change-control movement visible in the parent repository.

## Responder main source

- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/Responder.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/config/Config.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentDBDTO.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentPublishDTO.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddFragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddImageFragment.java` (new)
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddMarquee.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/DeleteFragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/DeleteImage.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/LockFragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UnlockFragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateFragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateMarquee.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/Fragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repository/FragmentRepository.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repositoryImpl/FragmentRepositoryImpl.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/DiaryContext.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentAndMarquee.java` (removed/replaced)
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentLocking.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentSequenceNormaliser.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ImageCatalogueService.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ImageFragmentMessageHandler.java` (new)
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ImageFragmentWritePolicy.java` (new)
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ResolvedFragmentState.java` (new replacement for `FragmentAndMarquee`)
- `diaries-responder/README.md`

## Responder tests

- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/ImageWiringIntegrationTest.java`
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/config/ImageFragmentGateConfigTest.java` (new)
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/dto/RetainedStateDtoContractTest.java`
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/AddFragmentContractTest.java` (new)
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/AddImageFragmentTest.java` (new)
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/DeleteImageTest.java`
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/FragmentLifecycleContractTest.java` (new)
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/UpdateFragmentImageTest.java` (new)
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/repositoryImpl/FragmentRepositoryImplTest.java`
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/DiaryContextTest.java`
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/FragmentSequenceNormaliserTest.java`
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/ImageCatalogueDeletionTest.java`
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/ImageFragmentMessageHandlerTest.java` (new)
- `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/ResolvedFragmentStateTest.java` (new)

## Database/config/change control

- `change-control/in-progress/0025-FEAT - add responder ImageFragment persistence and RPC/migration/001-preflight.sql`
- `.../migration/002-add-fragment-image-reference.sql`
- `.../migration/003-postflight.sql`
- `.../migration/assert-schema.sql`
- `.../migration/snapshot.sql`
- `.../migration/run-migration.ps1`
- `.../migration/README.md`
- `config/environments/local.env.example`
- 0025 feature `README.md`, implementation plan and evidence directories.

No diaries-client or diaries-web application source is changed by 0025.

## Synchronisation revalidation, 2026-09-28

See [exact responder changes](../changed-responder-files.txt) against the frozen pre-0025 baseline. The subsequent Synchronise/SynchroniseCallback changes and large-tree tests are included in the refreshed 398-file Step 14 inventory. Broker configuration and ACL changes are existing local work, not production changes made by this verification. This run adds run-mqtt-regression.ps1, run-container-deployment.py and fresh evidence; it does not alter application Java/TypeScript behavior.
