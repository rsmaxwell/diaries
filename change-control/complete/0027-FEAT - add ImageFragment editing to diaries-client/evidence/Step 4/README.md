# Step 4 evidence — typed Files/Image catalogue contracts

Step 4 promotes the additive Image catalogue metadata already used by upload/compatibility tests into first-class TypeScript contracts and an explicit Files-dialog catalogue-selection mode.

It also fixes the current responder/client mismatch discovered during implementation: `uploadFile` returned catalogue identity, while production `listFiles` did not. `listFiles` now enriches catalogued file entries with the same persisted `imageId` and nested Image metadata, leaving uncatalogued files/directories backward-compatible.

Validation in this sandbox:

- PASS — strict TypeScript compilation of the Step 4 model contracts.
- PASS — focused `hasCatalogueImage` runtime smoke test.
- PASS — TypeScript parse/transpile checks for modified Angular/RPC source and tests.
- PASS — static client/responder contract checks.
- NOT EXECUTED — Angular/Karma suite because the source bundle contains no `node_modules` and `ng` is unavailable.
- NOT EXECUTED — responder Gradle test because Gradle 9.6.1 is not cached and the sandbox cannot reach `services.gradle.org`.

The exact failed full-suite attempts are retained in this evidence directory and are not reported as successful tests.
