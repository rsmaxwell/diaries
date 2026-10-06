# Step 14 regression and rollout rehearsal checklist

Run ID: ____________________
Date: ____________________
Tester: ____________________
Step 13 closed run/evidence: ____________________
Reader backup: ____________________
Reader backup SHA-256: ____________________
Playbooks root/commit: ____________________

## Preconditions

- [ ] Step 13 is closed with client/responder/MQTT/PostgreSQL/Files lifecycle agreement.
- [ ] Java 25 is available.
- [ ] Docker/Testcontainers is available.
- [ ] Angular dependencies are installed.
- [ ] Chrome/Edge is available.
- [ ] Disposable reader backup is available.
- [ ] Current Playbooks source used for production is available for rehearsal.

## Client

- [ ] Full Angular/Karma suite passed with zero failed/skipped required tests.
- [ ] Final test count recorded: __________.
- [ ] Production Angular build passed.
- [ ] MARQUEE navigation/editing regressions remain green.
- [ ] IMAGE create/reference edit/action-state regressions remain green.

## Responder

- [ ] Full responder test/build passed.
- [ ] `ImageFragmentGateConfigTest` passed.
- [ ] `AddFragmentContractTest.legacyRequestStillCreatesMarqueeAndReturnsFragmentWithAdditiveImageId` passed.
- [ ] `AddImageFragmentTest` passed.
- [ ] `UpdateFragmentImageTest` passed.
- [ ] `FragmentLifecycleContractTest.addingMiddleImageFragmentNormalisesAndPublishesSurvivingChronology` passed.
- [ ] `FragmentLifecycleContractTest.addingMiddleMarqueeFragmentNormalisesAndPublishesSurvivingChronology` passed.
- [ ] `FragmentLifecycleContractTest.deletingMiddleImageFragmentNormalisesAndPublishesSurvivingChronology` passed.
- [ ] `FragmentLifecycleContractTest.deletingOneSharedReferenceLeavesOtherFragmentAndImageUntouched` passed.
- [ ] `FragmentLifecycleContractTest.updateRejectsCrossTypeMutationsBeforeAnyWriteOrPublication` passed.
- [ ] `DeleteImageTest.referenceConflictIs409WithRestoredFileAndRetainedMetadata` passed.
- [ ] `ImageWiringIntegrationTest` required MQTT/database/browser cases passed with no skips, including restart/replay, real retained-topic lifecycle, Files-dialog deletion, registered add and registered delete.

## Reader

- [ ] Full `diaries-web` test/build passed.
- [ ] `ProjectionServiceTest` mixed/shared Image chronology cases passed.
- [ ] `RenderingSafetyTest` catalogue URL/static Files path cases passed.
- [ ] `MqttProjectionIntegrationTest.imageCatalogueDoesNotChangeVisibleChronologyAcrossReaderRestarts` passed.
- [ ] `Step12MqttHttpIntegrationTest.retainedReplayLiveImageChangesAndFreshReconnectReachHttpWithoutStaleState` passed.
- [ ] Disposable `verify-imagefragment-reader.ps1` run passed against current responder/web source.
- [ ] Reader browser verification showed MARQUEE and IMAGE content without converting legacy content.
- [ ] Restart/replay restored the same ImageFragment/Image relationship.
- [ ] Browser-visible Image URL resolved through the configured Files route.
- [ ] Reference-aware Image deletion was blocked while referenced and allowed after the final owned reference was removed.

## Production-like configuration

- [ ] `compose.local-docker-build.yaml` rendered successfully with effective env overrides.
- [ ] `compose.local-published-smoke.yaml` rendered successfully with effective env overrides.
- [ ] Source/config SHA inventory captured after the successful run.

## Rollout rehearsal

- [ ] Current production Playbooks `roles/diaries` source inspected.
- [ ] Production responder template has `imageFragmentWritesEnabled=false`.
- [ ] Production reader Files path is compatible with `/files/...` catalogue URLs.
- [ ] Production start order validates Compose before pull/up.
- [ ] Production start waits for service health before shared-route activation.
- [ ] Production stop removes the shared route before stopping services.
- [ ] Step 14 performed no production deployment and no gate enablement.

## Final acceptance

- [ ] `regression-summary.json` is `PASSED`.
- [ ] `rollout-rehearsal.txt` contains no failures.
- [ ] `step14-finalize.ps1` passed and `step14-final-summary.json` is `PASSED`.
- [ ] No required test was skipped.
- [ ] No unresolved client/responder/reader mismatch remains.
- [ ] Restart/replay reproduces the pre-restart relationship and chronology.
- [ ] Existing MARQUEE behavior is unchanged.
- [ ] Step 14 is ready to close and Step 15 may begin.
