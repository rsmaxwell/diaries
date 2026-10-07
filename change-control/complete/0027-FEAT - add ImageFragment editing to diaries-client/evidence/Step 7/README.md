# Step 7 — Add Image Fragment workflow evidence

## Result

Step 7 is complete in source.

The diaries client now exposes a distinct **Add Image Fragment** action and implements the frozen first-release creation workflow without changing the existing MARQUEE creation RPC or introducing an Image-only chronology.

## Implemented behaviour

- Page header exposes a separate accessible **Add Image Fragment** control.
- The control is enabled only when diary, page and selected Fragment provide a valid authoritative page/day context.
- The Files dialog opens at `/<diary>/images` with `selectionMode: 'catalogue-image'`.
- No Fragment lock is acquired while browsing or creating.
- Cancelling the chooser sends no RPC and changes no selection.
- A selected entry must carry a positive persisted `imageId`.
- The active diary/page/Fragment/day context is reread after the chooser closes; changed context aborts creation.
- IMAGE and MARQUEE creation use the same extracted sequence-gap helper.
- The create request uses `addImageFragment` with empty initial text and the selected Image ID.
- Success selects the returned Fragment, clears Marquee selection and navigates using the returned authoritative `pageId`.
- Responder 403 produces the specific authoring-disabled message required by the frozen UX.
- 500/timeout or otherwise ambiguous creation failures are not retried automatically; the UI tells the user to refresh before retrying.
- No local Fragment list is mutated from the reply; retained MQTT state remains authoritative.

## Validation

`focused-typescript-validation.txt` proves the shared authoring-context and sequence helper compiles under strict TypeScript and executes the gap/fallback cases.

`typescript-parse-check.txt` confirms all changed TypeScript source/spec files parse without diagnostics.

`static-contract-check.txt` contains 19 focused source-level guards for the Step 7 workflow and invariants.

`angular-test-attempt.txt` records the attempted focused Angular/Karma run. It cannot start in this sandbox because the source bundle contains no `node_modules`, so the local `ng` executable is unavailable. This is an environment limitation, not a reported green Angular run.

## Baseline

Implementation was applied cumulatively to `diaries-sources-20261003-201800.zip` with the Step 1 through Step 6 0027 drop-in packages overlaid in order. The Step 6 state is therefore the comparison baseline for `changed-files.txt` and the Step 7 source checksums.
