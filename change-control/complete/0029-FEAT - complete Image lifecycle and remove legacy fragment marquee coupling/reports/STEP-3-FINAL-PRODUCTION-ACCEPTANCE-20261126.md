# 0029-FEAT — Production acceptance and evidence consolidation (2026-11-26)

**Status:** Production cutover **ACCEPTED for application functionality and PostgreSQL structural integrity**. Feature **IN PROGRESS**; independent retained-MQTT reconciliation and formal feature closure are **not yet accepted**. Do not move to `change-control/complete` yet.

## Release and source identities

| Component | Source / release |
| --- | --- |
| Diaries parent | `216413468fbaae21dbfbfe36e92c05cd87cba907` |
| Client | `cc826a8254b0e6d989755dc880d3023dae9e3416` / `0.0.9-build-81` |
| Responder | `a49c6abd0ce005d58eb516770f6515313e40cdf6` / `0.0.9-build-87` |
| Reader | `363ca8f425b811eeedff47486092b1f63c403ab0` / `0.0.9-build-10` |
| Playbooks | `e1273b48b1cea2e175ea098a0a82ff8b0b184851` |
| Ansible controller | `29c562f` (points at above Playbooks commit) |

## Production cutover 26 November 2026

- First attempt at 17:20 stopped application writers, then failed before migration because `pg_dump` used a nonexistent role `diaries`. No migration was run in that attempt. Evidence: `evidence/step-3-production-cutover/production-cutover-20261126-172041.log`.
- Corrected attempt started at 17:23. Application writers stopped. Fresh pre-migration PostgreSQL dump created and checksum/catalogue verified. Location: `evidence/step-3-production-cutover/diaries-production-pre0029-20261126-172307.dump` and associated `.toc`/checksum. **Retain backup locally; do not commit dump bytes to Git.** Evidence: `production-cutover-20261126-172307.log`.
- `step2-hybrid-schema-and-data.sql` committed successfully. `step3-retire-marquee-page-id.sql` committed successfully. Postmigration database integrity passed.
- First Ansible service restart failed because synced Mosquitto ACL was mode 0600, unreadable to Mosquitto UID 1883. The source file mode on mango was corrected to 0644 and the Diaries Playbook was rerun; production recovered. Source permissions are authoritative for synchronised files; no additional Ansible per-file permission task requested.
- Production `diaries-compose.service` subsequently active and all five containers healthy. Owner explicitly confirmed **all six production browser acceptance checks passed** (editor, annual PREAMBLE, dated TEXT/IMAGE, Hermitage and Whitley Park images, Reader, and editing/navigation as exercised).

## Repeated post-cutover integrity inspection

Two read-only inspections of production completed at **18:43:23** and **18:43:59 UTC**, with mutually consistent PASS output:

- `evidence/step-3-production-cutover/postcutover-integrity-20261126-184323.log`
- `evidence/step-3-production-cutover/postcutover-integrity-20261126-184359.log`

Verified state:

| Assertion | Evidence |
| --- | --- |
| Systemd | `diaries-compose.service` active |
| Five Docker containers | running, healthy |
| Docker application tags | Client `0.0.9-build-81`; Responder `0.0.9-build-87`; Reader `0.0.9-build-10` |
| Annual ACL | `diaries/years/#` read for Client and Reader, readwrite for Responder |
| DATED IMAGE | 73 |
| DATED TEXT | 2249 |
| PREAMBLE TEXT | 9 |
| Total Fragments | 2331 |
| PREAMBLE records | IDs 1,2,3,387,806,1177,1563,1564,1926 with explicit Diary/year and no Page |
| Historical DATED records | 1738 -> Page 1005; 2061 -> Page 1078 |
| Marquee/Fragment ownership and schema constraints | SQL `NOTICE: PASS: 0029 production post-cutover SQL ownership and schema integrity` |
| Recent responder/reader/broker error grep | no matching messages in inspection window |

These checks establish structure and observed service health. They do **not** prove that every retained MQTT topic agrees with PostgreSQL, nor prove there have never been application errors outside the inspected window.

## Recovery and functional acceptance

- Previously accepted isolated PostgreSQL restore, migration and rollback rehearsal need not be repeated.
- Production Files snapshot `20261126-150001Z` for backup `20261126-003058Z`: **128 source and 128 restored files, 98 MB**, full `diff -qr` PASS on mars, with a temporary copy. This verifies restored contents against backup; it is not a different-host disaster-recovery exercise.
- Six local-published-image browser checks PASS and six production browser checks owner-confirmed PASS.

## Acceptance gate disposition

| Gate | Disposition |
| --- | --- |
| Production application cutover / releases | PASS |
| Hybrid migration and `marquee.page_id` retirement | PASS |
| Read-only post-cutover PostgreSQL integrity | PASS |
| Restore/rehearsal evidence | PASS |
| Production Editor and Reader browser acceptance | PASS (owner confirmed) |
| Annual MQTT topic ACL | PASS |
| Independent retained-MQTT vs database topic inventory/replay comparison | **OPEN** — not demonstrated by these runs |
| Commit of final change-control evidence | **OPEN** until user applies and commits report/logs |
| Formal feature closure / directory move | **OPEN** — requires explicit approval |

### Evidence retention and next action

Keep complete raw outputs in this feature's `evidence/` directory. The two post-cutover logs were created by the Windows tool; do not rerun it solely to generate duplicates. Ensure the 18:43 logs and 17:23 cutover receipt are retained in the checkout. Archive the acceptance report and reference it in a subsequent Git commit, without adding the raw `.dump` file to Git. Before requesting formal feature closure, decide whether to run the existing read-only retained-MQTT reconciliation or explicitly accept that limitation. Do not silently mark it PASS.
