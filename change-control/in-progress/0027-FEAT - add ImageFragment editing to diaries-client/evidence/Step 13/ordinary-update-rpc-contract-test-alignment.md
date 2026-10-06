# Step 13 follow-up — align ImageFragment RPC contract tests after null-marquee fix

## Result

The production correction that removes `marqueeId` from `UpdateFragmentRequest` compiled successfully, but the first full Angular run reported two failing tests in `src/app/mqtt/image-fragment-rpc.spec.ts`.

Both failures were stale expectations, not production regressions:

- `keeps ordinary IMAGE updateFragment requests in preserve mode with imageId omitted` still expected `marqueeId: null`;
- `sends a positive imageId only through deliberate IMAGE replacement` still expected `marqueeId: null`.

Those expectations describe the exact wire shape that Step 13 intentionally removed because mqtt-rpc's immutable argument map rejects explicit null values.

## Correction

Only `image-fragment-rpc.spec.ts` changed. The tests now assert:

- ordinary IMAGE update: `imageId` absent, `marqueeId` absent;
- positive IMAGE replacement: positive `imageId`, `marqueeId` absent;
- IMAGE clear: explicit `imageId:null`, `marqueeId` absent.

The `ImageFragment` response/retained fixture still contains `marqueeId:null`; that is valid model state and is intentionally unchanged.

## Production impact

None. No production source changed in this follow-up.

## Next verification

Run:

```bat
npm test -- --watch=false --browsers=ChromeHeadless
```

The expected result is all 224 tests passing. Then repeat the live Phase A IMAGE Fragment text save on Fragment 2332 with the responder authoring gate disabled.
