# 0026 Step 5 — Store Images in immutable projection snapshots

**Complete locally — 2026-09-29.** Image metadata now participates in the same mutable→immutable projection lifecycle as the existing canonical entities. The corrected Step 5 source has been verified on the normal Windows Java 25/Docker development machine with the focused projection/contract/HTTP tests, the MQTT/Testcontainers integration tests, and the full `:diaries-web:test :diaries-web:build` run all completing successfully.

## Implementation
- `MutableProjectionState` now owns an `ImageItem` map. `UpsertImage` uses the existing equality-based `putChanged` policy and IMAGE tombstones remove from that map. No new stale-version/global ordering algorithm was introduced.
- `ProjectionSnapshot` copies the Image map with `Map.copyOf`, exposing only `imageCount()` and `imageById(long)` for bounded diagnostics/resolution access. A captured snapshot therefore cannot observe later mutable-state changes.
- Existing replay semantics apply unchanged: `beginReplay()` creates a new empty staging state, retained Image messages populate only staging, and the complete generation swaps atomically after subscription acknowledgement plus the quiet period. Missing Images in a reconnect replay are not copied from the old active state.
- `ProjectionService` replay logging now includes the Image count. `/health/ready` and the About projection status include `images` alongside the existing entity counts. `ProjectionStatus` itself did not require a new field: invalid-message/tombstone counters and failure/readiness semantics already cover Image events.
- Projection tests cover duplicate delivery, metadata/version replacement, IMAGE tombstone, immutable old snapshots, Image-before-Fragment and Fragment-before-Image arrival, tombstone-before-later-reference, and reconnect without a stale Image.
- The Image contract test now proves a malformed live Image replacement increments the rejection count while retaining the last valid Image and generation.
- Real MQTT integration tests now assert retained Image counts/lookups, live Image upsert/tombstone storage, and valid-plus-malformed Image replay with the actual `diaries-web` reader identity. Visible MARQUEE chronology remains unchanged by catalogue-only Images.

## Step boundary

This step deliberately does **not**:

- add an Image to `ResolvedFragment`;
- replace the temporary `unsupportedImageFragments` diagnostics;
- derive catalogue file URLs;
- change HTML/templates/JavaScript rendering;
- enable ImageFragment authoring.

Those are later 0026 steps.

## Validation performed

The authoritative console output is preserved verbatim in `test-results.txt`. The final corrected package was applied before these successful runs.

From the parent `diaries` directory:

```powershell
.\gradlew.bat :diaries-web:test `
  --tests "*ProjectionServiceTest" `
  --tests "*ImageReaderContractDefinitionTest" `
  --tests "*WebServerTest" `
  --rerun-tasks --console=plain

.\gradlew.bat :diaries-web:test `
  --tests "*MqttProjectionIntegrationTest" `
  --tests "*MqttReaderAclIntegrationTest" `
  --rerun-tasks --console=plain

.\gradlew.bat :diaries-web:test :diaries-web:build `
  --rerun-tasks --console=plain
```

Recorded outcomes:

- focused projection/contract/HTTP verification: **BUILD SUCCESSFUL in 10s**, 7 actionable tasks; the supplied evidence contains a second successful repeat of the same focused command;
- MQTT/Testcontainers integration verification: **BUILD SUCCESSFUL in 41s**, 7 actionable tasks;
- complete web test/build verification: **BUILD SUCCESSFUL in 49s**, 15 actionable tasks;
- only the pre-existing `ConfigLoader.java` deprecated-API compiler note was emitted; it is non-fatal.

The console log does not print an aggregate JUnit test count, so this evidence intentionally records the successful Gradle tasks rather than inferring a total test number.

## Packaging correction

The first Step 5 package exposed a Java generic-inference compile error in `ProjectionServiceTest.imageStorageIsIndependentOfImageFragmentArrivalOrder()`. The two heterogeneous event lists were corrected to use explicit `List.<ProjectionEvent>of(...)` type witnesses. This was a test-only compile correction; production Step 5 behaviour was unchanged. The successful verification above was run after that correction.

## Completion decision

Step 5 is complete locally because:

- Image upsert/update/tombstone state is stored in the mutable projection and copied into immutable snapshots;
- old snapshots remain isolated from later mutable changes;
- fresh replay/reconnect state does not retain stale Images;
- readiness/status exposes the projected Image count;
- malformed Image replacement preserves the last valid Image while incrementing rejection diagnostics;
- real MQTT retained/live Image storage and tombstone behaviour pass with the reader path;
- the full `diaries-web` test/build passes after the final source correction.

## Remaining boundary after completion

Step 5 still deliberately does **not** resolve a catalogue Image onto `ResolvedFragment`, derive browser file URLs, or render ImageFragments. Those are Step 6 and later. No production deployment or ImageFragment authoring is enabled by this completion.

**Next:** Step 6 — resolve mixed Fragment types and add diagnostics.
