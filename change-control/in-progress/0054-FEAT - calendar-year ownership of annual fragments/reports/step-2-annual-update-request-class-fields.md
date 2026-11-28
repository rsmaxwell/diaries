# 0054 Step 2 — annual update request own-property regression fix

## Evidence
Windows ChromeHeadless regression run 2026-11-28: 289 executed, 288 passed, 1 failed in `src/app/model/fragment.spec.ts`, annual `month` and `day` own-property expectations (lines 125–126). Angular build stage skipped on test failure.

## Cause and fix
TypeScript class field declarations `public month?: number; public day?: number;` may emit own properties initialised to `undefined`, even when the constructor deliberately does not assign them. JSON serialization drops undefined values, so browser Save worked, but `Object.hasOwn()` correctly detects these fields. Change these declarations to `declare public ...`, retaining constructor assignment for dated fragments. This avoids generated own properties for annual fragments. No RPC shape change for DATED updates.

## Verification required
Run `diaries-client/scripts/windows/regression-tests.bat` in Windows Command Prompt. Require 289/289 Angular tests PASS plus `npm run build` PASS. Record output under this feature's evidence. No repeat of previously accepted browser tests is necessary.
