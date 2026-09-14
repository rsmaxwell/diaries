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
[Phase 10 evidence](../../../change-control/in-progress/0024-FEAT%20-%20introduce%20reusable%20persistent%20Image%20catalogue/evidence/phase-10-smoke/README.md).
