# 0025 Step 4 — Generalise Fragment aggregate resolution and persistence

Completed 2026-09-27. Existing Step 3 changes were preserved; no commit or deployment.

## Changes

- Replaced `FragmentAndMarquee` with `ResolvedFragmentState`: Fragment, optional Marquee and resolved Image, with explicit writer validation.
- `DiaryContext.saveMarqueeFragment` requires MARQUEE, no Image reference, and a Marquee using the same Fragment/Page. `AddFragment` now uses this method.
- `saveImageFragment` requires a new IMAGE Fragment with a Page and zero/one existing Image. A new Fragment cannot already have a database Marquee; this path never creates one.
- Both helpers own a transaction, reject joining a caller transaction, return committed copies, and preserve caller candidates on failure. A failed second insert rolls back the first.
- `lockImageForFragmentWrite` requires an active transaction and a positive existing Image ID (or null), using JPA PESSIMISTIC_READ to serialize attachment with database deletion.
- `inflateFragment` resolves Image metadata. `resolveFragmentState` resolves the optional Marquee using the same Fragment instance. Missing Image metadata logs a warning and preserves its ID; replay does not discard the Fragment. Writer validation rejects unresolved or cross-type relationships.
- Updated aggregate callers in AddFragment, UpdateFragment, LockFragment, UnlockFragment, FragmentLocking and responder stale-lock release. Replay uses the common resolver. Existing RPC payloads and retained JSON remain unchanged.
- Reused the existing robust transaction helper for both Image and Fragment creation; transaction begin/commit/rollback handling and rollback exception preservation remain centralized.

## Verification

Full responder test/build passed (`final-test-build.log`): **269 discovered, 241 passed, 28 environment-gated skips, zero failures/errors**. See `unit-results.json`.
The first full run exposed an incomplete Page builder in the new unit fixture, corrected before the successful final run; its log is retained.

Separate PostgreSQL integration: `ImageWiringIntegrationTest.fragmentCreationResolutionRollbackAndImageLocking`, **one passed, zero skipped**. See `verified-run/result.json` and `integration-test.xml`. `run-01` is the earlier passing run.

The runner restores the frozen 0024 backup into an owned PostgreSQL 18 container, applies the Image and 0025 schemas, then verifies:

- IMAGE creation with/without an Image and two fragments sharing one Image;
- MARQUEE creation and aggregate resolution;
- missing Image/type/cross-type rejection;
- transaction rollback after an injected Marquee-insert failure;
- caller objects remain unchanged and nested transaction ownership is respected;
- replay retains fragments without a Marquee;
- on a second connection, a DELETE times out while the Image PESSIMISTIC_READ lock is held, and proceeds after release (the probe deletion is rolled back).

After fixture cleanup, Diary/Page/Fragment/Marquee/Image row counts and hashes match their initial values. The container is removed. Sequence advancement is confined to this disposable fixture. No live database, MQTT broker or NAS content is modified.

Unit tests also cover degraded replay with missing Image metadata and rejection of IMAGE+Marquee, MARQUEE+Image, mismatched Page/Fragment and missing type. Existing retained DTO and sequence tests passed.

## Boundaries

Step 5 still owns the public retained `imageId` contract. RPC authoring/update semantics, full workflow generalisation and referenced-Image deletion guards remain later steps. The demonstrated database locking primitive is not the complete filesystem-aware DeleteImage guard; no new authoring RPC is enabled here.

Client/web sources and runtime configuration were unchanged; their builds were not rerun. Existing Gradle/Shadow warnings and native-query deprecation warnings do not fail the responder build. The already-applied development Step 2 migration remains the startup prerequisite. No additional schema migration is needed for Step 4.
