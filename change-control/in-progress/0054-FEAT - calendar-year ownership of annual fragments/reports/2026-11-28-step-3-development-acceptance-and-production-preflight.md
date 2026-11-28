# 0054 — Step 3 development acceptance and production preflight (2026-11-28)

## Accepted development evidence

- Windows Angular ChromeHeadless: 289/289 successful; Angular build PASS (`note(20261128-114111).txt`).
- Windows Gradle responder+Reader tests and builds: BUILD SUCCESSFUL, 29 tasks (23 executed, 6 up-to-date), `note(20261128-114854).txt`. Shadow JAR service-file and Gradle 10 deprecation warnings recorded; they did not cause failure.
- Docker development infrastructure: PostgreSQL 18 and Mosquitto 2 both healthy (`note(20261128-115207).txt`).
- Read-only PostgreSQL: nine PREAMBLE fragments (IDs 1,2,3,387,806,1177,1563,1564,1926), year-owned, diary/page/month/day NULL, fragments 2355/2356 absent (`note(20261128-115338).txt`).
- Retained MQTT: nine canonical `diaries/years/{year}/preamble/{id}` records with matching ownership and sequence (`note(20261128-115532).txt`). Deleted IDs absent under fragment and year topic scan (`note(20261128-115645).txt`). MQTT subscription timeout is expected.
- Browser: user confirmed Reader shows PREAMBLE order then DATED content for 1828, 1832, 1834; deleted IDs did not reappear. Earlier accepted Editor, Quill Save recovery, drag reordering and deletion checks remain valid.

**Acceptance:** development integration checks PASS. The Step 3 production release gate remains OPEN. No production migration/deployment or rollback test is claimed.

## Existing implementation tool

`tools/0054-migrate-annual-fragments.sql` is the feature-local transaction that validates ownership, converts POSTAMBLE to EPILOGUE, clears annual diary/month/day and adds placement/ownership constraints. `tools/0054-audit-annual-fragments.sql` captures the inventory. Review their **actual current working-tree versions** before production execution; the last supplied complete source bundle is 2026-11-27 and is older than current local changes.

## Production preflight — read-only, no deployment

1. On Windows Cygwin, record parent branch/HEAD/status, `.gitmodules`, `git submodule status`, independent client/responder/web branches/HEAD/status, and preserve all local changes. Compare with deployed production image tags and matching source revisions. Do not assume parent/submodules or Windows/mango are synchronised.
2. On `pluto`, inventory actual production containers/images and service state. Inspect production PostgreSQL's current `fragment` schema/constraints and annual IDs, owner fields, placement and counts using a READ ONLY transaction. Verify which database/container and credentials are actually production before connecting. Do not assume the development container name applies.
3. Capture retained production annual topic names and payload ownership, including legacy topic families and `diaries/fragments/{id}`; check any stale 2355/2356 records (development deletion does not prove production deletion). Use established production MQTT credentials, without printing secrets to the evidence log.
4. Establish a **fresh, matching** pre-cutover PostgreSQL/files recovery point and a verified accessible restore/rollback path before changing production. Confirm the backup job completion, manifests, expected dataset identity and recovery point at mars/backup; no snapshot deletion or restore during read-only preflight.
5. Record original annual rows including diary_id provenance, exact IDs, versions, sequence, text/image/locks and counts/checksum. Confirm zero anomalies using audit tool. Preserve pre-migration row-level manifest under this feature evidence, not Playbooks.
6. Define and approve a coordinated release window and exact image tags/commit IDs for client, responder and Reader. Avoid exposing incompatible old/new protocol consumers during migration; preserve previous image tags, previous application configuration and documented rollback order. Responder startup sync rebuilds canonical retained topics and tombstones obsolete ones, to be verified after cutover.
7. Only with explicit approval: run migration with transaction error-stop; deploy coordinated compatible builds; verify database, MQTT replay/tombstones, Editor/Reader and legacy URL behavior; capture rollback receipts. Do not run write SQL or deploy as a consequence of this preflight report.

## Notes / deferred tests

- Paho MQTT v5 temporary synchronisation subscriber shutdown NullPointerException observed during development responder start; startup and subsequent functionality succeeded. Record as a separate issue if reproducible, not resolved by passing builds.
- Full legacy-retained replay and second-restart convergence, empty-Diary and two-Diary-year workflows, EPILOGUE creation, and production-specific recovery evidence are not proved by the three-year Reader check; do not claim them complete.
- Client Angular build generated `public/assets/build-info.json`; record working-tree changes when collecting exact revisions.

## Release hold point

**NO-GO until** exact production topology/schema/retained inventory, pre-cutover backup recovery evidence, production image/source revisions, anomaly-free migration audit and an approved component deployment/rollback sequence are recorded. Once collected, request explicit production execution approval. 0053 remains blocked on completed 0054.
