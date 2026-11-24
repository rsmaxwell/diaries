# 0028 Step 1 — Editor File Browser Compatibility Test Correction (2026-11-18)

## Observed

On 2026-11-18 at 19:58 UTC, the Windows Cygwin run of `npm run build` succeeded, but `npm test -- --watch=false --browsers=ChromeHeadless` reported **228 SUCCESS, 3 FAILED** (231 tests). All three failures are the same compatibility assertion with `additions=true`, across the three `baseUrl` variants.

The original expectations assumed the ordinary File Browser always displayed `2020 Jan 02` beneath a catalogued image and never rendered `.catalogue-image-id`. The updated client intentionally displays `Image ID: 101` as the subtitle when catalogue metadata is available.

## Correction

Update only `files-list-dialog.compatibility.spec.ts` to assert both existing compatibility states:

- **`additions=false`**: no catalogue ID; existing date subtitle is retained.
- **`additions=true`**: `Image ID: 101` appears below the filename, not the date subtitle.
- **Details mode**: the date column remains while the Image ID appears under the filename.

The existing checks for image URLs, folder navigation, selection payloads and the dedicated five-view catalogue display remain unchanged.

No production code, database schema, responder or deployment configuration is changed by this test correction.

## Verification to capture

From Windows Cygwin at the Diaries parent repository root, run:

```bash
(
  cd diaries-client &&
  npm run build &&
  npm test -- --watch=false --browsers=ChromeHeadless
)
result=$?
if [ "$result" -eq 0 ]; then echo 'PASS: Angular build and tests'; else echo "FAIL: Angular build or tests (exit $result)"; fi
```

Do not promote a production image until the full suite passes and the new client commit and parent submodule pin are published.
