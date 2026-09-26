# 0024 Phase 6.1 — staging

Implemented 2026-09-13. This completes the code implementation of 6.1; 6.2
catalogue conflict rules and 6.3 Image creation/publication remain separate work.

## Changed files

All Java paths below are relative to the responder's
`src/main/java/com/rsmaxwell/diaries/responder/` directory.

| File | Change |
| --- | --- |
| handlers/UploadFile.java | Resolve Files root through ImagePathPolicy, bound base64 input, decode to shared private staging, reuse streaming hash, inspect before promotion and clean up rejected/conflicting uploads |
| utilities/ImageCatalogueService.java | Add staging-only construction and private mount capability probe; reject unsafe POSIX staging permissions |
| handlers/ListFiles.java | Hide reserved staging and reject path/symlink aliases through shared policy |
| handlers/DeleteFile.java | Reject reserved staging and path/symlink aliases; avoid creating directories on rejected deletion |
| Responder.java | Protect both HTTP static routes with the shared path policy |

The responder README and implementation checklist describe the integration and
deployment requirements. Tests add `UploadStagingTest` and `StagingHttpTest`.
The packaged inspection probe now also exercises the filesystem capability
check. No client source, database schema, retained topic contract or deployment
configuration changed.

Authentication, active-account and editor authorization still precede file work.
The upload limit remains 20 MiB. Basic base64 rejects invalid characters and
trailing data after padding. Missing/blank optional SHA-256 remains accepted;
a supplied nonblank hash must match. Supported image bytes are fully inspected
even for octet-stream input. Generic octet-stream bytes remain accepted.

The response still contains `name`, `subdir`, `size`, `path` and `url`.
Canonical subdirectory separators are `/`. Successful uploads still use generic
file promotion; this phase does not insert Image rows or publish MQTT topics.
File extensions are not renamed. Existing files survive staging rejection.

Before decoding, disposable private files verify hard-link creation, atomic
move and locking support on the upload mount. Failure rejects the upload.
These checks cannot establish multi-host NAS locking reliability or identify
which Windows ACL principals are trusted. Before deployment, the operator must
verify server-only root ownership/ACLs and exclude staging from any separately
managed HTTP/static server. Such production configuration is outside this
workspace. Local validation did not access or modify live NAS data.

## Validation

* `responder-build.txt`: `gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain` succeeded.
* JUnit reports: **180 passed, 17 skipped, zero failures/errors** (197 discovered).
  The skipped tests require opt-in PostgreSQL/MQTT fixtures; they were not
  enabled for this staging-only change. No database/publication code path was
  activated. Existing Phase 5 integration evidence remains unchanged.
* Six new tests exercise authenticated handler requests, response fields,
  generic bytes, malformed/trailing base64, negative/mismatched size, checksum
  and MIME mismatch, truncation, traversal, cleanup, conflict preservation,
  authorization and reserved-directory list/delete guards.
* The HTTP test starts a real loopback server and checks GET/HEAD against
  literal, encoded, case-alias and traversal staging paths, with an ordinary
  public file as a positive control.
* `client-tests.txt`: all **8** existing Angular file-RPC compatibility tests
  passed in ChromeHeadless (`file-rpc-compatibility.spec.ts`).
* `client-build.txt`: `npm run build` succeeded.
* `packaged-windows.txt` and `packaged-linux.txt`: current fat-JAR decoder,
  portable-path, filesystem capability and rollback probes passed. Linux used
  cached Java runtime `rsmaxwell/diaries-responder:0.0.9-build-76`, a read-only
  local JAR mount, no network and temporary storage.

Existing Gradle/Shadow warnings remain. No live deployment, database or broker
was restarted. No commit or push was performed. Source remains authoritative
in the responder; `reports/` and logs are frozen validation outputs. SHA256SUMS
records all evidence files except itself, with text conversion disabled.
