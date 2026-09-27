# Step 15.2 / 15.3 controlled deployment runner

This runner deploys the current **0025 responder candidate** as a real Java process, but connects it only to disposable PostgreSQL/Mosquitto containers and a private temporary filesystem tree. It does not use the live development database, production, or the NAS.

Before it starts, it verifies that the application source still matches the Step 14 SHA-256 inventory. It then rebuilds the responder fat JAR, restores the frozen 0024 database into disposable PostgreSQL, applies/validates the 0024 + 0025 schema, and runs two deployment phases:

- **15.2 / disabled:** sign-in; existing Page/Fragment retained reads; `addImageFragment` gate rejection; create/edit/delete MARQUEE; upload/catalogue; generic `DeleteFile` conflict; unreferenced `DeleteImage`.
- **15.3 / enabled:** create IMAGE + Image reference; edit/date move; clear/reattach `imageId`; retained Fragment/Image checks; referenced `DeleteImage` and `DeleteFile` conflict; deliberate retained corruption; responder restart/replay; Fragment deletion; final successful Image deletion and retained tombstones.

The runner verifies the disposable application tables return to their pre-fixture hashes and deletes its private file tree and Docker containers. It records `productionModified=false`, `liveDatabaseUsed=false`, and `nasUsed=false` in `result.json`.

## Readiness and diagnostics

Each responder start is now checked using the responder's own Java MQTT RPC health-check client before the Node smoke phase begins. This uses the same MQTT v5 response-topic/correlation-data contract as the production health check and records attempts in `<phase>-health.log`.

The Node smoke client no longer performs its own repeated readiness loop. It uses a unique reply topic, omits empty MQTT user-properties (matching the Angular client), records publish acknowledgements and replies in `<phase>-console.log`, and force-closes its MQTT client on exit. Each Node phase has a hard 180-second process timeout, so a client shutdown problem cannot leave the validation hanging indefinitely.

The runner prints stage progress directly to the PowerShell window. It also captures the disposable broker log in `mosquitto.log` before cleanup.

## Running

The responder still has a fixed HTTP port of **8081**, so stop any currently running local responder before running this harness. The harness does not stop it automatically.

From `evidence/Step 15` use Windows PowerShell 5.1 or later:

```powershell
.\run-step15.ps1 -ApplyDocumentation
```

If `deployment/final-run` already exists from a failed or interrupted attempt, `run-step15.ps1` now archives it automatically as `deployment/failed-run-YYYYMMDD-HHMMSS` before starting a fresh run. A previously PASSED `final-run` is never overwritten.

The default evidence destination is `deployment/final-run`. A successful run is authoritative only when `deployment/final-run/result.json` says `PASSED` and all container cleanup codes are zero.
