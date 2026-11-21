# 0051 Step 4 — Editor Day Reader IMAGE media regression

Date: 2026-11-20  
Status: fix prepared; local Angular build, full browser acceptance, Jenkins publication and production redeployment **not yet run**.

## Observation

Following the production deployment of client `0.0.9-build-78`, responder `0.0.9-build-85`, and web `0.0.9-build-9`, the owner observed that existing IMAGE Fragment 2332 (Image ID 3) displayed its Image ID correctly in the Day Reader but only its `hello` text appeared beneath the metadata header. The selected-IMAGE editor reference panel displayed the catalogued image thumbnail. Production image schema and container health were already verified; IMAGE extension writes remained disabled.

## Cause

`diaries-client/src/app/dayview/dayview.component.html` displayed the authoritative IMAGE ID header and rendered the Fragment's `text` HTML, but had no image element or catalogue-image lookup for typed IMAGE fragments. The existing image-reference editor component handled metadata and image URLs, but that component was only used in the editor controls, not the Day Reader.

## Correction

- Resolve catalogue metadata for each IMAGE Fragment independently through `ModelContext.getLiveImage$(imageId)`; do not depend on selected IMAGE state.
- Build the static Files URL with the existing `buildCatalogueImageUrl()` utility and runtime configuration.
- Render catalogued media directly below the fragment metadata and above its transcription text; retain the `Image ID: N` label.
- Preserve optional HTTP/HTTPS fragment-owned external links with `safeImageLinkUrl()` and stop click/Enter propagation to the fragment navigation handler.
- Present a non-clickable unavailable state for a referenced Image with missing metadata; render no catalogue image for MARQUEE or unattached IMAGE records.
- Keep the existing legacy HTML/embedded-image rendering, Marquee behaviour, selection and drag-to-reorder unchanged.
- Cover mixed days, multiple distinct Image references, updates to retained catalogue metadata, external click isolation, unsafe links and unresolved metadata in Angular component tests.

## Scope

Only four files under `diaries-client/src/app/dayview/` are changed (`.ts`, `.html`, `.scss`, `.spec.ts`), plus this report. No responder, web reader, database, Ansible, NAS, backup, existing record or write-gate changes are included.

## Verification performed before packaging

- TypeScript syntax/transpilation via installed TypeScript 5.8.3: **PASS** for component and spec files.
- Static binding checks for image placement, URL binding, URL safety, click/keyboard isolation, legacy HTML preservation and responsive sizing: **PASS**.
- Source-snapshot and ZIP integrity/checksums: **PASS** at packaging.

The Angular build, Karma/Chrome Headless suite and live production browser regression were **not** executable from this source-only bundle (Angular `node_modules` not included). They must be performed in the Windows working copy after inspecting/applying the patch.

## Acceptance and release

1. Review/apply the repository-relative ZIP through Beyond Compare 4, preserving any later local modifications.
2. Run the Angular production build and Day Reader tests on Windows; resolve failures before publication.
3. Commit/push the client change and update the Diaries parent submodule pointer using the normal source-control workflow; publish a new **client-only** Jenkins image.
4. Update the client image tag in Playbooks, leaving responder build-85, web build-9 and `diaries_image_fragment_extensions_writes_enabled: false` unchanged; deploy and check container health.
5. Recheck Fragment 2332 in the Editor Day Reader: map displayed directly below `Image ID: 3` and above `hello`; check a legacy MARQUEE, a genuine IMAGE with link, and Reader behaviour.
6. Do not activate extension writes or close Step 4 until the corrected published client and browser acceptance have passed. Existing tested rollback evidence remains valid for the pre-activation boundary.
