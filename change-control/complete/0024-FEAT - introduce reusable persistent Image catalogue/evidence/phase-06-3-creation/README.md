# 0024 Phase 6.3 — catalogue creation and response

Implemented and validated 2026-09-13. UploadFile now invokes full catalogue
completion. Existing Phase 6.1/6.2 working changes and frozen evidence were
preserved. Phase 7 generic deletion protection and Phase 11 deployment checks
remain outstanding; no live deployment was changed.

## Changed files

| File | Change |
| --- | --- |
| responder handlers/UploadFile.java | Full completion, acknowledged retained publication, explicit committed/rollback/recovery errors and additive response |
| responder dto/UploadFileResponse.java | Seven-field response retaining the legacy fields and explicitly serializing null image fields |
| responder handlers/UploadStagingTest.java (tests) | Actual image registration/publication expectations, retry/conflict, rollback/overwrite compensation, generic nulls and publication failure |
| responder ImageWiringIntegrationTest.java (tests) | Real authenticated handler, PostgreSQL commit visibility, retained MQTT delivery and replay after a disconnected publisher |
| client src/app/mqtt/file-rpc-compatibility.spec.ts | Full Image metadata and explicit generic-null compatibility through the existing client decoder |
| responder README and parent 0024 README/checklist | Current behaviour, completed 6.3 criteria and remaining deployment/deletion work |

The Phase 5 service supplies atomic no-replace promotion, backup handling,
transaction boundaries and compensation. The handler now selects its full
completion mode. Supported JPEG/PNG/GIF/WebP bytes, including octet-stream
images, commit one Image row before publication to `diaries/images/{id}`.
Publication uses QoS 1 and retain, waits up to ten seconds for acknowledgement,
and rejects failure reason codes. The existing startup replay remains the
recovery route for retained state.

`UploadFileResponse` retains `name`, `subdir`, `size`, `path`, `url` and adds
`imageId` plus the ten-field `ImagePublishDTO`. A generic non-image octet-stream
upload creates no row/topic and returns both new fields as explicit nulls.
The absolute path stays only in the compatibility response; neither the row
nor retained Image contains a path resolved against deployment storage or URL.

A definitive repository failure removes a new file or restores the previous
uncatalogued file. Publication failure preserves committed bytes and metadata,
returns an internal error identifying the committed Image and replay need, and
leaves retries subject to the existing conflict guard. An uncertain commit or
failed compensation preserves recovery files and reports administrator recovery;
only that recovery diagnostic logs target/backup paths. No uploaded bytes or
tokens are logged. Ordinary uploads retain the Phase 6.1 logging restrictions.

## Validation

`responder-build.txt` records the full responder test/build:

```text
gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain
BUILD SUCCESSFUL in 2m 5s
24 suites; 207 tests; zero failures, errors or skips
```

All Image database/MQTT opt-ins were enabled. `reports/` freezes this full run.
Afterwards, the existing rejection test was extended to explicitly declare PNG
for truncated PNG bytes as well as testing octet-stream truncation. The handler
suite passed again; `handler-tests.txt` and `handler-tests.xml` record that
focused verification. No implementation changed after the full build.

Coverage includes:

* supported image and octet-stream image registration, byte-derived metadata,
  one retained entity, and preservation of the five compatibility fields;
* explicit null response fields and no Image creation for generic bytes;
* corrupt content/MIME/checksum/path rejection without changing existing bytes;
* retry and overwrite conflicts, including concurrent same-path uploads;
* repository failure cleanup and restoration of uncatalogued overwrite bytes;
* callback observation of committed rows before publication;
* publication failure preserving file/row and rejecting a retry;
* actual PostgreSQL and MQTT publication/recovery: a separate EntityManager
  sees the committed row before the production publisher runs; a late broker
  subscriber receives its exact JSON with QoS 1 and retain. Disconnecting the
  publisher causes a committed-state error for a second upload. The actual
  `DiaryContext.loadFromDatabase()` projection supplies its payload for replay,
  and a subsequent late subscriber receives the repaired retained entity.

The integration test uses the production handler and publication callback;
it does not route the request through the MQTT RPC dispatcher. Client tests
separately exercise the existing RPC reply decoder and compatibility contract.
`client-tests.txt` records **10 passing** ChromeHeadless compatibility tests;
`client-build.txt` records a successful Angular production build. No client
runtime source or chooser UI changed.

Database/broker tests used disposable containers `diaries-0024-phase63-db` and
`diaries-0024-phase63-mqtt` (PostgreSQL 18 / Mosquitto 2.0.22). Database storage
was tmpfs; the wiring database was restored from the frozen development backup
and given the additive Image schema. The broker used the repository ACL and
random loopback ports. Both fixtures were stopped. Final wiring counts after
cleanup: 10 Diary, 683 Page, 2329 Fragment, 2269 Marquee, zero Image. The suite
also checks full chronology table digests unchanged.

Existing Gradle/Shadow warnings remain. The actual deployment mount and
external static-server ACLs were not exercised; prior deployment requirements
still apply. No live database, broker or NAS content was modified. No commit or
push was made.

## Frozen evidence

`source/` contains the five changed code/test files under short filenames.
Logs, JUnit reports and summary record validation. `SHA256SUMS.txt` hashes all
evidence files except itself; `.gitattributes` prevents text conversion.
Phase 6.1 and 6.2 evidence remains unchanged.
