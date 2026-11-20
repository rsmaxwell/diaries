# 0051 Step 2 — initial responder test-compilation failure

**Status:** OPEN — corrective test-only patch prepared 20 November 2026; owner rerun pending.

## Recorded test outcome

Owner executed `./gradlew --no-daemon :diaries-responder:test` in Windows Cygwin and captured `evidence/Step 2/private/step2-responder-tests.log`. Responder `compileJava` passed; `compileTestJava` failed with **2 errors and 7 deprecation warnings**. Consequently the responder JUnit suite did not run. No live migration, application deployment, PostgreSQL modification or MQTT integration occurred in this stage.

- `utilities/FragmentSequenceNormaliserTest.java:175`: missing JUnit Jupiter static import of `assertDoesNotThrow`.
- `utilities/ImageLinkWritePolicyTest.java:45`: Java generic type inference for a `List.of(Map.of(...))` of heterogeneous value types did not satisfy `Map<String,Object>`.

The seven `jakarta.persistence.Query` deprecation/removal warnings relate to existing integration-test code and are **not** the compilation cause; Gradle also emits deprecation warnings.

## Corrective change

Only two responder **test** source files are changed: add the missing static import and use explicit `Map.<String,Object>of(...)` type witnesses. Production Java code, migrations, feature gates, unrelated 0028/0029 edits, and existing Step 1 evidence are unchanged. This is an incremental patch: the earlier `STEP2-UPDATE-MANIFEST.txt` is preserved as a receipt for its original package, rather than rewritten.

## Next verification gate

After applying the repository-relative ZIP to the **Windows** Diaries checkout and reviewing differences with Beyond Compare 4, run the same full responder tests again:

`./gradlew --no-daemon :diaries-responder:test`

Capture full output to `evidence/Step 2/private/step2-responder-tests-rerun.log`. If it passes, inspect Gradle/JUnit summaries and proceed to isolated database/MQTT integration. **Do not mark Step 2 CLOSED or deploy to production until the remaining integration criteria are accepted.**
