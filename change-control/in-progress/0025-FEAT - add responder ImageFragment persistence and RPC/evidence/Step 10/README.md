# 0025 Step 10 - Focused cross-type unit and contract coverage

Completed 2026-09-27. Test/documentation changes only; existing Steps 1-9 work preserved.

## New tests

| File | Coverage |
| --- | --- |
| `utilities/ResolvedFragmentStateTest.java` | 13 named dynamic cases covering the entire writer invariant matrix, including MARQUEE with/without Marquee, IMAGE with/without a resolved reference, missing references, forbidden IMAGE+Marquee, and null writer type. Validation preserves the input state; readers can still expose incomplete state for repair. |
| `handlers/AddFragmentContractTest.java` | Legacy numeric-sequence request creates MARQUEE plus Marquee; existing geometry minimum and response fields preserved. `imageId` is explicit null. Injected IMAGE/type/reference fields cannot change the creation path. Exact retained aliases, identical alias payloads, QoS 1, retain and publication after persistence returns are checked. |
| `handlers/FragmentLifecycleContractTest.java` | Real lock/unlock/update/delete and Marquee handlers with strict in-memory persistence/publication seams. Same ownership and session conflict rules for both types; shared Image and second reference survive deletion; immutable type/Page; missing or inappropriate Image references rejected; IMAGE+Marquee update/delete rejected; AddMarquee/UpdateMarquee reject IMAGE with or without an Image reference without unlocking or publishing. |

Added **19 executable test cases** (13 matrix + 1 legacy creation + 5 lifecycle).
No production Java, database schema, runtime configuration, client or deployment changes.

## Required invariant matrix

All entries run in `ResolvedFragmentStateTest.writerInvariantMatrix` on every ordinary test invocation:

| Type | Marquee | Image reference | Expected |
| --- | --- | --- | --- |
| MARQUEE | present | null | valid |
| MARQUEE | absent | null | valid compatibility state |
| MARQUEE | present or absent | existing or unresolved ID | reject |
| IMAGE | absent | null | valid incomplete state |
| IMAGE | absent | resolved Image | valid |
| IMAGE | absent | unresolved ID | reject |
| IMAGE | present | null, resolved or unresolved ID | reject |
| null | absent | null | reject for writers |

Handler tests additionally exercise the actual guard call sites, so coverage is not
limited to directly invoking validation helpers. The existing creation/update tests
cover malformed IDs and missing lookups; aggregate validation tests model the result
of reference resolution rather than claiming to check PostgreSQL existence.

## Contract traceability and existing regression coverage

| Requirement | Executable coverage |
| --- | --- |
| addFragment backward compatibility | AddFragmentContractTest |
| addImageFragment never creates/publishes a Marquee | AddImageFragmentTest.validOptionalReferencesAndUnexpectedFields; its context has no Marquee persistence configured and checks the exact publication set |
| immutable type / authoritative pageId | FragmentLifecycleContractTest.updateRejectsCrossTypeMutationsBeforeAnyWriteOrPublication; UpdateFragmentImageTest.identityKeysMayConfirmButCannotChangeOwnership |
| additive explicit imageId and unchanged aliases/tombstones | RetainedStateDtoContractTest, AddFragmentContractTest |
| reusable Image and isolated Fragment deletion | FragmentLifecycleContractTest.deletingOneSharedReferenceLeavesOtherFragmentAndImageUntouched; existing Step 8/9 database evidence covers actual persistence |
| identical Fragment locking rules | FragmentLifecycleContractTest.sameLockOwnershipConflictAndUnlockContractForBothTypes |
| reference attach/replace/clear | UpdateFragmentImageTest |
| cross-type Marquee operations | FragmentLifecycleContractTest.marqueeHandlersRejectImageShapeWithoutUnlockingOrPublishing; ResolvedFragmentStateTest |
| native projection and nullable IDs | FragmentRepositoryImplTest |
| replay and tolerant legacy reads | DiaryContextTest |
| shared mixed-type chronology | FragmentSequenceNormaliserTest |
| reference conflict, recovery, generic DeleteFile protection | ImageCatalogueDeletionTest, DeleteImageTest, ImageDeletionConcurrencyTest, unchanged DeleteCatalogueTest |

## Validation

Command from the Diaries root:

```powershell
.\gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain
```

**BUILD SUCCESSFUL. 309 discovered, 276 passed, 33 environment-gated skips,
zero failures/errors.** The 13 focused test classes account for **85 passing cases**,
with no skips. Reports are preserved under `unit-reports/`; totals and per-class
counts are in `unit-results.json`. `source-sha256.csv` identifies the tested source.

The initial attempts (`test-build.log`, `test-build-02.log`) are retained for audit.
They identified test fixture issues: MQTT client explicit close, boxed deletion return
signature, typed JPA query proxy, and the legacy handler's numeric (not string) sequence
contract. The final log is authoritative. No application fix was needed.

Gradle emitted its existing deprecation and Shadow service-merging warnings. These did
not fail the build. `git diff --check` passed. Prior uncommitted feature work was preserved.

## Scope and remaining verification

This step deliberately runs without Docker, a database, broker connection, browser or
NAS. Lifecycle fixtures record repository calls, transaction boundaries and retained
publications; they do not emulate PostgreSQL constraints, rollback or locking.
The real database serialization evidence remains in Steps 8/9. The broader database
fixture and live retained-RPC verification in Steps 11/12 remain separate work.
Client builds were not repeated because this step changes only Java test sources and
documentation; Step 9 records the passing client compatibility and production build.
