# Development steps

1. Add `LEDGER_DB_DATA_DIR` to each mode-specific environment file, with a mode-specific default.
2. Add `config/environments/local.env.example` with `LEDGER_DB_DATA_DIR=./data/database/common`.
3. Ignore `config/environments/local.env` in Git.
4. Change all three local PostgreSQL Compose services from named volumes to `${LEDGER_DB_DATA_DIR}:/var/lib/postgresql`.
5. Remove the now-unused top-level named database volume declarations from the local Compose files.
6. Update every Windows script that consumes a mode environment file so it also validates/loads or passes `local.env` second. This gives machine-local settings precedence.
7. Update the direct `ledger-server` Windows scripts (`run-server.bat`, `test-local.bat`, and `import-sample-data.bat`) to load `local.env` after `development-infrastructure.env`.
8. Update all database backup/restore/status/start/stop/build/test commands that call Docker Compose to pass both `--env-file` arguments in the same order.
9. Update each `reset-db.bat` to delete the bind-mounted PostgreSQL data directory explicitly rather than relying on `down -v`.
10. Document the common database behaviour and the requirement that only one local mode runs at a time.
11. Before switching an existing development database, take a backup from the mode containing the data you want to preserve. After the change, create `local.env`, start one mode to initialise the common directory, then restore the backup.
