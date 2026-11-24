# 0028-FEAT — Production release execution package and rollback gates

Prepared 24 November 2026 from the uploaded `diaries-sources-20261124-090430.zip`, `playbook-sources-20261124-084655.zip`, and the accepted Step 3 terminal receipts. **This is a production release preparation package, not an approval to execute the migration.** It does not mark any formal feature step CLOSED.

## Accepted evidence — do not repeat expensive rehearsals

- Reviewed source scope: **71 in-place IMAGE conversions**, one `DEFER` (Fragment **1564**), 30 external links and 22 same-identity Marquees.
- Isolated Java/PostgreSQL conversion, negative approvals, per-date rollback/restart, journal idempotence, MQTT replay and Reader/Editor visual samples passed in Step 2. Separate Editor lock-release defect is 0053-DEF.
- Read-only production source comparison passed at **2026-11-24 09:53 UTC**; repeat **once, after verified writer isolation, immediately before approved apply**.
- Both `mars` and `backup` report healthy retained `production/20261124-003112Z` manifest identities. Both have DB dump and Files inventory components.
- The actual custom PostgreSQL dump from `mars` restored into network-disabled PostgreSQL 18 on Windows (2,331 Fragments, 2,270 Marquees, 85 Images, 683 Pages). Three sampled retained Files payload hashes passed. **Complete Files restore has not been verified.**
- Live writer survey and offline release assessment passed. PostgreSQL had an externally published host port and two observed client sessions at the accepted survey; this is NOT positive writer isolation.

## Source-derived controls and precise names

| Layer | Actual production / source interface | Notes |
| --- | --- | --- |
| Docker **container** | `diaries-postgres` | PostgreSQL 18; a host port is published |
| Compose **service** | `diaries-db` | Use in `docker compose ... stop/exec`, **not** as `docker inspect` name |
| Docker **container** | `diaries-mosquitto` | MQTT |
| Compose **service** | `diaries-mqtt` | Use in `docker compose ...` |
| Responder | `diaries-responder` | The container has `restart: unless-stopped`; it holds the live `/config/responder.json`, `/data/files` mounts |
| Supervisor | `diaries-compose.service` | Unit `ExecStop` invokes deployment `stop.sh`; do **not** stop this unit to isolate *just* the responder: it could bring down DB/MQTT |
| Backup | `diaries-complete-backup-publish.timer` and `.service` | Publisher may itself stop and restart the responder |
| Backup launcher | deployment `scripts/backup-dataset.sh` | Actual `.service` selects `fixed-capture-preflight` + `fixed-capture` **or** `publish-preflight` + `publish` |
| Migration CLI class | `com.rsmaxwell.diaries.responder.migration.migration0028.Migration0028ReviewedFragments` | Separate Java main; **not** automatically run by responder startup |
| Journal schema | `diaries-responder/src/main/resources/migration0028/001-create-journal.sql` | **Not** installed by Java CLI; separately reviewed production SQL operation |

The Java `apply` requires `--mode apply --manifest ... --output <new-dir> --config ... --plan ... --approval ... --permit-production-apply YES` and a JSON `0028-apply-approval-v1` with exact plan/input/database/files identities, explicit owner/time, scope `PRODUCTION`, verified backup and accepted rehearsal SHA-256 references, and `writer_state=OFFLINE_WRITERS_STOPPED`. A correctly shaped approval file is **not proof** that writers really stopped.


## Disposable one-shot migration CLI — accepted design

The 0028 Java main is **temporary tooling**, not an ongoing production function or a new responder endpoint. It must be invoked only as a one-shot command. The normal `diaries-responder` service must never automatically run it, and **do not redeploy the production responder just to obtain it**. The build below creates a **disposable fat JAR** (containing responder dependencies and a separate migration main), not a permanent migration daemon or service. It may be staged transiently in a controlled runner only after the runtime design is approved; remove those staged executable bytes once postflight/rollback acceptance allows.

**Retain until the rollback window has closed:** the exact JAR/checksum, source commit, reviewed inputs/plan, owner approval, SQL journal and execution/postflight receipts under this feature's private evidence. The migration executable and source must remain available for forensic review or a separately authorised retry until acceptance; do not delete them immediately after `apply` returns.

**At formal feature closure:** remove the migration-specific CLI entry point, Gradle migration task and other one-off implementation from the **responder source in a separate reviewed commit**; keep the historical Git revision and change-control records. Do **not** drop database journal tables or remove migration evidence as part of routine executable cleanup. Any database journal/schema removal requires a separate retention decision. The normal responder remains independent of this tool, with no permanent migration service, endpoint, installed command or scheduled job.

## Phase A — prepare a pinned, separate migration executable (Windows, Cygwin)

Do this **before** requesting any production maintenance approval. Apply this ZIP with Beyond Compare 4 at the Diaries parent root.

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/prepare-0028-step3-release-artifact.sh'
```

This refuses to build a purportedly pinned artifact from a **dirty responder submodule**. If it fails, review the local source changes and commit intended code in that submodule **manually**, then decide whether/when to update the parent Git submodule pointer. Do not reset/discard uncommitted work. The tool builds one fat JAR with Gradle, verifies that it contains the 0028 main and journal SQL resource, and hashes a private copy. It does not publish an image or alter production. Source ZIPs do not contain `.git` history; **only the user's live Windows checkout can supply the actual commit identity**. Compare that with `mango` before deploying anything.

**Important runtime issue:** production responder image `0.0.9-build-86` was observed at the previous survey; the new migration CLI is in the local source but not proven in that deployed image. Do NOT silently upgrade the responder to obtain the CLI. Plan a separate one-shot Java runner using the exact fat JAR SHA, production DB connectivity, and read-only `/data/files` mount. Reusing the existing responder *image runtime* with a **mounted JAR** may be feasible, but the network, mount and Java compatibility must be validated against the read-only live contract first. No one-shot container launch or staging transfer is authorised by this package.

## Phase B — current execution contract (Windows, Cygwin; read-only SSH)

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/inspect-0028-step3-release-runtime.sh'
```

This reads only Docker inspect and systemd properties on `pluto` and records container image IDs, Compose service names, working directory, config-file labels, mount targets/read-only flags, network names, DB port bindings, backup service state and restart policies. It deliberately **omits** `.env` values, config contents, NAS credentials and DB passwords. Results are in ignored private Step 3 evidence; they do **not** establish writer isolation.

## Phase C — bind the artifact, runtime and accepted restore receipt (Windows, Cygwin; offline)

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/assess-0028-step3-final-release-candidate.sh'
```

It refuses mismatching JAR bytes, unexpected container/Compose identities, PostgreSQL 18 drift, wrong restored counts or any earlier evidence claiming production approval. **Its success result is always `RELEASE_CANDIDATE_PREPARED_NO_PRODUCTION_PERMISSION`.**

## Phase D — executable maintenance plan, only after separate owner approval

**Do not run these maintenance-stage operations yet.** Before the final execution commands can be frozen, the private Phase B runtime inventory must be reviewed for an exact safe isolation method covering external DB port clients, Docker-network connections, Nginx authoring ingress and possible other writers. The service state is potentially time-sensitive. No generic firewall edits, DB role revocations, Docker network disconnects or broad `docker compose down` are implicitly authorised.

1. **Explicit owner signoff:** close Step 1 and Step 2 only on the accepted evidence; name precise reviewed manifest and hashes, migration source commit/JAR digest, planned outage, rollback deadline, and authorised scope (71 conversions, one `DEFER`, preserved links/Marquees). Do not substitute the earlier rehearsal plan: production DB/Files identity will differ.
2. **Inspect current running services and retain original values.** On **Windows Cygwin**: `ssh pluto 'systemctl show diaries-compose.service diaries-complete-backup-publish.timer diaries-complete-backup-publish.service --property=LoadState,ActiveState,SubState,UnitFileState --no-pager'`. Confirm the current Compose working directory and `.env` path from the private runtime survey. Check the deployed service: `ssh pluto 'systemctl cat diaries-complete-backup-publish.service'`. No secrets in shared receipts.
3. **Positive writer exclusion:** block the Editor/new RPC ingress without affecting unrelated shared-Nginx services, drain active editor sessions and check Fragment locks. Coordinate backup scheduler and any active capture so no timer/service restarts responder. Stop **only** the responder Compose service (`diaries-responder`) without stopping PostgreSQL or MQTT. Separately isolate *all* direct PostgreSQL writer connections including the published host port. Keep one controlled migration connection permitted. Verify no unaccounted writers/reconnections; otherwise **ABORT**.
4. **Fresh matching rollback point:** with writers positively stopped, run the **actually deployed** complete-capture mode and verify that it does not bring up the responder if it was already stopped. In uploaded `production-complete-dataset.py` regular capture records `was_running` and restarts the responder **only when it was running at capture entry**; verify the installed fixed-capture branch independently. Confirm DB and Files match the same capture, manifest verifies, and copy/replication to `mars` and `backup` is actually complete. Pin the rollback copy against pruning. No snapshot deletion or destructive restore is allowed without specific consent.
5. **Final fresh source lock:** while writers remain isolated, perform the strict existing 0028 read-only production freshness comparison, requiring reviewed 71/1, 30 external links, 22 Marquees with preserved associations, no reviewed locks, Image catalogue checksums and no source/version drift. If comparison changes, **ABORT** rather than silently regenerate decisions.
6. **Production-only Java dry-run:** use the pinned, tested one-shot CLI JAR with the actual production `/config/responder.json` and read-only `/data/files` through a separately verified runner environment. `--mode validate-manifest` first (offline), then `--mode dry-run` on production; freeze and hash the **new** plan. The tool writes its output only to a new *private evidence* directory. Check 71 planned conversions and exactly Fragment 1564 deferred.
7. **Journal and signed apply:** perform a separately reviewed journal schema install via controlled `psql` only after recovery and frozen preflight are accepted. Hash the exact production plan and approval JSON. Execute the one-shot Java `--mode apply --permit-production-apply YES` **only after the owner's separate written authorisation**, with all hard gates verified and preserved in private receipts. The executable itself is fail-closed on plan/manifest/database/files mismatches and journals date-level work, but it does not independently shut off writers. Never automatically rerun a partially committed apply: inspect the authoritative SQL journal and per-date progress first.
8. **Database postflight then MQTT reconciliation:** run CLI `--mode postflight` against the same frozen plan with writers still closed. Only after DB postflight passes, permit controlled responder startup for DB-to-MQTT retained replay; verify the 71 Fragment and 22 Marquee topics, unchanged Page associations, links, chronology, deferred 1564, and expected tombstones/unchanged topics. Test representative Editor and Reader images/links before reopening authoring ingress. Treat a startup replay timeout or unexpected retained state as STOP, not success.
9. **Controlled reopen or rollback:** if verification passes, restore exactly the original backup timer/supervisor/ingress states and check health. If it fails, leave writers closed; decide between completing a partial journaled transaction and an explicitly approved matching DB **and** Files restore. Restoring a previous state destroys later writes and requires separate destructive-operation approval. Reconcile MQTT retained topics against the restored DB and remove stale retained entries as specifically verified before reopening.

### Important source facts and limits

- The 24 November source contains the `fixed-capture` option as a separate branch; **the deployed systemd service and its configuration, not this source template, determine which command is safe at execution**.
- The SQL journal script is explicitly documented as a separate reviewed operation. Running `apply` without that schema does not install it.
- The production DB is Postgres 18. The built responder fat JAR is Java-dependent. Verify that the chosen runtime image and JVM version support this exact artifact; do not assume the already running image has the new class.
- Both the original Reader/Editor users and the broker may reconnect while the responder is stopped. Responder stopped is **necessary, not sufficient** for writer isolation.
- The accepted backup restore test proved the **database** restore and **three** Files samples, not the full Files dataset or a production rollback.

## Owner release decision — OPEN

| Gate | Decision required |
| --- | --- |
| Formal Step 1 source/manifest signoff | OPEN |
| Formal Step 2 functionality/rehearsal signoff | OPEN |
| Exact clean responder source, submodule and JAR digest | Pending Phase A |
| Current pluto Compose, Docker mount, Java, systemd identities | Pending Phase B |
| JAR/runtime/recovery binding | Pending Phase C |
| One-shot Java production access design and no automatic responder upgrade | OPEN |
| All writer paths demonstrably isolated; original supervisor states recorded | OPEN |
| Fresh writer-stopped complete DB+Files recovery point, replication and pin | OPEN |
| Frozen production plan, explicit owner apply approval and tested rollback deadline | OPEN |
| Production apply, DB journal postflight, MQTT replay, Editor/Reader acceptance | NOT EXECUTED |
| Formal 0028 closure | OPEN |

The deliverable is **release engineering preparation, not a production change**. Retain existing successful test and backup evidence. After Phase A/B/C results, freeze the remaining exact one-shot runtime and writer-containment commands from actual observed state; do not guess live port/IP/credential values.
