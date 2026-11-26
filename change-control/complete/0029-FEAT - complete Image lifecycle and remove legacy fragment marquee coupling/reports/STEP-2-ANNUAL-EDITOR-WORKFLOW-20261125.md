# 0029-FEAT — Annual editor integration candidate (25 November 2026)

## Source baseline

`diaries-sources-20261125-123246.zip`; integrated Step 2 annual creation candidate, with this editor increment layered over it. Git metadata is not present in the archive; Windows checkout branch/revision/dirtiness must be rechecked before applying.

## Added functionality

- A Diary-level annual editorial panel for one selected Diary/year/placement, with retained MQTT subscriptions scoped to the specific annual group.
- PREAMBLE and POSTAMBLE creation of TEXT or IMAGE Fragments through `addAnnualFragment`; image ID and optional validated external link are supported.
- Existing annual text/HTML updates under the existing Fragment edit-lock and optimistic-version protocol.
- Deletion with confirmation, ownership lock and annual-group normalisation via the responder candidate.
- Up/down annual ordering using server-side update and annual normalisation; dated ordering remains isolated.
- Shared request contracts and focused Jasmine tests; Dayview's type label now accepts TEXT.

## Verification performed here

- Source-level review against the latest bundle and the previously integrated candidate.
- TypeScript transpilation syntax checks for new and modified TS sources: passed.
- Package integrity checked after creation.

## Remaining gates / caution

**NOT DEPLOYABLE OR INTEGRATION-VERIFIED.** No Angular node_modules present in this container, so no Angular compilation or Jasmine/Karma tests were executed. Responder/reader Gradle compilation and browser integration remain outstanding. The database migration must NOT be executed independently.

The annual editor currently provides a plain HTML/text source textarea rather than the existing rich-text Quill editor. This is an authoring integration candidate, not final UI acceptance. Existing introductory content must be preserved (particularly links). Annual editor styling, navigation and cross-client reconciliation require browser verification. The existing 49 development-only migrated HTML source Fragments must be dispositioned before final schema enforcement.

Apply as a consolidated candidate only after comparing with the current Windows worktree and confirming submodule revisions. No production/database changes were performed.
