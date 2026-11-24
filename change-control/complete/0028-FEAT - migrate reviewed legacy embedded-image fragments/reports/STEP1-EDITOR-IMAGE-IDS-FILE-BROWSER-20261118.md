# 0028 Step 1 — Show catalogue IDs in Image selector and ordinary file browser (2026-11-18)

## Purpose

The first implementation showed **Image ID: n** only in `catalogue-image` selection mode. In the Diaries Editor, the **List files** toolbar action instead opens `FilesListDialogComponent` with `data: { path$, select: true }`. Thus the browser seen at `/diary/1/692/85` was not showing IDs despite using the correct Angular development server. This follow-up deliberately extends the presentation to that ordinary browser.

## Changes

- Show `Image ID: n` directly beneath filenames of **catalogued** images in all five modes (`large`, `medium`, `small`, `list`, `details`), both in the regular **List files** browser and the existing catalogue Image selection mode.
- For catalogued thumbnails, replace the less-useful taken-date subcaption with the catalogue ID. In Details view, keep the existing modified/taken date columns, but add the Image ID under the filename.
- Uncatalogued files still display their original taken-date subcaption, if available, in ordinary browsing; they are not assigned a fabricated ID.
- Include the ID in the ordinary file browser's hover title and accessible label.
- Preserve generic selection payload `{ url, name }`, catalogue-image selection payload and selection restrictions; no responder, database or MQTT changes.
- Extend the compatibility test to assert displayed IDs in all five views, and unchanged generic file selection payload.

## Source and checks

Derived from the previously delivered `0028-FEAT-editor-image-selector-id-20261118.zip`, already reported to build and pass 230 ChromeHeadless tests on Richard's Windows checkout. This revised package is statically checked after packaging, but **the new tests and Angular build have not yet been executed on the revised code**.

## Usage

1. Apply the repository-relative ZIP to the Windows Diaries checkout with Beyond Compare 4.
2. Rebuild with `npm run build` and run `npm test -- --watch=false --browsers=ChromeHeadless` in `diaries-client`.
3. Use the Editor toolbar's **List files** icon: the file browser can now reveal Image IDs without creating an Image Fragment. Navigate to the relevant diary's `images` folder (Whitley Park image ID 3 belongs to `diary-1828-and-1829-and-jan-1830/images`, not `diary-1830/images`).
4. If the ID remains absent, inspect whether the file is actually catalogued in the RPC `listFiles` response; missing `imageId` cannot be fabricated by the client.

**0028 Step 1 remains IN PROGRESS. This change performs no migration and makes no production writes.**
