# 0029-FEAT — Annual IMAGE link editing candidate (25 November 2026)

## Scope

Extends the integrated Step 2 candidate with editing of the optional `imageLinkUrl` on a PREAMBLE/POSTAMBLE IMAGE Fragment, without editing catalogue-owned caption or alt text. Uses the established `updateImageLink$` RPC (which applies `UpdateImageLinkRequest` set/clear intent), the same Fragment ID lock and the existing edit cancellation path. An unchanged URL unlocks without updating.

The annual editor still does not allow replacing an annual IMAGE catalogue reference after creation; this operation requires a separately reviewed change and tests. This candidate does not change database migrations, production state or the IMAGE catalogue.

## Evidence and limits

- TypeScript transpile syntax check for changed annual editor component: PASS (zero transpile diagnostics).
- Confirmed existing RpcService.updateImageLink$ and UpdateImageLinkRequest set/clear contract in the source.
- ZIP CRC/integrity check: PASS.
- Full Angular compilation, Java builds, tests, browser end-to-end checks: NOT RUN (node_modules and Gradle distribution unavailable here).

## Required consolidated verification on Windows

Apply this ZIP to an inspected Windows Diaries checkout via Beyond Compare; inspect git branch, revisions, submodule statuses and uncommitted modifications first. Do not execute the SQL or deploy the candidate. Run client `npm ci`, `npm run build`, and `npm test -- --watch=false --browsers=ChromeHeadless`, plus responder/reader Gradle builds and tests using the project's own build commands, then resolve any compiler and integration failures. Test annual TEXT Quill edit/cancel, IMAGE set/clear/unchanged link, locks across two browser tabs, retained MQTT updates, annual creation/deletion/ordering and reader projection.

The 49 development-only Page-less legacy records still require the accepted 0028 disposition before the schema candidate can be executed.
