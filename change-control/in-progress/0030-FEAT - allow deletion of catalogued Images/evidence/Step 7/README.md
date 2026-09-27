# 0030 Step 7 — Files-dialog context menu

Completed 2026-09-27.

## Changes

- Files dialog TypeScript imports CdkMenuModule, filters non-directory image filenames (JPEG, PNG, GIF, WebP, BMP, TIFF; case insensitive), and emits a typed deleteImageRequested event containing name and raw root-relative subdir.
- HTML attaches the CDK context-menu trigger to file cards shared by all five view modes. Directories have no trigger; other files retain their native browser context menu. The menu offers Delete image. Existing normal-click selection/open behaviour is unchanged.
- SCSS styles the overlay menu using existing diary colours, with hover/focus treatment.
- Nine component tests cover five view modes, excluded items, action selection, Escape dismissal, and root-path/eligibility guards. Existing compatibility tests continue to cover ordinary selection and navigation.

The menu-selection event is the Step 8 integration point. It currently has no deletion consumer: selecting the action closes the menu and emits the event only. Confirmation, RPC execution, duplicate-submit protection, directory refresh and error handling remain Step 8. No responder, RPC or retained-state contract changed. Extension filtering is an affordance; responder catalogue and authorization checks remain authoritative.

## Validation

- npm.cmd test -- --watch=false --browsers=ChromeHeadless --progress=false: 122 passed, zero failures.
- npm.cmd run build -- --configuration production: passed. Existing CommonJS optimization warnings for quill-delta and buffer remain.
- Initial test runs exposed mock-list timing problems; the fixture now delivers asynchronously like RPC and waits for rendering before interaction.
- Git diff --check passed.

Tests use the real CDK overlay and DOM events in headless Chrome with a mocked file listing. No live deletion or manual visual/browser session was performed. No database, NAS, deployment, configuration or responder changes were needed.

See client-tests.log, client-production-build.log and source-sha256.csv. Existing uncommitted changes were preserved; nothing committed or pushed.
