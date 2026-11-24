# 0028-FEAT — Production maintenance and release decision runbook

**Prepared:** 24 November 2026. **Status:** PREPARATION ONLY; not permission to execute production migration. **Feature:** in-progress/0028-FEAT.

## Evidence this runbook reuses (do not repeat)

- Step 1 frozen reviewed manifest: 72 records, 71 `CONVERT_TO_IMAGE`, one `DEFER` (Fragment 1564), 30 preserved hyperlinks and 22 preserved Marquees. Technical checks passed; the **owner's formal Step 1 acceptance remains unrecorded**. Historical 0022 candidate-CSV limitation remains documented.
- Isolated PostgreSQL 18 conversion rehearsal: 71 date-transaction conversions, deliberate rollback, resume, idempotence, 71+71 journals and unchanged unrelated rows. Retained MQTT topic replay (71/71 and 22/22) and Editor/Reader GUI representative images, original scans and navigation passed. The separate 0053-DEF locking-on-undo issue is deferred, not fixed.
- Fresh read-only production source comparison: **PASS** at 2026-11-24 09:53:20 UTC. Must be repeated **after writers are stopped**, immediately before an *approved* apply.
- Both `mars` and `backup` healthy with common retained ID `production/20261124-003112Z`; matching DB and Files metadata. The custom dump from `mars` was **fully restored into an isolated, network-disabled PostgreSQL 18** on 24 Nov, yielding 2,331 Fragments, 2,270 Marquees, 85 Images and 683 Pages; three retained Files SHA checks passed. Complete Files restore remains unverified.
- Writer survey at `evidence/Step 3/private/20261124T142644Z-retained-restore-and-writers/pluto-writer-channels.json` captured production containers/ports, PostgreSQL connection groups and systemd backup states. A successful survey is **not** proof of writer isolation.

## Run the evidence-only release assessment

**Windows PC — Cygwin terminal, Diaries parent checkout:**

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/assess-0028-step3-maintenance-gates.sh'
```

This reads *existing* private evidence and records a new ignored assessment. It has **no SSH, Docker, SQL, service or snapshot side effects**. A PASS means evidence is coherent, **not** that maintenance may begin. It records the current Git parent/submodule state without assuming it is clean. The private report deliberately omits PostgreSQL usernames, client addresses and credential material; consult the original private survey if necessary.

## Verified source design and release hazards

The 24 Nov Playbooks source `roles/diaries/templates/compose.yaml.j2` has five live container names confirmed by pluto: `diaries-postgres`, `diaries-mosquitto`, `diaries-responder`, `diaries-client`, `diaries-web`. The Compose service names are **different** for the first two: `diaries-db` and `diaries-mqtt` respectively. Always distinguish `docker inspect <container>` from `docker compose ... <service>`. PostgreSQL 18 publishes `${DIARIES_DB_HOST_PORT:-5433}:5432` and therefore has potential direct SQL writers. The responder and client use `restart: unless-stopped`. `diaries-compose.service` supervises the installed stack. Shared Nginx offers `/diaries/`, `/diaries-responder/`, `/mosquitto/` and `/diaries-web` routes. The backup publisher timer/service can stop **and restart** the responder during capture; coordinate it before maintenance.

The permanent `backup-dataset.sh` supports `preflight` and the installed mode's complete capture. The template service calls `fixed-capture-preflight` and `fixed-capture` when fixed-capture is configured, otherwise `publish-preflight` and `publish`. **Do not assume which branch is currently deployed**; check the live `systemctl cat diaries-complete-backup-publish.service`, effective `.env` and installed tool help before preparing the final capture. Do not write credentials into receipts.

The 0028 Java CLI is a **separately invoked offline tool**, not invoked at responder startup. It enforces production `scope=PRODUCTION`, matching exact input/plan/dataset identities, an explicit `writer_state=OFFLINE_WRITERS_STOPPED` declaration, backup/rehearsal receipt hashes and `--permit-production-apply YES`. Those fields are **necessary but not sufficient**: their statements must be supported by actually verified maintenance evidence. The production image `diaries-responder:0.0.9-build-86` has not been demonstrated to contain this newly implemented migration CLI. Prepare a reproducible, pinned migration execution artifact capable of reaching the production database and read-only Files-root, with the current responder configuration and tested Java dependency set; **do not silently upgrade the running responder or rely on the local Windows dry-run plan for production identity**. Confirm parent/submodule commits and exact artifact digest prior to approval.

## Controlled future maintenance — not executable approval

The owner must separately approve the exact production window, scope (71 conversions + one DEFER), anticipated interruption, pinned artifact/input hashes, recovery deadline, and rollback protocol. These are the intended boundaries, **not commands to execute today**:

1. **Prepare:** obtain Step 1/2 formal evidence acceptance; confirm deployed software compatibility and a pinned runnable migration artifact; examine the private writer report for PostgreSQL login roles, active client groups and published bind addresses. Record a specific authorised direct-SQL containment design. No generic firewall/role changes or network disconnects are approved by this runbook.
2. **Coordinate backup service:** check whether `diaries-complete-backup-publish.timer` or service is active and whether any capture is running. During the *approved* window, ensure the backup scheduler cannot start a new capture and restart the responder. Preserve the original timer/service state for restoration. Do not interrupt an in-progress backup.
3. **Block the public authoring path:** temporarily deny Editor and external MQTT/RPC authoring ingress without disrupting unrelated shared Nginx services. Independently stop and drain `diaries-responder` through the **actual installed Compose service** (not a general `docker compose down`, which would stop PostgreSQL). Confirm automatic restart/other supervisors and the timer are unable to bring it back. The Reader can remain read-only only after confirming it cannot write to the affected data or retained topics.
4. **Block direct SQL writers:** there is a published PostgreSQL host port; simply stopping `diaries-responder` is *not* full isolation. Apply only a separately approved, reversible SQL/network access control tailored to the observed clients and roles, including any trusted/internal Docker connections. Confirm no non-migration sessions can write/reconnect. If no safe positive isolation mechanism is established, **abort maintenance, do not migrate**.
5. **Create fresh rollback point:** when writers are demonstrably quiesced, perform the installed, approved complete-dataset backup (DB and Files) and verify its manifest, consistency, durability and retained/replicated identity. Beware backup tooling that starts the responder: confirm its actual behaviour when the responder was already stopped. Retain and protect the pre-migration recovery dataset; do not prune or overwrite established snapshots. Record exact rollback deadline and whether the new backup is yet present on `mars` and `backup`. Do not claim remote replication has happened just because local capture succeeded.
6. **Final source lock:** run fresh production read-only inventory and strict 0028 comparison after isolation. Confirm the exact 71/1, 30 links, 22 same-identity Marquees, zero reviewed locks and current catalogue SHA. Recreate the production `dry-run` plan in the actual approved execution environment, compare digests and date order. Approval must bind the **new production plan**, not the earlier isolated Windows plan.
7. **Migration (only under separate explicit owner authorisation):** record exact Git/submodule/CLI/manifest versions, schema journal install outcome and proof of writer isolation; run `apply` using the approved manifest/plan/approval record and production permit flag. Collect per-date commit and journal outputs. On any failure **keep writers closed** and diagnose whether a date was already committed; the tool's journal enables considered resume, not automatic blind rollback.
8. **Reconcile retained MQTT:** start the compatible responder for PostgreSQL-to-retained topic replay only after DB postflight. Validate all 71 Fragment topics, 22 Marquees, chronology and preserved links. Verify both Editor/Reader visual samples and original page images; keep authoring ingress blocked until this is complete.
9. **Reopen/rollback:** if postflight passes, restore the original backup timer/supervisor/ingress states and verify healthy editors. If recovery is needed, restore a **matching DB and Files recovery point** only after explicit owner approval; that operation may destroy later writes. Rebuild retained MQTT state from the restored DB using the controlled responder replay and verify tombstones/state, then re-enable writers.

### Explicit STOP conditions

- Any active/unaccounted direct SQL client or unblocked published DB port; backup/supervisor might restart responder unexpectedly.
- Fresh backup or Files payload not verified/pinned; no accepted rollback plan; source/Marquee/link drift after quiescence.
- Production runtime/plan/version mismatch; production approval absent or missing exact receipt identities; unexpected journal counts.
- Missing independent MQTT replay/postflight or evidence that unrelated records changed.

## Owner decision record (OPEN)

| Decision | Current state |
|---|---|
| Formal Step 1 review-manifest acceptance | **OPEN** — owner has not explicitly signed this gate |
| Step 2 Java/DB/MQTT/GUI acceptance | Strong evidence; **formal owner gate record OPEN** |
| 0053-DEF | Separate non-blocking lock-release defect, not fixed by 0028 |
| Complete Files restore | Not verified (3 sampled hashes passed) |
| Production migration execution artifact | Not verified on `pluto` |
| All writer channels blocked | **OPEN** |
| Fresh writer-stopped recovery point, replication and pin | **OPEN** |
| Exact production plan, maintenance window and owner apply approval | **OPEN** |
| Step 3 production migration/replay | **NOT EXECUTED** |
| Step 4 formal closure | **OPEN** |

**No step is marked CLOSED by applying this ZIP or running the assessment.** Historical accepted rehearsals must not be repeated without a specific new justification.
