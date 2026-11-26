# 0029 Step 2 — Approval-gated live development cutover handoff (2026-11-25)

Status: **PREPARED, NOT EXECUTED, NOT APPROVED**. Database target is hardcoded `diaries-development-db` (database/user `diaries`). Production is excluded.

## Evidence and inherited acceptance

The source is 60 Page-less rows (11 reviewed; 49 embedded-image legacy), 3 IMAGE Fragments. A retained custom-format backup from 20:16 was restored and replayed successfully. Isolated conversion + *unchanged* hybrid schema produced 49 receipt rows, 49 archives, 9 annual PREAMBLE TEXT, 51 dated IMAGE, 2,271 dated TEXT and 0 invalid ownership rows. Current on-disk catalogue SHA-256 passed for all 49 occurrences. The 49 mapping rows, including the provisional Alexander Nevsky assignments 611–613→Page 756, and replacement of embedded HTML with escaped caption paragraphs remain **editorially unapproved**. Original embedded HTML remains in the archive and prior preflight CSV.

## Package

`tools/step2-live-development-cutover.sh` defaults to `--plan`. In plan mode it verifies pinned SQL SHA-256 against the successful rehearsal (`f6dbd065...`, `563cb107...`), backup checksum, Git/submodule identities, hardcoded development DB identity, legacy counts and absence of existing migration receipts. It cannot determine whether an IDE responder is running; operator inspection and shutdown remain required. Plan mode does not write to the database or MQTT.

The `--execute` path is technically implemented but blocked by explicit editorial approval and an IDE responder shutdown attestation. **DO NOT run `--execute` unless the user has expressly authorised this exact 49-record mapping, caption replacement and the live development cutover.** Before the first database write it creates a fresh custom-format dump, checks pg_restore TOC, saves SHA-256, then runs the unchanged isolated-rehearsal conversion SQL and hybrid SQL sequentially against the fixed development database. It postflights `49:49:9:51:0`. The SQL includes source checksums, Page ownership, IMAGE collisions, 11-row set and transaction abort guards. Source working trees are not modified.

**Important:** the two SQL files commit separately. A failure after conversion but before/within hybrid migration leaves a partially migrated development database. Keep the responder stopped, retain the log and restore a full pre-cutover custom backup. The schema-only rollback file is insufficient. The `migration0029_rehearsal_receipt` table retains its historic name because changing SQL would break the exact tested fingerprint; its use on the eventual development DB is an audit artifact, not proof of production execution.

## Development cutover operational runbook (after approval only)

1. Windows Cygwin, at parent repository root: inspect responder logs and ensure the locally IDE-run responder process is stopped; ensure no alternative responder container and no concurrent editor writes; keep development DB and MQTT running. Record process and relevant broker topic-tree baselines in feature evidence.
2. Run `tools/step2-live-development-cutover.sh --plan`, check PASS. **Do not execute without approval.**
3. On explicit authorisation, provide the two exact approval attestation variables to `--execute`, ensuring you are in Windows Cygwin and the expected repository checkout. Confirm the fresh backup receipt before the SQL phase; on any failure retain backups and do not start a mixed-version responder.
4. Verify DB postflight (49 receipts, 49 archives, 9 preambles, 51 IMAGE, 0 invalid ownership). Start only the updated 0029 responder. The startup Synchronise implementation reconciles retained `diaries/fragments/#`, `diaries/dates/#`, `diaries/years/#`; capture startup logs and inspect retained topics (including deletes/tombstones). Do not bulk-clear `diaries/#`.
5. Verify client & reader end to end: 1828/1829/1830 annual preambles above Jan 1, normal dated pages and chronology, images 598/606 and 611–613, 1738/2061 placement, existing Whitley Park reference, create/edit/delete an annual test Fragment and POSTAMBLE behaviour on development only. Preserve screenshots/logs under feature evidence.
6. Failure/rollback: keep responder stopped. Use the fresh pre-cutover custom-format backup and documented retained backup to restore a controlled empty database with PostgreSQL `pg_restore --exit-on-error --no-owner --no-acl`. **Never restore blindly over a populated schema**. Before replacing or dropping any development database, obtain explicit destructive-operation approval and preserve the post-failure database/evidence. Restart only the previous compatible responder and reconcile retained MQTT state; acceptance of rollback requires database and reader checks. No automatic destructive rollback is supplied.

## Outstanding approvals

- Explicit acceptance of all 49 source→Image/Page mappings and conversion of HTML into caption text (particularly 611–613→Page 756 and caption-less sources).
- Explicit authorisation to modify **live development** PostgreSQL, with development responder stopped.
- Detailed rollback operation remains a controlled manual operation; the pre-cutover backup is retained.

0029 Step 2 remains **OPEN**; no production change is authorised.
