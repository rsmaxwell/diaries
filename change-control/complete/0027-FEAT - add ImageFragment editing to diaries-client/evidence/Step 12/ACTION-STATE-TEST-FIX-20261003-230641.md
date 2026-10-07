# Step 12 action-state test correction — 2026-10-03 23:06 run

## Observed result

The third normal Windows development-tree run successfully:

- generated the Angular application bundle;
- started Karma;
- launched Chrome Headless;
- executed all 222 discovered tests.

The final result was **221 SUCCESS, 1 FAILED**.

The sole failure was:

`ImageFragmentActionStateService derives selected IMAGE and attached-Image state from retained Fragment truth`

Both positive assertions (`selectedFragmentIsImage$` and `selectedImageHasAttachedImage$`) observed `false` instead of `true`.

## Root cause

This was a test-observation defect, not a production-state defect.

`ImageFragmentActionStateService` deliberately applies `startWith(null)` to the retained Fragment stream. Therefore both derived observables deliberately emit an initial `false` representing "no retained selection has been observed yet" before the harness's `BehaviorSubject` immediately emits its current IMAGE Fragment.

The test used `firstValueFrom(...take(1))`, so it asserted that intentional transient first emission rather than the immediately following derived retained state.

## Correction

The test now keeps subscriptions open for the duration of the case and asserts the latest synchronous derived values after each `BehaviorSubject.next(...)` operation.

This also verifies the transitions:

- IMAGE with positive `imageId` -> selected IMAGE = true, attached Image = true;
- same IMAGE with `imageId: null` -> attached Image = false;
- MARQUEE Fragment -> selected IMAGE = false.

## Production impact

None.

No production TypeScript, template, style, configuration, responder, or RPC contract file is changed by this correction.

## Remaining acceptance action

Rerun:

`npm test -- --watch=false --browsers=ChromeHeadless`

Step 12 can be closed when the standard Angular suite completes green.
