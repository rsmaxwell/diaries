# 0051 Step 3 — First local regression failure and correction (20 November 2026)

**Status:** Step 3 remains OPEN. This is a corrective follow-up to the initial editor/reader implementation package; it does not modify product application code.

## Original run

- Windows Cygwin runner: `tools/verify-step3-local.sh`
- Evidence directory on the Windows checkout: `evidence/Step 3/private/run-20261120T130225Z/`
- Web reader: main sources and tests compiled, 140 test cases executed, **2 failed**.
  - `WebServerTest.mixedTypedFragmentsRemainAvailableThroughMonthAndSourceHttpResponses`, original line 297.
  - `WebServerTest.step11CoversMixedChronologyDegradedMediaMissingOwnershipAndReadOnlyHttpBoundaries`, original line 378.
- Angular Chrome Headless tests did **not execute**: TypeScript compilation failed at `src/app/model/image-link-contract.spec.ts:34` (TS2345).
- Angular production build: **PASS**.

## Cause and correction

`TestData.readyMixedMediaProjection()` now supplies a valid IMAGE (fragment 35) with a same-Page Marquee (46) and a safe external link. Two pre-existing HTTP test methods still asserted that this IMAGE had *no* Marquee. They consequently expected Fit selection and highlight controls to be disabled, the original-page text instead of the source-region text, and no Marquee selector on the source page.

Updated only those WebServerTest expectations to require the correct, approved 0051 behaviour: IMAGE fragment 35 retains `hasMarquee=true`; the viewer can fit/highlight the selected region; the source page contains `data-marquee-fragment="35"`; source-page selection is a separate action. The tests continue to protect against unsupported media, unowned fragments, invalid metadata and unsafe URLs.

The Angular test fixture is intentionally typed `Fragment`, for which `imageLinkUrl?: string | null`; the Jasmine `toBe` inference rejected an optional string as its expected argument. The assertion now checks against the fixture's explicit URL string. Application source and runtime validation logic remain unchanged.

## Verification boundary and next action

- Corrections reviewed against the actual Step 3 sources and template conditions in the prior ZIP.
- Java/Angular full test suites **not executed in the packaging environment**.
- Apply this small ZIP to the authoritative Windows checkout with Beyond Compare, without overwriting other dirty submodule files.
- Run `bash "$feature/tools/verify-step3-local.sh"` from the Windows Diaries parent after setting `feature` as in the original Step 3 instructions. The runner writes a **new** timestamped run; retain `run-20261120T130225Z` as failure evidence.
- Inspect any remaining failures before deciding Step 3 acceptance. No production deployment and no Step 2 acceptance reruns.
