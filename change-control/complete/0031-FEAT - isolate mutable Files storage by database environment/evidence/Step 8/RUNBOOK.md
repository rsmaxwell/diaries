# Step 8 runtime runbook

This runbook assumes the Step 5/7/8 Playbooks source has been deployed to
production and that the production inventory explicitly contains:

```yaml
diaries_files_dir: files
```

Do not run a normal full-stack `stop.sh`; PostgreSQL must remain available for
the production `pg_dump`.

## 1. Freeze local writes on Windows

From the Diaries project root:

```bat
scripts\windows\0031-step8\freeze-local-writes.bat
```

If it reports TCP/8081 still listening, stop the direct Java responder and rerun
until the script reports PASS.

## 2. Freeze production writes on pluto

```bash
cd ~/projects/diaries
./scripts/step8-freeze-writes.sh
```

Do not restart the responder.

## 3. Capture the effective local database

Ensure exactly one local Diaries database mode is running, then:

```bat
scripts\windows\0031-step8\capture-local-database-backup.bat
```

With the normal `local.env` common override, this is one `common` database
backup for all three local launch modes.

## 4. Capture the production database

On `pluto`:

```bash
cd ~/projects/diaries
./scripts/step8-capture-production-database-backup.sh
```

## 5. Snapshot the frozen shared Files tree

Back on Windows:

```bat
scripts\windows\0031-step8\capture-shared-files-snapshot.bat -ProductionWriteFreezeConfirmed
```

If the inferred UNC path is not available in the current Windows session, pass
the mapped path explicitly, for example:

```bat
scripts\windows\0031-step8\capture-shared-files-snapshot.bat ^
  -ProductionWriteFreezeConfirmed ^
  -SharedFilesRoot "P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files"
```

## 6. Preserve evidence and keep writes frozen

Copy the small production evidence files from:

```text
~/projects/diaries/data/0031-step8/
```

into this Step 8 evidence directory. The Windows scripts already write their
small runtime evidence here by default.

Do **not** copy the full per-file NAS inventories into Git. Preserve them beside
the snapshot and retain their hashes in `SNAPSHOT-MANIFEST.json`.

Do not restart either responder yet. Step 9 should examine the frozen pre-split
state.
