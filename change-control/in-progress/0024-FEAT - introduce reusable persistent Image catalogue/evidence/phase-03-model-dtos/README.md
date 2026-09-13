# 0024 Phase 3.1: Image model and DTOs

Implemented on 2026-09-12. Responder source added:

- `model/Image.java`: extends Base; maps the eight metadata fields explicitly
  to the Phase 2 columns; inherited id/version retain the existing mappings.
  String checksum uses JDBC CHAR with length 64, matching the existing SQL.
- `dto/ImageDBDTO.java`: persistence metadata, constructors from the model and
  publish DTO, JSON helpers and explicit validation.
- `dto/ImagePublishDTO.java`: the ten-field metadata projection, constructors,
  JSON helpers, map/MQTT publication and tombstones using the existing Publisher.
- `src/test/java/com/rsmaxwell/diaries/responder/dto/ImageDtoTest.java`:
  ten focused conversion, validation, mapping and publication contract tests.

The three types follow the existing Lombok no-argument/builder and Base
conventions. Caption and alt text default to empty strings and reject explicit
nulls. Relative paths are Strings; no platform Path, file bytes, absolute URL,
Fragment/Page ownership, or java.awt.Image is included.

`Image.validate()` rejects absent/invalid metadata: non-NFC paths, absolute,
drive-qualified and URL-like paths, backslashes, empty/dot/traversal segments,
control characters, unsupported MIME types, nonpositive dimensions, invalid
lowercase SHA-256 shape, invalid original filename, negative/null version and
nonpositive assigned identity. It preserves valid Unicode, spaces, percent,
underscore and case. Validation rejects noncanonical input rather than silently
rewriting it. An unsaved model/DB DTO may have a null id; publication requires
a positive persisted id.

Validation is invoked by conversions, DTO JSON serialization/publication and
JPA pre-persist/pre-update callbacks. It is available for the later service
boundary. It does not prove filesystem containment or that metadata describes
actual image bytes: safe real-path resolution, symlink checks, normalization
and image decoding remain the Phase 5 service responsibilities. Database MIME,
dimension, version and checksum constraints are unchanged from Phase 2.

Publication uses only `diaries/images/{id}`, once per call, through Publisher
with QoS 1 and retained=true. Map removal and MQTT zero-byte retained tombstones
need only the id, so deleting retained state does not require complete metadata.
Serialization uses Jackson UTF-8 bytes, and tests check Unicode payload values.
The exact JSON fields are id, version, relativePath, mimeType, originalFilename,
width, height, checksum, caption and altText.

Validation commands (Diaries repository root):

```powershell
.\gradlew.bat :diaries-responder:test --tests com.rsmaxwell.diaries.responder.dto.ImageDtoTest --console=plain
.\gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain
```

Both passed. Full suite: 15 suites, 137 tests, zero failures/errors/skips,
including all ten new tests. See [test-results.json](test-results.json) and
[responder-build.txt](responder-build.txt). Existing Shadow service-duplicate and
Gradle deprecation warnings remain.

MQTT tests use the existing recording-client approach and verify actual calls
to Publisher; no broker publication or live database write was performed.
JPA column mappings and callback annotations were checked, but a live Hibernate
round trip remains with repository/registration tests in 3.2/3.3. No client,
web, database schema, NAS or deployment configuration changed. The entity is
not yet registered in GetEntityManager and database replay is not wired; those
are later sections. Existing consumer contracts remain unchanged.

`SHA256SUMS.txt` records hashes of this evidence and the added Java source/test
snapshot. No commit or push was performed.
