# Image catalogue validation

`test-image-catalogue.ps1` runs 0024 Phase 9 automated tests and builds using
disposable PostgreSQL and MQTT fixtures. Its two required parameters are
`-BackupFile` and a new `-EvidenceDirectory`.

`smoke-image-catalogue.cjs` runs Phase 10 through the actual packaged responder,
packaged web reader, production Angular bundle, MQTT broker and PostgreSQL.
It uses headless Chrome for sign-in, file upload/list/preview and MARQUEE viewing.

## Phase 10 prerequisites and invocation

Run from the `diaries` directory. Docker, Java/Gradle, Node, installed client
dependencies, Python with Pillow, Chrome and the Node `playwright` package are
required. `NODE_PATH` may point at an existing Playwright installation.
`SMOKE_PYTHON` selects Python; `CHROME_BIN` selects Chrome.

Build the current artifacts first:

```powershell
.\gradlew.bat :diaries-responder:shadowJar :diaries-web:shadowJar
npm.cmd --prefix .\diaries-client run build -- --configuration production

node .\scripts\windows\validation\smoke-image-catalogue.cjs `
  .\data\database-backups\development-infrastructure\diaries-development-20260912-203528.dump `
  .\diaries-responder\build\phase8-proof\files `
  .\diaries-responder\build\phase10-new-run
```

The second argument is an existing local Files-tree copy, not a live writable
NAS mount. The third argument must be new. The selected backup must have the
pre-0024 schema and existing MARQUEE data; the runner adds the Image table only
inside its newly created fixture database. It replaces one login only in that
fixture to support browser authentication.

`SMOKE_JAVA_IMAGE` selects an available Java 25 runtime image (default:
`diaries-responder:local`). The application JARs in that image are not used:
the runner mounts the freshly built responder and web JARs and records their
hashes. PostgreSQL uses `postgres:18-alpine`; MQTT uses
`eclipse-mosquitto:2.0.22` with the application ACL. The Angular production
files are served by a temporary local HTTP server with fixture runtime URLs.

All containers and their network have a unique `diaries-0024-phase10-` prefix.
The database uses tmpfs. Files are copied into the responder container's own
writable filesystem, where the fixture staging directory has mode 700.
The runner reserves a stable responder HTTP port for restart tests. Published
fixture ports and the temporary client server bind to loopback.

No named Docker data volume is created. Success and failure both close the
browser/connections and remove only the containers/network created by the run.
The local output remains for inspection; its `evidence/summary.json` records
cleanup failures and its evidence directory is hashed. Logs retain selected
operational lines rather than authentication replies or uploaded bytes.

## Scope

The runner preserves the source Files copy and diary/page/fragment/marquee rows.
It creates supported uploads, generic/corrupt files, an uncatalogued image,
identical bytes at different paths, a genuine Linux case collision, and a
catalogue row with deliberately missing bytes. Reconciliation runs after all
test editing clients are quiesced and uses the production file/catalogue locks.
Two responder restarts must reproduce database and retained state.

The selected page receives a synthetic image matching its stored dimensions;
the original page/fragment/marquee metadata is retained. This checks the actual
MARQUEE UI controls without requiring a write to or complete copy of the NAS
source-page archive. It does not perform Fragment editing or create ImageFragments.

Windows-backed Docker bind mounts exposed the staging directory as mode 777
during validation and were correctly rejected. Native-container storage passed.
Phase 11 must verify the actual deployment filesystem's owner-only staging,
file locks, hard links and atomic moves before enabling production uploads.

Frozen results and the requirement-to-evidence mapping are in the
[Phase 10 evidence](../../../change-control/complete/0024-FEAT%20-%20introduce%20reusable%20persistent%20Image%20catalogue/evidence/phase-10-smoke/README.md).

## 0026 Step 13 controlled ImageFragment reader verification

`verify-0026-step13.ps1` runs the controlled cross-component development verification for
0026 without using the live development database or writable NAS content.

It requires a PostgreSQL backup of the development dataset and a **new** evidence directory:

```powershell
.\scripts\windows\validation\verify-0026-step13.ps1 `
  -BackupFile .\data\database-backups\development-infrastructure\diaries-development-YYYYMMDD-HHMMSS.dump `
  -EvidenceDirectory .\diaries-web\build\step13-YYYYMMDD-HHMMSS
```

The wrapper builds the current responder/web fat JARs, then
`smoke-imagefragment-reader.cjs` creates a uniquely named Docker network and disposable
PostgreSQL, Mosquitto, responder and web containers. PostgreSQL uses tmpfs and the
responder's `/data/files` tree exists only inside the disposable responder container.
No NAS mount or normal development database is used.

The restored database must already contain the 0022 Page/type Fragment schema. The runner
adds the 0024 Image schema only when absent and applies the 0025 ImageFragment migration
only when `fragment.image_id` is absent; otherwise it runs the committed 0025 schema
assertion. All schema work is therefore confined to the restored fixture database.

The fixture then:

- proves MARQUEE authoring/rendering while `imageFragmentWritesEnabled=false` and confirms
  `addImageFragment` is rejected with 403;
- enables ImageFragment authoring only in the fixture responder and restarts it;
- uploads owned nested-path Images through `uploadFile` and creates IMAGE Fragments through
  `addImageFragment`, including no-selection and a two-Fragments/one-Image case on strictly
  different Pages/dates; the browser proves both references resolve the same catalogue URL;
- uses a loopback reverse proxy so the browser sees `/reader` and `/diaries-responder`
  production-style prefixes rather than container addresses;
- captures desktop/mobile month/source-page screenshots and exercises keyboard selection,
  deep links and Back/Forward;
- injects a retained-metadata loss only for an owned fixture Image and physically hides only
  an owned fixture file; a fresh browser context makes the `FILE_LOAD_FAILED` check independent
  of any earlier browser cache;
- verifies reference-aware `deleteImage` conflict, removes fixture references through
  `deleteFragment`, then deletes the Image through `deleteImage` and checks file/retained
  tombstones;
- restarts responder/web and verifies authoritative metadata restoration and deterministic
  surviving chronology;
- records fixture IDs, retained payloads/hashes, database rows, HTTP/network samples,
  screenshots, selected logs, artifact hashes and cleanup status.

`CHROME_BIN`, `STEP13_PYTHON` and `STEP13_JAVA_IMAGE` may override the browser, Python
command and Java 25 fixture image respectively. The default Java image is
`diaries-responder:local`; its packaged application is not used because the freshly built
candidate JARs are mounted and hashed.

A successful run must finish with `summary.json` status `PASSED` and an empty
`cleanupFailures` array. Failed attempts are intentionally left in the requested evidence
directory for diagnosis, but owned Docker containers/network are still removed in `finally`.

### Step 13 retained-snapshot reliability

Before building, the wrapper runs `step13-retained-snapshot.test.cjs` to exercise
large retained replay, QoS-1 ACL rejection, stalled SUBACK and missing-marker diagnostics without Docker.
The runner uses `step13-retained-snapshot.cjs` to snapshot the Image and Fragment
retained topics only, with a separate authenticated publisher for its non-retained,
QoS-1 `diaries-sync/step13/...` drain marker. These are the canonical topics
used by Step 13's reference, tombstone and restart assertions.

Each snapshot now writes `<label>-mqtt-diagnostics.json` on success **and** failure.
It records actual granted SUBACKs, message counts, marker delivery and disconnect/error
information without storing broker credentials. In the event of another snapshot
timeout, preserve the matching diagnostics JSON plus `mqtt.log`, `summary.json` and
`cleanup.json` from that run's evidence directory. Do not replace a timeout
with an arbitrary sleep or treat a missing barrier as a passing snapshot.

### Step 13 catalogue Image HTTP and browser-load diagnostics

Before testing browser ImageFragment rendering, the runner now checks each owned
fixture upload against its original SHA-256 on three paths: its file inside the
disposable responder container, the direct responder `/files/...` HTTP route,
and the browser-visible `/diaries-responder/files/...` proxy route. It preserves
`catalogue-image-http-preflight.json` even if one route fails. This catches
missing files and incorrectly encoded nested or Unicode paths before they can
be confused with a lazy browser image.

The reader template marks catalogue images `loading="lazy"`. Step 13 scrolls
each selected fixture image into view before requiring non-zero `naturalWidth`,
without modifying the production JavaScript or changing the `loading` attribute.
If browser decoding/loading still fails, inspect the generated
`selected-image-browser-image-diagnostics.json` (or the corresponding shared
reference label), which records the actual `src`, request status/failures,
file-fallback state and console errors. The image preflight has four small
non-Docker regression tests run by the PowerShell wrapper before building.

### Step 13 HTTP endpoints after disposable container restarts

The runner publishes responder/web container ports with Docker's ephemeral
`-p 127.0.0.1::CONTAINER_PORT` form. The host-side port must not be assumed
stable across `docker restart`, particularly on Docker Desktop for Windows.
After enabling ImageFragment authoring, and again after the final component
restarts, Step 13 rediscovers each published port through `docker port`.
The public prefix proxy reads the **current** port for every request. Responder
readiness now requires an actual synthetic Page response with its original
SHA-256; an MQTT subscription on its own is insufficient. Web readiness
requires an HTTP 2xx response from the current `/reader/health/ready` route.

`gate-enabled-responder-port.json`, `final-restart-responder-port.json`, and
`final-restart-web-port.json` record previous/current published ports, HTTP
probes, retry errors and whether the endpoint became ready. These diagnostics
are written even when readiness times out. Selected responder logs now include
static-server startup, exceptions and errors. If the published port is unchanged
but HTTP never becomes ready, inspect those diagnostics and responder logs
rather than assuming a proxy/fixture-path defect.

The PowerShell wrapper also runs the non-Docker
`step13-proxy-routing.test.cjs` regression suite before the clean build.

## 0026 Step 14 full regression and artifact verification

`verify-0026-step14.ps1` runs the Java 25 full web suite/build, requires non-skipped selected
real-MQTT/Testcontainers suites, seals the exact-source SHA inventory and final web JAR
identity, and sanitizes both local Compose renderings. `-FullResponder` and `-Client`
run the additional full suites; `-BackupFile` reruns the disposable Step 13 real-browser
checks; `-InspectPublishedImages` opportunistically records exact IDs/digests for referenced published images that are already local; missing images are recorded as unavailable and are verified at the Step 15/16 deployment gate rather than blocking Step 14.
Evidence must be written outside subproject generated-output directories; in particular do not use `diaries-web/build`, because the Step 14 full web gate begins with `:diaries-web:clean`. Use the top-level `build/step14-*` location documented in the Step 14 feature README.
It never starts a Compose stack or accesses a live NAS/database. See
`change-control/in-progress/0026-FEAT - render ImageFragments in diaries-web/evidence/Step 14/README.md`
for full commands, prerequisites, evidence and acceptance rules.
