# Step 12 evidence — focused unit and compatibility regression coverage

Step 12 adds focused regression coverage before live MQTT/responder verification. It deliberately makes no production-code change.

## Added executable specs

- `diaries-client/src/app/model/image-projection.spec.ts`
  - freezes the retained `diaries/images/<id>` JSON projection and exact client deserialization.
- `diaries-client/src/app/fragment/image-fragment-step12-regression.spec.ts`
  - freezes MARQUEE/IMAGE authoring-control boundaries;
  - freezes confirmed Clear Image failure behaviour, including failed-edit unlock fallback and retained-state preservation.
- `diaries-client/src/app/fragment/marquee-fragment-compatibility.spec.ts`
  - proves existing MARQUEE creation stays on `addFragment`;
  - proves MARQUEE editing stays on marquee edit mode rather than Image mutation;
  - proves MARQUEE Fragment deletion stays on `deleteFragment` and never cascades to `deleteImage`.

## Development-run compilation corrections

The first real Windows development run reached Angular bundle compilation, then exposed two test-source typing defects from earlier 0027 work:

1. `files-list-dialog.compatibility.spec.ts` used a typed `querySelectorAll<T>()` through untyped `fixture.nativeElement`; it now narrows the element to `HTMLElement` first.
2. `image-fragment-reference.accessibility.spec.ts` used an incomplete `CatalogueImage` fixture; the fixture now supplies every required metadata field.

These corrections change test code only. Production client and responder code remain unchanged.

## Execution status

The original sandbox could not run Angular because it had no `node_modules`. The subsequent normal development-tree run on 2026-10-03 proves the Angular runner starts correctly and reaches compilation; its exact output is preserved in `development-angular-test-attempt-20261003-225828.txt`.

That run did **not** execute the Jasmine suite because compilation stopped on the two test-source issues above. The fixes are now supplied. Step 12 therefore remains open until the standard Angular suite is rerun and passes.

## Second development run — runtime-test corrections

The next real Windows development run successfully built the Angular bundle, launched Karma/Chrome Headless and began the 222-test suite. It found two test-fixture timing/state defects:

1. `image-fragment-reference.component.spec.ts` was resolving its assertion as soon as retained Image metadata appeared, before asynchronous runtime configuration had produced the static URL. It now waits for `imageUrl`.
2. `fragment.component.spec.ts` replaced the retained "already-current" fixture with an object that omitted the lock. It now preserves the harness's post-lock retained metadata while changing only the requested Image reference.

These are test-only corrections. No production client or responder source is changed. The exact run is preserved in `development-angular-test-attempt-20261003-230245.txt` and the diagnosis is in `RUNTIME-TEST-FIX-20261003-230245.md`.

Step 12 remains open pending one more standard Angular rerun.

## Third development run — final action-state test correction

The next Windows development run successfully built the bundle, launched Karma/Chrome Headless and executed all 222 tests. The result was **221 SUCCESS, 1 FAILED**. The sole failure was the `ImageFragmentActionStateService` retained-state test.

The service intentionally begins its derived retained-selection observables with `false` via `startWith(null)`. The test incorrectly used `firstValueFrom(...take(1))`, so it asserted that transient initial value instead of the immediately following `BehaviorSubject` IMAGE value. The test now subscribes for the case duration and asserts the latest synchronous derived state.

This correction is test-only; production source remains unchanged. The exact run is preserved in `development-angular-test-attempt-20261003-230641.txt` and the diagnosis is in `ACTION-STATE-TEST-FIX-20261003-230641.md`.

Step 12 remains open pending the final standard Angular rerun.


## Final development-tree runtime result — 2026-10-04

The final rerun completed the full Angular/Karma suite with **222/222 tests passing**:

```text
Chrome Headless 154.0.0.0 (Windows 10): Executed 222 of 222 SUCCESS
TOTAL: 222 SUCCESS
```

Evidence: `development-angular-test-green-20261004-001033.txt`. Step 12 is closed.
