# 0024 Phase 6.2 — upload conflict rules

Implemented and validated 2026-09-13. Phase 6.1 local work and its frozen
evidence were preserved. Image creation, publication and additive response
fields remain Phase 6.3.

## Changed files

| Responder file | Purpose |
| --- | --- |
| handlers/UploadFile.java | Resolve canonical identity, check ownership through the JPA adapter before staging, and use guarded promotion instead of direct moves |
| utilities/ImageCatalogueService.java | Guarded generic promotion shares the full completion lock, ownership check, no-replace promotion, backup and compensation implementation |
| handlers/UploadStagingTest.java (tests) | Guard/alias/missing-file/overwrite/concurrency tests and a fail-closed configuration test; existing staging cases still run |
| ImageWiringIntegrationTest.java (tests) | Exercise the actual authenticated UploadFile handler against PostgreSQL Unicode identity |

The responder README and parent 0024 README/checklist describe the new
behaviour. No client source, schema, ACL or deployment configuration changed.

The handler checks the canonical NFC path against the existing repository's
`lower(relative_path COLLATE pg_catalog.pg_unicode_fast)` identity. This check
precedes filesystem case-alias rejection, so owned aliases return conflict
status 409 even if the backing file is missing. Both overwrite modes are
rejected, including generic octet-stream attempts against a catalogued path.
No configured catalogue, or a failed lookup, can permit promotion.

Ownership is checked again inside the service's process critical section and
shared filesystem lock. An ordinary existing file still conflicts when
overwrite=false. Only uncatalogued files may be replaced. Hard-link promotion
creates the target atomically without replacement, and an overwritten file is
first moved to a private backup. Guarded generic and full catalogue completion
use the same backup/compensation implementation. Definitive later insertion
failure restores the original file; uncertain commit/compensation outcomes
preserve recovery files rather than deleting potentially committed bytes.

For this phase, guarded generic promotion performs no insertion or publication.
The response retains name/subdir/size/path/url. Phase 6.3 will select full
completion and add Image metadata to the response. Other writers/reconciliation
must use the same file integrity protocol; arbitrary external writers and
direct manual database changes are outside the locking guarantee.

## Validation

* Full responder test/build: **203 tests, 24 suites, zero failures/errors/skips**;
  `BUILD SUCCESSFUL in 1m 42s`. All PostgreSQL/MQTT opt-ins were enabled.
* Five new focused tests cover exact/Unicode-case/separator ownership aliases,
  missing backing files, both overwrite modes, ownership becoming true before
  locked promotion, uncatalogued overwrite, simultaneous no-overwrite requests
  and missing catalogue configuration. The test catalogue rejects any attempt
  to insert a row from this phase's handler.
* The new PostgreSQL test invokes authenticated UploadFile with a catalogued
  accented filename, decomposed Unicode/case/backslash aliases, and literal
  `%`/`_` characters. Conflicts preserve original bytes and row metadata; a
  distinct non-owned name succeeds. Missing files remain missing on rejection.
* Existing service tests verify rollback restoration, uncertain commit
  preservation, replacement-file identity protection and publication failures.
  Existing real-broker retained replay/tombstone tests also passed. The handler
  has no publication callback in guarded generic mode.
* **8 Angular file-RPC compatibility tests passed** in ChromeHeadless.
* Angular production build passed. No client source was changed.

Tests used disposable PostgreSQL 18 and Mosquitto 2.0.22 containers named
`diaries-0024-phase62-db` and `diaries-0024-phase62-mqtt`, exposing random loopback
ports. The wiring database was restored from the frozen development backup
into tmpfs and given the additive Image schema. The broker used the current
repository ACL. Both fixtures were stopped after validation. Final wiring
counts: 10 Diary, 683 Page, 2329 Fragment, 2269 Marquee, zero Image after cleanup.
The wiring suite also verifies complete chronology table digests unchanged.

No live database, broker or NAS content was changed. Existing deployment
permission/filesystem checks remain necessary; Phase 6.2 did not run a NAS
probe. Gradle deprecation/Shadow warnings remain. No commit or push was made.

`reports/` contains all JUnit XML reports under short names; logs and summary
record the commands/results. `source/` freezes the four implementation/test
files listed above. SHA256SUMS records every evidence file except itself;
`.gitattributes` disables text conversion. Phase 6.1 evidence hashes remain
unchanged.
