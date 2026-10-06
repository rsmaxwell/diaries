# Step 12 focused unit and compatibility regression matrix

This matrix maps every required Step 12 test area to executable Jasmine coverage in `diaries-client`.

| # | Required area | Executable coverage |
|---|---|---|
| 1 | Null/absent Fragment type remains legacy MARQUEE | `src/app/model/fragment.spec.ts` — `treats a null or absent migration type as legacy MARQUEE` |
| 2 | Image retained projection deserializes correctly | `src/app/model/image-projection.spec.ts` — `deserializes the responder retained Image projection without renaming or dropping metadata` |
| 3 | `selectedImage$` follows `imageId` and tombstones | `src/app/model/model-context.spec.ts` — retained Image relationship tests, including imageId switch and tombstone-to-null |
| 4 | Files chooser returns persisted `imageId` and refuses uncatalogued files | `src/app/files-list-dialog/files-list-dialog.compatibility.spec.ts` — catalogue-image selection test; existing captured additive compatibility cases remain unchanged |
| 5 | `addImageFragment$()` wire payload | `src/app/mqtt/image-fragment-rpc.spec.ts` — positive, omitted and explicit-null creation payload tests |
| 6 | `updateFragment` preserve/set/clear wire payloads | `src/app/model/fragment.spec.ts` plus `src/app/mqtt/image-fragment-rpc.spec.ts` — preserve omission, positive replacement and explicit-null clear |
| 7 | TextPanel IMAGE save omits `imageId` | `src/app/fragment/text-panel/text-panel.component.spec.ts` — ordinary preserve-path IMAGE save |
| 8 | Day-view IMAGE reorder omits `imageId` | `src/app/dayview/dayview.component.spec.ts` — IMAGE reorder preserve-path test |
| 9 | New authoring controls enable/disable correctly across MARQUEE/IMAGE state | `src/app/headers/pageheader/pageheader.component.spec.ts`, `src/app/fragment/image-fragment-reference.accessibility.spec.ts`, and new `src/app/fragment/image-fragment-step12-regression.spec.ts` type-boundary test |
| 10 | Add ImageFragment success/cancel/403 | `src/app/fragment/fragment.component.spec.ts` — add workflow success, cancellation and authoring-disabled cases |
| 11 | Replace Image success/no-op/failure | `src/app/fragment/fragment.component.spec.ts` — replacement success, unchanged Image no-op, cancelled chooser and responder failure |
| 12 | Clear Image confirmation/success/failure | Existing `src/app/fragment/fragment.component.spec.ts` covers confirmation/success/cancel; new `src/app/fragment/image-fragment-step12-regression.spec.ts` covers confirmed clear failure + unlock fallback |
| 13 | Successful update has no redundant unlock | `src/app/fragment/fragment.component.spec.ts` — replace and clear success explicitly assert no fallback/extra unlock |
| 14 | Failed update invokes unlock fallback | `src/app/fragment/fragment.component.spec.ts` plus new confirmed-clear failure regression |
| 15 | IMAGE Fragment delete leaves Image lifecycle separate | `src/app/fragment/image-viewer/image-viewer.component.spec.ts` — deleteFragment-only IMAGE deletion, no `deleteImage$` |
| 16 | Existing MARQUEE create/edit/delete remains compatible | New `src/app/fragment/marquee-fragment-compatibility.spec.ts` covers existing addFragment creation, marquee edit mode and deleteFragment deletion. All 36 pre-Step-12 spec files are byte-for-byte unchanged. |

## Compatibility acceptance

Existing Files and Fragment RPC compatibility remains protected by the unchanged suites:

- `src/app/mqtt/file-rpc-compatibility.spec.ts`
- `src/app/files-list-dialog/files-list-dialog.compatibility.spec.ts`
- `src/app/mqtt/image-fragment-rpc.spec.ts`
- `src/app/model/fragment.spec.ts`

The Step 12 source hash evidence proves these pre-existing spec files were not edited while adding the new coverage.
