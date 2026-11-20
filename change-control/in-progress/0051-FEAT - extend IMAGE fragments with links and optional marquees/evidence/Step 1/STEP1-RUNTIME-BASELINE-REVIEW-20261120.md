# 0051 Step 1 — Local runtime regression baseline review (20 November 2026)

**Result: PASS for the selected existing-code tests. Step 1: CLOSED after explicit owner contract and coverage-boundary approval on 20 November 2026.**

This review records the **owner-provided Cygwin terminal output**, not a test execution by the author of this report. The underlying full raw logs remain on the owner's Windows checkout in the ignored `evidence/Step 1/private/` directory and are not included in the ZIP.

## Local execution baseline

The prior Windows checkout inspection reported the following pinned source revisions; no new source-revision verification was included in the runtime-test logs:

| Submodule | Revision |
|---|---|
| diaries-client | `89c9d539d79bd6b235ab28aa55ea600c86aa4fce` |
| diaries-responder | `bd65d08435c0f5d240337cd6479cb41befe4d8c1` |
| diaries-web | `cc147426e93ee6952558b65147e444d38316b3ce` |

The earlier read-only production inspection captured responder `0.0.9-build-84`, client `0.0.9-build-77`, and web reader `0.0.9-build-8` as running and healthy. Those are **production container versions**, not the Windows test build versions. The responder's local test build generated `0.0.9-SNAPSHOT` build information.

## Runtime test evidence

The owner ran targeted test commands in the Windows Diaries checkout and then displayed the saved log tails. The terminal summary reported PASS for all three groups; the subsequently inspected log contents verified:

| Test group | Underlying saved log | Confirmed outcome |
|---|---|---|
| Responder Gradle `:diaries-responder:test` | `private/step1-responder-runtime.log` | `> Task :diaries-responder:test`; `BUILD SUCCESSFUL in 6s`, six actionable tasks (3 executed, 3 up-to-date) |
| Web reader Gradle `:diaries-web:test` | `private/step1-web-runtime.log` | `> Task :diaries-web:test`, `:diaries-web:jacocoTestReport`; `BUILD SUCCESSFUL in 14s`, seven actionable tasks (6 executed, 1 up-to-date) |
| Angular Chrome Headless | `private/step1-client-runtime.log` | `Chrome Headless 157.0.0.0`; `Executed 39 of 39 SUCCESS`; `TOTAL: 39 SUCCESS` |

The Java Gradle output does not state per-class test counts. The selected class filters came from the submitted command; JUnit XML was not reviewed. These results show that the selected existing tests pass; they do **not** demonstrate that future `IMAGE`+Marquee or URL-write functionality already exists.

Warnings observed: Gradle 9.6.1 reported deprecated features in the responder build; web-reader compilation reported deprecated API usage in `ProjectionServiceTest.java`. No build failure resulted. These warnings are follow-up maintenance, not Step 1 blockers.

## Static source tests and production inspection

* Windows Cygwin Python **3.7.12** ran the corrected `tests/step1-static-baseline.py`: **12 source-baseline checks PASS, 0 FAIL**. The owner retained its dated raw output in `private/step1-static-baseline-*.log`.
* The live production inspection at **2026-11-20 10:47:37 UTC** found five production containers running and healthy, existing `imageFragmentWritesEnabled=true`, and the current Fragment/Marquee constraints. The read-only PostgreSQL transaction ended in `ROLLBACK`. See `STEP1-LIVE-BASELINE-REVIEW-20261120.md`.
* The database has **no `fragment.image_link_url` column** yet and **no cross-table database constraint** ensuring `marquee.page_id = fragment.page_id`; those remain proposed implementation items, not existing guarantees.

## Coverage limits and next step

These were selected existing-code unit/component tests and read-only production inspections. **No isolated database/MQTT integration run, new 0051 code, schema migration, live new-feature test, deployment, or historical legacy conversion occurred.** The comprehensive cases in `STEP1-TEST-MATRIX.md` (e.g. U01–U09, M01–M07, R01–R05, D01–D02) are still acceptance tests for Steps 2–4, not marked as passed here.

Step 1 now has the baseline evidence needed for contract review. **Owner decision recorded 20 November 2026:** the owner explicitly approved the updated cross-component contract decisions and testing boundary; **Step 1 CLOSED**. The accepted boundary leaves all new-feature database/MQTT integration and deployment work for Steps 2–4. The 0028 migration remains paused.
