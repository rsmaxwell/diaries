# 0028-FEAT — Step 3 retained recovery proof and live writer-channel inventory

**Prepared:** 24 November 2026. **Status:** execution package; live checks NOT yet executed. **Production migration NOT authorised.**

## Why this increment is needed

Previously accepted evidence establishes:

- Reviewed 72 legacy occurrences: 71 `CONVERT_TO_IMAGE`, one `DEFER` (1564); 30 original links and 22 Marquees preserved.
- Real restored-production *migration* rehearsal: date-level rollback/restart, idempotence, 71 source and 71 occurrence journals, MQTT retained replay, Reader/Editor visual checks. This work must not be repeated merely to collect more evidence.
- Production source freshness `PASS_SOURCE_FRESHNESS` at 24 November 2026 09:53:20 UTC, with 70/70 NAS catalogue media checks and no active locks (point-in-time only).
- Both `mars` and `backup`: `HEALTHY`, zero manifest conflicts, selected common backup `production/20261124-003112Z`.
- On 24 November, paired retained metadata inspection: matching manifest digest, DB custom and SQL dumps present at expected sizes, Files inventory/hash list present and matching. **This is not a restore proof.**

This increment verifies the **retained custom-format dump itself**, not another live production `pg_dump`, and obtains a current read-only writer-channel survey. The original source snapshot and already migrated isolated environment stay untouched.

## Exact execution

Apply the ZIP at the Windows Diaries parent repository root with Beyond Compare. In the **Windows PC — Cygwin terminal**:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/verify-0028-step3-retained-restore-and-writers.sh'
```

The script:

1. Saves Windows parent/submodule revision and status. Requires the accepted local paired-component receipt from `20261124T101320Z-retained-components`; does not assume working trees are clean.
2. Via SSH on `pluto`, runs only read-only Docker/systemd/PostgreSQL inspection. Captures container versions, restart policies, published ports, database client groups and login-role names **without passwords or SQL query text**. Production writer isolation is **not** claimed.
3. Via existing `sudo -n` on `mars`, selects exact retained production backup `20261124-003112Z` through `diaries-backup-history show`. Validates its manifest SHA against the **accepted mars/backup matched receipt**, selected dump path/declared size/SHA, verified Files inventory and three actual Files payload hashes. No snapshot, backup or live production file is altered.
4. Creates a **new, uniquely named Docker volume** `diaries-0028-retained-restore-pgdata` and container `diaries-0028-retained-restore-db` on the **Windows PC** using the already locally available `postgres:18-alpine` image. The container has Docker `--network none`, **no published ports**, and no production credentials. Both resources are retained for inspection. The command refuses to run if either already exists, to prevent destructive re-restores.
5. Streams the accepted retained PostgreSQL custom dump through SSH directly to `pg_restore` in this **new isolated database**, verifying the entire dump SHA-256 as it is streamed. No separate dump copy is left in the Windows repository. Records both SSH and restore exit statuses, then reads Fragment, Marquee, Image and Page counts from the restored database. Any mismatch or failure blocks the gate and retains logs/the container for diagnosis.
6. Records a private `READINESS-RESULT.json`, distinguishing a **retained database restore PASS** from the **still-open full Files restore**, maintenance-window fresh backup, writer-stop and production approval gates.

Evidence is under `change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/evidence/Step 3/private/<timestamp>-retained-restore-and-writers/` and must remain private. The only intended writes are **new private evidence** in the feature directory and **a new isolated Docker volume/database on Windows**. It makes **no changes** to production, `mars`, `backup`, the existing development environment, established recovery snapshots, or the successful 0028 migration rehearsal database.

Do **not** rerun if it fails after creating the target; inspect the retained evidence and isolated target instead. Do not use general Docker prune/volume prune. Removal requires a separately reviewed, guarded cleanup after accepting the evidence.

## Writer-isolation design informed by Playbooks

The current Playbooks `roles/diaries/templates/compose.yaml.j2` shows:

- `diaries-responder` has `restart: unless-stopped`. The production application is also managed by `diaries-compose.service`.
- `diaries-db` uses PostgreSQL 18 and publishes `${DIARIES_DB_HOST_PORT:-5433}:5432` in the template, so direct SQL clients must be handled as well as browser/MQTT RPC writers.
- The frontend is served by shared Nginx, with `/diaries/` Editor, `/diaries-responder/` and `/mosquitto/` routes. Writer ingress cannot safely be isolated simply by stopping the responder.
- `diaries-complete-backup-publish.timer/service` may start `backup-dataset.sh`, which stops and restarts `diaries-responder` during backup capture. This must be coordinated with any maintenance window.
- The general `stop.sh`/Compose shutdown path is **not** an acceptable writer-stop tool for migration because PostgreSQL must remain available.

The **live** read-only writer survey in this package records current service identities and client groups; those observations must be reviewed before choosing an exact reversible mechanism. No stop/firewall/revoke/systemd commands are executed by this package.

### Proposed future production sequence — NOT executable authorisation

1. Record owner's formal Step 1/Step 2 evidence acceptance and obtain separate approval for exact production run, pinned manifest/git/Images, downtime and rollback terms.
2. At the authorised maintenance window, coordinate/suspend the backup scheduler *safely*, place user-facing Editor/RPC ingress in maintenance mode, stop/drain the responder and verify its supervisor will not restart it. The Reader may remain read-only if compatible and safe.
3. Block/reject all non-migration direct database writers **without stopping PostgreSQL**; verify through live `pg_stat_activity`, published host port controls and network/role exposure. No unreviewed SQL grants, configuration changes or broad `iptables` rules. If complete isolation cannot be demonstrated, abort.
4. Take and verify the **fresh, consistent database-and-Files recovery point** using the established complete-dataset process while writers stay isolated. Record immutable dataset ID, manifest, replication/pinning outcome and restore deadline. Do not delete or overwrite old snapshots.
5. Run final strict source/Images/locks comparison **after** writer isolation; plan must still match all 71 conversions, one DEFER, 30 links, 22 Marquees and bound file checksums.
6. Only after owner approval: run approved migration in a supported production execution environment, capture durable journals, restart compatible responder for MQTT retained replay, verify all 71 records, both UIs and Marquees, and then reopen writers.
7. On any mismatch, keep writes closed and follow the explicitly accepted recovery/restore plan. A production restore is destructive to newer writes and requires explicit authorisation; do not make it an automatic fallback.

## Acceptance boundaries

| Gate | Result before this script executes |
|---|---|
| Source review, rehearsed 71 conversions, MQTT/Editor/Reader checks | Supported by prior accepted terminal and GUI evidence |
| Paired retained DB + Files metadata identities | PASS from 24 November 10:13 UTC terminal log |
| Actual retained custom dump bytes + isolated DB restore | **OPEN** |
| Three real retained Files payload SHA checks | **OPEN** |
| Full Files payload recovery | **OPEN; not attempted in this increment** |
| Live production writer topology | **OPEN** |
| Production writers stopped/isolated | **OPEN; never attempted in this increment** |
| Fresh final recovery point and exact rollback procedure | **OPEN** |
| Formal Step 1/2 sign-off and production apply approval | **OPEN — production apply NOT authorised** |

**Do not mark Step 3 CLOSED** on a successful retained database restore alone. No migration `apply` is part of this tool.
