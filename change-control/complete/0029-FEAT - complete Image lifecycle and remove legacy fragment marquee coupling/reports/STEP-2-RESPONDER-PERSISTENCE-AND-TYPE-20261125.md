# 0029 Step 2 — Responder persistence and TEXT type candidate (25 Nov 2026)

Status: **source candidate, not deployed or integrated**. Based on Diaries bundle `diaries-sources-20261125-123246.zip`. The previous responder foundation candidate is included in full; this package supersedes it and should not be overlaid with an independent version of that package.

## Changes

- Adds `diary_id` and `placement` to native Fragment repository select/insert/update mapping, including the special queries used for lock recovery and Marquee discovery. DTOs and JPA entity from the foundation candidate are included.
- Introduces enum `FragmentType.TEXT` in place of content type `MARQUEE` and updates direct responder enum references in handlers and utilities. This does **not** rename the separate `Marquee` entity or `diaries/marquees` topics.
- Preserves existing Image Catalogue ownership of caption and alt text and the Fragment image-link field.

## Must be completed before application or deployment

1. Finish RPC validation and creation/update flows for annual Fragments; ensure DATED gets a matching Diary identity, and PREAMBLE/POSTAMBLE do not receive Page or Marquee.
2. Handle MQTT alias removal/republication on placement, year or Diary changes. The current `FragmentPublishDTO` topic calculation does not itself remove old retained aliases.
3. Implement client and public-reader TEXT type/placement support, including annual reader projection and editor operations; update automated tests.
4. Integrate removal of persisted `Marquee.page_id` across responder repository, DTOs and publishers.
5. Reconcile development-only 49 Page-less legacy HTML Fragments against 0028; do not execute the production-shaped SQL candidate in development.
6. Run full responder/client/reader builds and integration regression against migrated development database prior to any production update.

This candidate contains **no database execution**, no production deployment and no claim of passing full builds or tests. Source-bundle snapshots contain no verified Git metadata, so apply only after checking actual working-tree revisions and uncommitted changes.
