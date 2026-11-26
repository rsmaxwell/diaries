# 0029 Step 2 — Live development cutover plan and acceptance gates (2026-11-25)

**Status:** Technical isolated migration rehearsal PASSED. **Live development migration NOT executed or authorized.**

## Accepted evidence

- 49 source HTML fingerprints verified; 49 current catalogue image SHA-256 checks PASS (48 distinct Images). Historical byte identity is not proved.
- Retained backup: `evidence/step-2-live-development-readiness/diaries-development-pre0029-20261125-201628.dump`, with matching `.sha256` receipt. This exact backup has been restored successfully into an isolated PostgreSQL 18 instance.
- Isolated migration achieved 49 receipts/49 archives, 48 converted IMAGE Fragments and 1 existing link, followed by the **unchanged** 0029 hybrid schema SQL. Final totals: 51 DATED IMAGE, 2271 DATED TEXT, 9 PREAMBLE TEXT, 0 invalid ownership relations.
- Automated application checks passed: responder, reader and Angular (258 tests). No post-migration live editor/reader/MQTT acceptance yet.

## MQTT synchronisation evidence from source

`diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/sync/Synchronise.java` snapshots separate retained branches (`diaries/fragments/#`, `diaries/dates/#`, `diaries/years/#` and others). It publishes missing/changed DB entries and removes orphaned retained entries using zero-byte retained QoS 1 messages. It validates the resulting map. **Use the new compatible responder's startup reconciliation; do not blindly clear `diaries/#`.** Startup success must be verified from logs and topic-tree snapshots.

## Cutover acceptance (not yet granted)

1. **Editorial mapping:** Explicitly approve all 49 source→Image/Page mappings and caption/text handling. Particularly confirm 611–613 to Page 756. The tested conversion SQL is marked *isolated rehearsal only*; it is not an authorized live conversion script.
2. **Source recovery:** Pin exact parent/submodule revisions and confirm source baseline immediately before cutover. Preserve the retained, restore-tested backup. If the live database has changed since it was captured, obtain and restore-test a fresh logical backup first.
3. **Service quiescence:** Identify and stop the actual development responder (potentially IDE-launched, not visible in `docker ps`), verify no old responder is writing, and prevent old/new version overlap. Keep DB/MQTT running as necessary.
4. **Migration:** Only after authorization, use an approved source-guarded live executor. Apply the tested 49-record conversion and unchanged hybrid schema in the correct order. Capture command outputs, transaction receipts and a postflight; abort on any count/hash/version discrepancy.
5. **MQTT reconciliation:** Start the new compatible responder, verify startup synchronization/normalization logs and retained `fragments`, `dates`, `years` trees including tombstones. Check reader/editor navigation, annual preamble, images 598/606, 611–613, 1738/2061, and synthetic POSTAMBLE.
6. **Rollback:** `step2-hybrid-schema-rollback.sql` alone cannot restore legacy HTML/49 sources. Stop the responder, restore the full pre-0029 custom-format backup to a controlled DB, restart a compatible older responder and reconcile MQTT; **this precise full rollback path has not been rehearsed**. Preserve existing backups and snapshots.
7. Production deployment is separate and requires its own authorization and acceptance.

## Read-only transition gate

**Windows 11 Cygwin Bash, Diaries parent repo:**

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
FEATURE="change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling"
bash "$FEATURE/tools/step2-live-development-transition-gate.sh"
```

The gate checks backup hash, SQL hashes, Git revisions/dirty state, DB identity, legacy counts `60:11:3`, and unexpected migration receipts. Docker inventory is contextual and cannot prove an IDE responder has stopped. It performs **no database or MQTT writes**. Keep logs in this feature's evidence directory.

**Step 2 remains OPEN** pending accepted editorial mapping, a verified cutover/rollback procedure, authorized live migration and integrated editor/reader/MQTT postflight.
