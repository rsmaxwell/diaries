# Step 2 — Retained-backup restore and transition readiness (2026-11-25)

## Previous accepted evidence
- Source database container `diaries-development-db`, PostgreSQL 18.7, remains on the old model (60 Page-less, 3 IMAGE).
- Retained archive: `evidence/step-2-live-development-readiness/diaries-development-pre0029-20261125-201628.dump` (289535 bytes); checksum receipt and TOC validated in `readiness-20261125-201628.log`.
- Prior **separate** isolated rehearsal passed: 49 archived source rows, 49 receipts, 48 converted rows + 1 existing link, 9 PREAMBLE and 51 DATED IMAGE after unchanged hybrid migration, zero invalid ownership.
- The retained archive itself has NOT been restore-tested yet.

## This increment
The attached `tools/step2-retained-backup-restore-rehearsal.sh` verifies the retained archive hash, restores the **same retained dump** into an isolated PostgreSQL 18 Docker container (`--network none`, no ports or mounts), replays the previously tested 49-row conversion and unchanged hybrid script, and verifies the schema and retained source baseline. Logs and checks remain under the feature evidence directory. The container is automatically removed on exit. This does not write the live database or MQTT broker.

## Operational transition still required before live development migration
1. **Editorial review/acceptance**: 49 destination/caption mappings; especially Alexander Nevsky 611–613 at Page 756; empty captions 980/1029/1030; Whitley Park 84/2338 and corrected images 598/606. The candidate and rehearsal receipts do not themselves constitute approval. Note that the rehearsal updates 48 existing Fragment rows in place and generates simplified caption HTML; the original full HTML resides in the isolated rehearsal archive, not live after conversion.
2. **Responder quieting**: identify running development responder container, local IDE responder process, and any client writes; agree a brief quiescent window and confirm stopped writes immediately before capture and mutation. Do not stop production services.
3. **MQTT retained topic-tree**: migration alters dates/ownership/topics; specify which retained topics are retired and what is republished from database on responder restart. Check for stale retained Fragment, date and annual year placement topics and reader/editor consistency. A database restore alone does not roll back retained MQTT state.
4. **Rollback**: retain PostgreSQL custom dump and independent MQTT snapshot/repair plan; test DB restore with live responder stopped before authorizing migration. The `step2-hybrid-schema-rollback.sql` alone does NOT reconstruct all original 49 HTML rows.
5. **Explicit authorization**: do not run either conversion SQL or hybrid migration against live development until user approves the mapping and execution plan. Production out of scope.

## Acceptance for this script
- Retained checksum PASS; isolated restore PASS; baseline 60 Page-less, 11 reviewed, 3 existing IMAGE; conversion receipts/archive 49 each, PREAMBLE 9, DATED IMAGE 51, invalid ownership 0; source remains 60 Page-less and 3 IMAGE.
- Log under `evidence/step-2-live-development-readiness/`.
- Editorial/MQTT/operational acceptance remain OPEN.
