# 0026 Step 2 - Define the Image reader contract and degraded states

Implemented 2026-09-28.

## Scope

Step 2 is a contract-definition step. This implementation deliberately adds no Image subscription, decoder, projection map, rendering, Files URL, ACL change, database change or authoring capability.

The authoritative contract is:

- [`../../IMAGE-READER-CONTRACT.md`](../../IMAGE-READER-CONTRACT.md)

The machine-readable table-driven fixture is:

- `diaries-web/src/test/resources/fixtures/image-reader-contract-cases.json`

The executable contract anchors are:

- `diaries-web/src/test/java/com/rsmaxwell/diaries/web/mqtt/ImageReaderContractDefinitionTest.java`

## Decisions frozen by this step

1. Retained Image metadata contains only `id`, `version`, `relativePath`, `mimeType`, `originalFilename`, `width`, `height`, `checksum`, `caption`, and `altText`; unknown additive fields are tolerated.
2. Zero bytes mean tombstone. JSON `null` is malformed data, not a tombstone.
3. Topic ID and payload ID must match for non-empty Image publications.
4. Image validation mirrors responder `Image` / `ImagePublishDTO`: positive persisted ID and dimensions, non-negative version, canonical NFC relative path, supported MIME, filename-only original name, lowercase 64-hex checksum, and non-null caption/alt text.
5. Reader compatibility maps **absent** caption/alt text to empty string; present strings, including `""` and whitespace-only strings, are preserved as plain text. Explicit JSON null is invalid.
6. IMAGE Fragment `imageId` absent and explicit null are identical `NO_SELECTION` states. Positive IDs are references; non-positive present IDs are invalid.
7. Unknown explicit Fragment types remain distinct from legacy absent/null type. The future implementation must preserve an `UNKNOWN` sentinel plus the exact raw type (or an equivalent representation), keep otherwise valid Page-owned chronology, and never coerce the value to MARQUEE.
8. Media resolution distinguishes `NOT_APPLICABLE`, `NO_SELECTION`, `AVAILABLE`, `MISSING_METADATA`, `INVALID_METADATA`, and `UNSUPPORTED_TYPE`. Browser `FILE_LOAD_FAILED` is separate and does not mutate projection metadata.
9. A malformed live replacement is rejected before projection mutation, increments invalid-message diagnostics, and leaves the last valid active entity in place until a valid upsert or zero-byte tombstone.
10. Fresh reconnect/replay still uses empty staging; malformed retained state is not repaired by copying an old entity into the new generation.

## Executable coverage

`ImageReaderContractDefinitionTest` adds three focused cases:

- absent versus explicit-null `imageId` decode identically for IMAGE Fragments;
- the existing decoder/client failure path leaves a last valid active Fragment unchanged while incrementing `invalidMessageCount`;
- the machine-readable fixture is valid JSON, has unique IDs, contains every required Step-2 category and includes the mandatory null/absent, tombstone, ID-mismatch, unknown-type, invalid/missing metadata, file-load-failure and malformed-replacement cases.

The remaining fixture rows are intentionally forward contract cases. They become direct decoder/projection/rendering assertions in Steps 3, 5, 6, 8-10 rather than being simulated by Step 2.

## Source references

This contract was checked against the current responder and reader source represented by `source-sha256.csv`, particularly:

- responder `model/Image.java` and `dto/ImagePublishDTO.java`;
- web `FragmentItem`, `FragmentType`, `RetainedMessageDecoder`, `MqttProjectionClient`, and `ProjectionService`;
- existing `RetainedContractTest` and `ProjectionServiceTest` behavior.

The 0026 implementation plan was read from GitHub `rsmaxwell/diaries` at commit `37a2a8d9ac57f19dbcc80d1f10a34f1e86adab75` because the previously supplied source bundle predates the addition of 0026 change-control files.

## Completion assessment

The decoder, projection and rendering work now have one explicit shared contract, including the required explicit-null versus absent `imageId` distinction and degraded-state matrix. No Step-3 behavior is claimed as implemented here.
