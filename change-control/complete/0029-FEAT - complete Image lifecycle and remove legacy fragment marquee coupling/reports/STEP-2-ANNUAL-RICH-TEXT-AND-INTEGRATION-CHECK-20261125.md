# 0029-FEAT — Annual editor rich text and integration check (25 Nov 2026)

Status: **candidate, not accepted or deployable**.

## Changes in this consolidated candidate

- The annual editor now uses the existing ngx-quill editor for TEXT content, with a constrained toolbar and HTML preview. The previous textarea displayed and edited literal markup.
- IMAGE annual Fragments no longer expose a misleading Fragment-caption editor: caption and alt text remain on the Image Catalogue. IMAGE occurrence continues to own an optional link.
- The addAnnualFragment request validates annual placement/type at runtime, including values arriving from JavaScript that bypass the TypeScript type system.
- Focused Jasmine cases added for the rejected DATED and legacy MARQUEE annual creation inputs.
- Previous responder, reader, Angular and guarded SQL candidates remain consolidated in this ZIP.

## Evidence and limitations

- Verified presence of `QuillModule` and `ngx-quill` in the repository's existing source and package manifest.
- ZIP integrity and targeted structural checks were performed.
- Full Angular compilation/tests: **NOT RUN**. `npm ci --offline` failed `ENOTCACHED` for zone.js 0.15.1. Installing packages from the Internet is unavailable here.
- Java responder/reader compilation: **NOT RUN**; Gradle dependencies were not available in the analysis environment.
- Database migration: **NOT RUN**. The production-shaped script deliberately rejects the 49 additional development Page-less legacy records.
- No claim of RPC end-to-end behaviour, live MQTT reconciliation or functional acceptance.

## Outstanding integrated completion work

1. Compile responder, reader and Angular source in Windows checkout, fixing any actual compiler/test errors.
2. Verify Quill data persistence and cancel/lock lifecycle with two editor windows. Existing TEXT editor lock corrections from 0053 must not regress.
3. Reconcile 49 development-only Page-less embedded-image sources against 0028 and record their disposition; make a development-safe migration.
4. Verify Image catalogue selection UI and annual navigation, annual placement rendering (including POSTAMBLE), and production-shaped migration in a disposable test environment.
5. Address redundant Marquee.page_id removal and all affected repository/DTO consumers as part of the integrated schema cutover.
6. Reconcile old date retained topics and new year topics; check MQTT replay and rollback.

Do not deploy or execute SQL scripts from this package independently.
