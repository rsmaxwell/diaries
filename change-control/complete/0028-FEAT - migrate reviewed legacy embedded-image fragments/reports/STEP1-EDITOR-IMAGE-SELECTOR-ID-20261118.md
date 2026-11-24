# 0028 Step 1 — Editor Image selector shows catalogue IDs (2026-11-18)

## Motivation
The 0028 human reviewer identifies an Image by the persisted catalogue Image ID, but the Diaries Editor's Image selection dialog currently shows the image filename followed by its EXIF date in thumbnail modes. This makes mapping a file such as `img2840-image-map-whitley-park.jpg` to Image ID `3` unnecessarily difficult.

## Change
The Angular `FilesListDialogComponent` already receives `FileEntry.imageId` in `listFiles` results. In `selectionMode: 'catalogue-image'` only, display **Image ID: N** directly below the filename in small, medium, large, list and details views. The tooltip and accessible name also include the ID.

- No new RPC or backend change.
- Files without a valid, positive catalogue Image ID remain unselectable and never acquire a fabricated ID.
- Ordinary file browsing/selection continues to show the original image dates and names; neither the historical file-selection return contract nor the catalogue-image selection payload changes.
- Image ID is not extracted or guessed from the filename (`img2840` is a page/image filename token, not the Image catalogue primary key).

## Verification
- Checked the changed TypeScript sources for syntax by transpiling them with TypeScript 5.8-compatible syntax options: PASS.
- Checked the template's ID rendering branches and generic-date fallback with source assertions: PASS.
- Updated the existing `files-list-dialog.compatibility.spec.ts` to verify the catalogue ID appears in every view mode, the tooltip/accessible name includes it, disabled uncatalogued files remain disabled, the selected Image payload stays the same, and generic file selection continues to display the date.
- Angular/Karma suite and browser visual verification: **not run in the source-bundle environment**; required on the Windows development checkout before acceptance.

## Git / review requirements
The application uses `diaries-client` as an independent Git submodule; commit the client changes inside that submodule before updating the parent pointer. Compare the ZIP with local Windows changes before applying. Preserve local uncommitted work and all unrelated feature evidence. The latest supplied source bundle is a snapshot, not a verified checkout revision; check the branch, commit and status of the working repositories before applying or testing.

## Status
Implementation proposed; no production deployment or acceptance claimed. The change is an editor usability enhancement that supports 0028 Step 1 reviews; it does not change the migration review or execution contract.
