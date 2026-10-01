# Step 14 — Full regression and artifact verification

## Status

**Complete — closed 2026-10-01.**

Step 14 has been completed successfully against the final source and exact
candidate artifacts.

The successful verification evidence is:

```text
build\step14-20261001-080620
```

The complete Step 14 runner ended with:

```text
Step 14: PASSED
evidence: build\step14-20261001-080620
```

## Verification performed

The final verification run included:

1. Step 13 retained-snapshot barrier and failure-diagnostic regression tests.
2. Step 13 public Image HTTP preflight and failure-diagnostic regression tests.
3. Step 13 restart-safe responder/web reverse-proxy routing regression tests.
4. Full `diaries-web` clean test/build and Shadow/fat-JAR generation.
5. Full `diaries-responder` clean test/build.
6. `diaries-client` unit tests and production build.
7. Source-stability verification, excluding intentionally generated build metadata.
8. Compose/artifact inspection and published-image inspection.
9. A fresh fully disposable Step 13 cross-component verification using the exact
   responder/web candidate artifacts built during the Step 14 run.

## Component results

### diaries-web

The clean build completed successfully:

```text
BUILD SUCCESSFUL
16 actionable tasks: 16 executed
```

The focused/full web verification and fat-JAR generation also completed successfully.

### diaries-responder

The full responder build and tests completed successfully:

```text
BUILD SUCCESSFUL
15 actionable tasks: 15 executed
```

The build emitted existing non-blocking deprecation and Shadow service-file warnings.

### diaries-client

The Angular unit suite completed successfully:

```text
Executed 132 of 132 SUCCESS
TOTAL: 132 SUCCESS
```

The production build also completed successfully.

The production build intentionally regenerated:

```text
diaries-client/public/assets/build-info.json
```

That generated build metadata is excluded from the Step 14 source-stability comparison.

## Fresh Step 13 verification

Step 14 rebuilt the exact responder/web candidate JARs and then ran the fully
disposable Step 13 cross-component verification.

The retained-state checkpoints were:

```text
before faults:
    2336 Fragments
    89 Images
    MQTT barrier received

after delete:
    2334 Fragments
    87 Images
    MQTT barrier received

after restart:
    2334 Fragments
    88 Images
    MQTT barrier received
```

The fresh cross-component run concluded:

```text
0026 Step 13: PASSED
```

Its evidence is beneath:

```text
build\step14-20261001-080620\step13-fresh
```

This proves that the exact candidate responder/web artifacts used for Step 14
also pass the real database -> responder -> MQTT retained state -> diaries-web ->
HTTP/browser verification path.

## Published-image inspection

Published-image inspection was requested.

An optional published image that is not available locally is recorded as
unavailable rather than incorrectly treated as an application regression.
Artifact identity verification for the actually published/deployed image remains
part of the deployment gate.

## Non-blocking warnings

The successful run retained several maintenance warnings, including:

- deprecated Java/JPA APIs;
- Gradle deprecation warnings relevant to future Gradle 10 compatibility;
- Shadow JAR duplicate service-file handling warnings;
- Angular CommonJS optimization warnings for `quill-delta` and `buffer`.

These warnings did not cause test, build, artifact, source-stability, MQTT,
browser, or cross-component verification failures and are not blockers for
Step 14.

## Acceptance conclusion

The Step 14 completion condition was:

> all required tests/builds, browser checks and real-MQTT cases pass against
> the exact release candidate; skipped work is not silently treated as
> acceptance.

That condition has now been met:

- web regression/build: passed;
- responder regression/build: passed;
- client tests/build: passed;
- Step 13 regression harness tests: passed;
- fresh real cross-component Step 13 verification: passed;
- source-stability gate: passed;
- artifact/configuration inspection: completed;
- final Step 14 status: passed.

**Step 14 — Full regression and artifact verification is therefore closed.**

## Completion date

2026-10-01
