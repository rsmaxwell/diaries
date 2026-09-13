# 0024 Phase 5 — shared services evidence

Implemented and verified on 2026-09-13. Phase 5 is complete. UploadFile and
DeleteFile adoption is reserved for Phases 6/7; no RPC payload or client/web
behaviour changed in this phase. Existing Phase 4 work and evidence were preserved.

## Implementation

The responder adds five utilities under
`src/main/java/com/rsmaxwell/diaries/responder/utilities/`:

| File | Responsibility |
| --- | --- |
| ImagePathPolicy.java | NFC, portable separators, canonical paths, case/Unicode alias checks, traversal and symlink/reparse rejection |
| ImageMetadataInspector.java | Byte-derived JPEG/PNG/GIF/WebP identity, full decoding, positive dimensions, SHA-256 and bounded resource usage |
| InspectedImage.java | Immutable validated supported-image metadata |
| ResolvedUpload.java | Immutable staged file, target, original name and inspection result |
| ImageCatalogueService.java | Private staging, ownership checks, file locking, no-replace promotion, committed registration, compensation and publication |

The parent version catalogue and responder build add TwelveMonkeys WebP 3.14.0
([upstream release](https://github.com/haraldk/TwelveMonkeys/releases/tag/twelvemonkeys-3.14.0)).
No native decoder installation is needed. Test fixtures are synthetic 16x12
images generated with the included optional Pillow script; Gradle uses the
committed bytes and does not require Python. Extensions are neither trusted nor
changed. Existing NAS extension mismatches remain reconciliation findings.

Default limits are 20 MiB encoded bytes, 40 million decoded pixels across frames
and 256 frames. GIF dimensions describe its logical canvas. Image MIME mismatch,
container truncation, PNG CRC corruption, decoder warnings, zero dimensions and
checksum mismatch reject the image. Unsupported octet-stream content returns a
generic-file result and creates no Image row.

Staging computes SHA-256 while writing. Inspection trusts that hash only through
the package-private staging API. The public inspector hashes the bytes itself.
Promotion uses hard-link creation, which fails if the target already exists;
plain ATOMIC_MOVE without replacement is not assumed to provide that guarantee.
An uncatalogued overwrite is first moved atomically to a private backup.
Operations share a process critical section and an OS file lock.

The JPA adapter creates one EntityManager per call and uses the existing
PostgreSQL `pg_unicode_fast` path identity. Publication runs after commit. A
definitive rollback restores original bytes; an uncertain commit preserves the
promoted file and any backup. Compensation verifies file identity before
deleting it. Publication failure preserves the committed row/file and exposes a
snapshot DTO for replay.

## Validation

`responder-build.txt` records:

```text
gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain
BUILD SUCCESSFUL in 1m 39s
22 suites; 191 tests; 0 failures; 0 errors; 0 skipped
```

All Image integration opt-ins were enabled. PostgreSQL 18 used disposable
container `diaries-0024-phase5-db`, with a tmpfs database, and dedicated
`image_repository_test` / `image_wiring_test` databases. The latter was restored
from the frozen development backup and given the additive Image schema.
Mosquitto 2.0.22 used disposable container `diaries-0024-phase5-mqtt` and the
repository ACL. Both exposed random loopback ports and have been stopped.
No live application database, broker or NAS files were modified.

New coverage comprises 28 focused tests and one real PostgreSQL adapter test:

* 4 portable-path tests, including Windows junction/symlink escape rejection;
* 14 inspection cases covering static/animated images, corruption and limits;
* 10 service tests covering staging rejection, generic content, ownership,
  overwrite conflict, rollback/restoration, uncertain commit, publication
  failure, replacement-file protection and concurrent uploads;
* a PostgreSQL service test checking that the row is visible from a separate
  EntityManager during publication, Unicode case lookup, literal `%`/`_`
  handling and database uniqueness rollback.

The existing database and real-broker replay tests also passed. The wiring suite
checks full chronology table digests before/after. Final fixture counts were
10 Diary, 683 Page, 2329 Fragment, 2269 Marquee and 0 Image after test cleanup.

`packaged-windows.txt` and `packaged-linux.txt` record additional checks using
only the built fat JAR: all seven image fixtures decode, portable path rules
hold, and hard-link promotion/file locking/overwrite rollback work. The Linux
probe also tests symlink escape rejection. Linux ran in the cached
`rsmaxwell/diaries-responder:0.0.9-build-76` Java runtime with networking disabled,
read-only source and a temporary filesystem. It loaded the newly built local
JAR, not the image's bundled application. The probe was compiled on Windows
because that Linux runtime contains no compiler module.

Existing Gradle deprecation and Shadow service-file duplication warnings remain.
Packaged WebP decoder discovery was explicitly verified on both operating systems.
Parent and responder `git diff --check` passed. Client tests/builds were not run
because this phase adds responder services without changing a client contract.

## Activation requirements

Before Phases 6/7 activate the services, exclude `.image-staging` from listing,
generic deletion and all HTTP/static serving routes. Windows staging inherits
the server directory ACL; POSIX staging uses owner-only permissions. The Files
root and staging must have only trusted server writers. These guards are not a
defence against arbitrary external processes changing directories mid-operation.

Deployment must verify hard-link, atomic-move and locking support on the actual
Files mount. Unsupported operations fail closed. The tests used temporary NTFS
and Linux filesystems; NAS semantics were not tested. Crash recovery and
pre-existing uploads remain reconciliation work in the later phases.

## Frozen files

`reports/` holds all 22 JUnit reports under short filenames. `source/` contains
the Phase 5 source/test/build snapshots; `source-map.json` maps them to their
authoritative workspace files. `fixtures/` contains the seven synthetic image
files. `summary.json` records the suite totals. `SHA256SUMS.txt` records each
evidence filename and SHA-256, excluding itself. `.gitattributes` disables text
conversion for this evidence package. Existing Phase 4 hashes are unchanged.
