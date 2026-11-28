# 0054-FEAT — Step 1: verified baseline and frozen contract

**Status: CLOSED — 27 November 2026.** Static source review, live development and production PostgreSQL inventories, both retained MQTT annual-topic trees, existing production backup publication and mars retained history have been checked. The calendar-year ownership and EPILOGUE naming decisions were accepted in the feature discussion. This closure is a design/baseline gate, **not** evidence that migration code, a rollback or deployment was executed.

## Verified evidence

| Check | Evidence | Result |
|---|---|---|
| Windows parent and submodule revisions, clean statuses | `note(20261127-210141).txt` | PASS — parent `e817acc0eb37`; client `aa6493557771`; responder `a49c6abd0ce0`; Reader `18b18c2c090e` |
| Development PostgreSQL schema | `note(20261127-210242).txt` | PASS — fragment `diary_id NOT NULL`; year/month/day nullable; legacy placement constraints |
| Development annual inventory | `note(20261127-210329).txt`, `note(20261127-211130).txt` | PASS — nine TEXT PREAMBLE; no POSTAMBLE; all annual page IDs null, dates 1 January, no duplicate year/placement/sequence |
| Development MQTT | `Screenshot 2026-11-27 211555.png` | PASS — nine retained annual topics in diary/year/placement/id structure |
| Production PostgreSQL | `note(20261127-211917).txt` | PASS — nine TEXT PREAMBLE, no POSTAMBLE/EPILOGUE; same year/Diary counts, no duplicate annual sequence; 2,322 DATED fragments |
| Production MQTT | `Screenshot 2026-11-27 212627.png` | PASS — nine retained annual topics matching production SQL inventory |
| Production publication | `note(20261127-212054).txt` | PASS — schema-2 backup ID `20261127-003111Z`, 128 durable files, manifest verification succeeded |
| mars retained history | `note(20261127-212259).txt` | PASS — backup ID `20261127-003111Z` shown verified, 20 retained snapshots as of observation |

The production application baseline at inspection: client `0.0.9-build-82`, responder `0.0.9-build-87`, Reader `0.0.9-build-11`, PostgreSQL 18-alpine and Mosquitto 2. Git revisions and deployed images must be checked again at cutover.

The nine annual IDs are `1, 2, 3, 387, 806, 1177, 1563, 1564, 1926`. Calendar-year counts: 1828/Diary 1 = 3; 1829/Diary 1 = 1; 1830/Diary 1 = 1; 1831/Diary 3 = 1; 1832/Diary 4 = 2; 1834/Diary 5 = 1. SQL inventories do not establish byte-for-byte equality between development and production dated records.

## Agreed Step 2 contract

1. Three canonical placements: `PREAMBLE`, `DATED`, `EPILOGUE`. Legacy `POSTAMBLE` is a migration input only, not a final enum, DTO, RPC value, schema check, MQTT path or editor/Reader label.
2. Annual fragments are owned by calendar year and placement, independently of a physical Diary or Page: annual `year NOT NULL`, `diary_id=NULL`, `page_id=NULL`, `month=NULL`, `day=NULL`; stable ID, type, text/image, locks, version and sequence retained. Ordering is `sequence`, then `id`. DATED fragments stay Page-owned with valid date and Diary relationships.
3. Annual retained path becomes `diaries/years/{year}/{placement-lowercase}/{id}`, replacing `diaries/years/{diaryId}/{year}/{placement-lowercase}/{id}`. Preserve the existing fragment identity topic and dated publication semantics. Year-only records must appear in the database-derived startup topic map.
4. The physical Diary page is the editor navigation context only; the Annual editorial content UI selects year explicitly, including from an empty physical Diary, and selects PREAMBLE or EPILOGUE. The same year opened from two Diaries addresses the same collection. Navigation Diary IDs must not become annual owners.
5. The Reader must consume year-owned annual fragments and preserve existing viable physical URLs during 0054. Calendar-first public navigation belongs to the subsequent 0053 feature.
6. Implement one feature-local, repeatable database migration, with dry run, transactional constraint/data updates and an audit manifest preserving original annual Diary, month, day and placement. Test idempotency and backout against local/disposable data; do not insert one-off migration logic into permanent Playbooks roles.

## Startup MQTT reconciliation and rollback (simplified decision)

The responder's `Synchronise.java` captures retained topics, calls `context.loadFromDatabase()`, publishes missing/changed database entries (`addNewEntries`), and deletes orphaned retained topics (`removeOrphanEntries`, retained zero-byte payload); it subsequently checks topic key agreement. **PostgreSQL remains authoritative.** The Step 2 implementation MUST generate canonical year-only topics through this database-derived map, and confirm by integration test that a startup:

- creates missing new annual year-only topics;
- tombstones the legacy diary/year annual paths;
- preserves the expected fragment identity and dated branches;
- converges after a restart and repeats without stale/duplicate annual topics.

**A separate MQTT payload export/restore utility is not required for 0054.** No MQTT snapshot archive, dedicated rollback publisher or new permanent Playbooks role is part of the feature. Inventory screenshots are sufficient baseline evidence, but do not constitute executable rollback archives. The previously proposed `annual-retained-snapshot.py`, its README and standalone tests are withdrawn.

**Rollout:** before production change, recheck revisions and capture a *fresh*, verified complete PostgreSQL + matching files recovery point. Quiesce write activity; migrate the schema/data and roll out compatible responder, client and Reader together, then allow responder startup reconciliation. Verify SQL IDs/counts/content/constraints and retained topic key/payload shape; test fresh MQTT subscribers and editor/Reader behaviours. Avoid mixed old/new consumers. No production deployment authorised by Step 1 closure.

**Rollback:** stop writers, restore the pre-cutover matching PostgreSQL/files dataset and compatible prior application images, restart the old responder, and let its existing startup reconciliation republish legacy topic keys and tombstone new ones. Verify both topic trees, SQL records and UI/Reader access. This depends on correctly restored schema and responder being able to start; demonstrate forward and reverse reconciliation against disposable/local state during Step 3. No repeat of previously accepted expensive full restore testing is required solely for Step 1.

## Separate operational finding (does not block 0054)

On `mars`, unprivileged `diaries-backup-status` reports invalid JSON because its underlying history operation cannot read `/etc/btrfs-snapshot-manager.json` (root-owned, mode `0600`). `sudo diaries-backup-history --config /etc/btrfs-snapshot-manager.json list` successfully reports verified retained backups. Do not weaken configuration permissions to resolve this feature; address status-command diagnostics/access separately.

## Step 1 gate determination

**CLOSED (documentary gate).** Source, schema and retained-state inventories agree; placement/editor/Reader/RPC ownership contract is agreed; backup capability is verified; and responder-derived MQTT reconstruction replaces dedicated MQTT rollback tooling. Step 2 implementation and cutover preflight remain outstanding; no tests or deployment are claimed complete beyond the cited baseline checks.
