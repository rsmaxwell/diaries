# 0024 Phase 4 — retained Image catalogue

Completed 2026-09-13 in source. No live application restart or production
deployment was performed.

## Implementation

- `utilities/DiaryContext.java` independently iterates ImageRepository.findAll
  and publishes each DTO into the startup map at `diaries/images/{id}`. Images
  do not require a Diary, Page, Fragment, Marquee, Files root or readable file.
- `sync/Synchronise.java` waits for the existing retained-replay quiet period
  before computing differences. Previously a fast/empty database replay could
  race incoming retained messages and miss stale topics. The synchroniser now
  dispatches changed topics and tombstones in sorted topic order, explicitly
  uses QoS 1 and retain, and encodes JSON as UTF-8. Unchanged topics are skipped.
  This preserves the existing one-second quiet-period heuristic; it is not a
  protocol-level end-of-replay guarantee for an arbitrarily delayed broker.
- `config/mosquitto/aclfile.txt` adds only responder read/write permission on
  `diaries/images/+`. All three local modes mount this file. Client, web and
  health permissions/subscriptions are unchanged. No ListImages RPC is added.
- Existing ImagePublishDTO/Publisher provide metadata and identity-only
  zero-byte tombstones. The metadata is exactly id, version, relativePath,
  mimeType, originalFilename, width, height, checksum, caption and altText.
  No file content, resolved URL or absolute storage path is generated.
- Responder/Mosquitto READMEs and the 0024 checklist record the behaviour and
  ACL deployment prerequisite. Upload, inspection and reconciliation remain
  later phases.

## Validation

`responder-build.txt`: **BUILD SUCCESSFUL in 1m 43s**, 19 suites, **162 tests**,
zero failures/errors/skips. Database and broker opt-ins were all enabled.
Existing Shadow duplicate-service and Gradle deprecation warnings remain.

- `dto.xml`: exact fields/values, Unicode, canonical topic, QoS 1, retain,
  identity-only tombstones, path validation and absence of extra metadata.
- `replay.xml`: independent/unreferenced Images with no chronology or file
  configuration; identical topic/payload maps for different repository orders;
  empty catalogue; existing orphan Fragment/date projection unchanged.
- `database-integration.xml`: actual production Hibernate factory and responder
  context against PostgreSQL 18.6, with Hibernate validate. Two committed,
  unreferenced Images appear in replay and in a fresh EntityManager/context.
  All pre-existing chronology topic payloads are preserved. Full-row digests
  of Diary/Page/Fragment/Marquee are unchanged before/after the suite.
- `mqtt-integration.xml`: actual Synchronise.perform against Mosquitto 2.0.22
  with the repository ACL and a disposable responder password. Existing stale
  Image metadata is updated; removed Image rows and noncanonical aliases get
  tombstoned; late subscribers receive exactly the retained canonical state at
  QoS 1. Repeating startup sends no unchanged messages. Metadata updates and
  deletion preserve the Fragment topic. The DTO tombstone helper also removes
  the broker's retained copy. This test supplies a database-map fixture; the
  separate PostgreSQL test exercises creation of that map from durable rows.

All three Compose configurations passed `config --quiet` using committed mode
environment files. Expected warnings reported missing developer-specific
credentials/NAS configuration because local overrides were not loaded. These
checks validate configuration syntax, not application startup. Client/web code
and subscriptions were inspected; frontend builds were not needed or run.

## Fixtures and repeatability

`fixture.txt` records exact Docker image IDs and final database counts.
The new `diaries-0024-phase4-db` container used PostgreSQL tmpfs storage and a
random loopback port (62619 in this run). A new image_wiring_test database was
restored from the previously verified `diaries-development-20260912-203528.dump`
(SHA-256 `fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86`),
then the Phase 2 schema was applied. A separate image_repository_test database
received only that Image schema. Final counts: 10 Diaries, 683 Pages, 2,329
Fragments, 2,269 Marquees and zero fixture Images after test cleanup.

The new `diaries-0024-phase4-mqtt` container used port 58220 on loopback,
`mosquitto.conf` from this directory, and the repository ACL mounted read-only
at `/mosquitto/config/aclfile.txt`. Its entrypoint created `/tmp/phase4-passwords`
using `mosquitto_passwd -b -c /tmp/phase4-passwords diaries-responder phase4-fixture`,
made that temporary password file readable to Mosquitto, then ran
`mosquitto -c /mosquitto/config/mosquitto.conf`. This known password is strictly
for the disposable fixture; no application credentials were read or recorded.
Persistence and anonymous access were disabled. Both containers used `--rm`
and were stopped after evidence capture.

To repeat, create fresh isolated fixtures as above (database restore details
also appear in the Phase 3.3 evidence), substitute their loopback ports, and run
from the parent Diaries repository:

```powershell
$env:DIARIES_IMAGE_REPOSITORY_TEST_URL = 'jdbc:postgresql://127.0.0.1:PORT/image_repository_test'
$env:DIARIES_IMAGE_WIRING_TEST_URL = 'jdbc:postgresql://127.0.0.1:PORT/image_wiring_test'
$env:DIARIES_IMAGE_MQTT_TEST_URL = 'tcp://127.0.0.1:MQTT_PORT'
.\gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain
if ($LASTEXITCODE -ne 0) { throw 'Validation failed' }
```

Never point the MQTT test at an application broker: startup reconciliation
owns `diaries/#` and intentionally removes stale fixture topics. Database tests
require the dedicated database names. Stop only the disposable containers and
unset these opt-ins afterward; without opt-ins integration tests are skipped.

## Rollout and evidence integrity

Before starting the updated responder, apply/verify the Phase 2 Image schema
and reload the selected local broker's ACL (or restart that mode's broker).
The running broker may still have its earlier ACL loaded. Production needs the
equivalent responder-only Image permission during Phase 11; no separate
playbooks repository was modified. Development/production databases, live
retained topics and NAS files were not modified by validation.

`source/` contains flat snapshots of the changed Java classes/tests and ACL;
responder-README.md and mosquitto-README.md snapshot their respective READMEs.
SHA256SUMS.txt freezes this package's filenames and bytes. Earlier Phase 1–3
evidence was not rewritten. No commit or push was performed.
