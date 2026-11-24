# 0028 — Isolated database integration and failure/restart rehearsal

**Prepared 23 November 2026 — NOT YET RUN against Windows Docker or production data.**

This package follows the accepted 0028 read-only Step 1 reconciliation and local
Step 2 Gradle/JUnit checks (23 November 2026). It does **not** grant production
apply approval, implement MQTT replay or close Step 2/3.

## Operator — Windows PC Cygwin

Apply the small ZIP at the Diaries parent repository root in Beyond Compare 4.
Keep `diaries-responder` and unrelated working-tree changes intact.

From a Cygwin Bash terminal, with Docker Desktop running, invoke:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'

bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/rehearse-0028-step2-isolated.sh'
```

The runner uses the already reviewed private manifest at
`evidence/Step 1/private/20261123T144651Z-reviewed-manifest-prepared`.
It records branch/HEAD/status for parent and responder before testing; it does
not commit, stage or reset Git work.

### Isolation boundaries

- **Production `pluto`:** a consistent `pg_dump -Fc` read from
  `diaries-postgres`, nothing written to the container/DB. No backup snapshot
  creation, pruning, replacement or restore on pluto/mars/backup.
- **Windows local development DB:** not touched. The script creates a separate
  Docker container **`diaries-0028-rehearsal-db`**, named volume
  **`diaries-0028-rehearsal-pgdata`**, database `diaries_0028_rehearsal`, and
  binds PostgreSQL only on **127.0.0.1:55428**. Existing container/volume
  names cause the script to refuse a second restore instead of overwriting.
- **Media:** copies only the referenced catalogue Image files to a new
  `files-root/` inside the private feature evidence directory, verifying
  each source and destination SHA-256 against the approved 71-row manifest.
  Source files are never modified. By default, the effective development
  `DIARIES_CONTENT_DIR` and `DIARIES_FILES_DIR` configuration is used.
  If no matching local Files-root is found, set
  `DIARIES_0028_SOURCE_FILES_ROOT` to a verified Cygwin path to the existing
  image Files-root and rerun (no database is started until media checks pass).
- **Java config:** generated with fixed local host/port and staged Files-root;
  no production credentials. Only the ephemeral labelled DB can receive SQL
  writes from this workflow. There are no MQTT calls.

### Consolidated checks

1. Tests the helper scripts, verifies prepared manifest hashes and copies
   the reviewed image bytes independently with SHA-256 checks.
2. Creates the isolated PostgreSQL 18 instance, saves a **PRIVATE** production
   dump with a SHA-256 receipt, restores it and checks fragment count.
3. Runs the real compiled Java `analyse` and `dry-run` against that restored DB,
   frozen manifest and staged media. Stores the exact plan and hashes.
4. Installs the versioned 0028 journal **only** on the isolated DB; verifies it
   is empty. Records full-table fingerprints for all non-migrated Fragments,
   Pages, Images and Marquees (MD5 is used solely as an equality fingerprint,
   not a security or backup checksum).
5. Verifies an intentionally invalid approval is rejected without writes.
6. Installs a temporary DB trigger to raise a controlled failure partway
   through a multi-Fragment date, then confirms that date completely rolled
   back while earlier dates remained committed. Removes the trigger.
7. Resumes and applies all 71 conversions, checks the committed source and
   occurrence journal, runs independent Java `postflight`, then re-applies
   unchanged inputs to establish idempotence.
8. Compares all protected/unrelated row fingerprints before vs after. Saves
   stdout, Gradle failure traces, database receipts and `RESULT.txt` under
   `evidence/Step 2/private/<UTC>-isolated-db-rehearsal/`.

The deliberate `invalid-approval` and `injected-failure` Gradle invocations
**must fail**. The runner counts them as a passed *negative test* only after
checking the expected rejection and database state. An unexpected failure is
reported as a **FAIL**, not concealed.

### Limitations and follow-on acceptance

- This is an isolated PostgreSQL **migration-engine integration rehearsal**,
  not yet a full restored Files-root/MQTT/Editor/Reader end-to-end rehearsal.
  It copies exactly the reviewed catalogue image files; unrelated media are
  not restored and no broker is started. Complete Step 3 UI and MQTT retained
  state verification is still required.
- The local media selection is verified against frozen catalogue SHA-256 and
  again against the restored production Image table by the Java tool; a drift
  blocks application. No live production image changes are permitted.
- Dumps, full image files and rendered plans are **PRIVATE**; do not stage
  them into public repositories or send them to non-private services.
- The isolated container and Docker volume remain available for inspecting
  failures or receipts. Do not delete until evidence is accepted. The
  optional `tools/remove-0028-isolated-rehearsal-db.sh` checks both labels
  before removing **only** these two disposable Docker objects. It does not
  delete the feature evidence directory.
- An isolated rehearsal approval JSON produced by the script is expressly
  `RESTORED_REHEARSAL`; it **cannot be used as production approval**.

## Prepared package validation

Offline tests of the media-copy and fixture helpers and Bash syntax checks
were executed against synthetic data. No production DB dump or Docker
integration was run in the packaging environment. The operator's terminal log
is the acceptance evidence for the live rehearsal.
