# 0029-FEAT — Annual creation and consolidated integration candidate (25 November 2026)

## Basis

Source archive: `diaries-sources-20261125-123246.zip` (source only; no Git metadata). This ZIP supersedes the prior Step 2 candidates as a **review baseline**, but is not a deployable release.

## New responder work in this increment

- Registers `addAnnualFragment` RPC, authorises active EDITOR, requires valid `diaryId`, `year`, `placement` (`PREAMBLE` or `POSTAMBLE`), `type` (`TEXT` or `IMAGE`), `sequence`, and text. Accepts an optional catalogue image reference and optional image link for IMAGE.
- Rejects Page/Marquee arguments, calendar date overrides, and an existing Fragment ID.
- Resolves Diary before writing; persists and normalises only the appropriate annual sequence in one owned transaction, using existing `FragmentSequenceNormaliser.normaliseAnnual`.
- Publishes the committed canonical and annual retained Fragment topics and any renumbered annual entries. Warns if publication fails after commit; do not retry creation blindly.
- Corrects `Fragment.getDiaryId()` for DATED Fragments with an inflated Page: derive owner through Page when there is no explicit Diary relation.

Existing lock/unlock/update RPCs work by Fragment ID, but end-to-end verification of annual edits, retained topic transitions and projection is pending. Existing date-only `addFragment` remains Page-based; annual creation is a separate RPC.

## Verification performed here

- Reassembled previous consolidated candidate and both annual normalisation overlays on top of latest source bundle.
- Archive and source-difference checks completed. No production operations or database modifications.
- Attempted `./gradlew :diaries-responder:compileJava --offline`: **BLOCKED** before compilation because Gradle 9.6.1 distribution was not cached and network DNS was unavailable (`UnknownHostException: services.gradle.org`). This is not a compile PASS.

## Outstanding before any deployment

1. Run responder, reader and Angular builds/tests on the Windows checkout.
2. Complete the Angular editor annual UI (create, list, edit, lock, delete, order) and verify reader projection on actual MQTT state.
3. Reconcile 49 development-only legacy HTML Fragments with 0028 records; migrate development and production data separately with guarded preflights/backups.
4. Verify `TEXT` cutover, annual retained-topic lifecycle, Page/Diary ownership constraints, and the removal of redundant `Marquee.page_id`.
5. Recheck compatibility of reader and editor when published together; preserve accepted 0053 lock behaviour.

No Step 2 acceptance gate is closed.
