# Ledger feature 0021 - shared local PostgreSQL data

This package is based on `ledger-sources-20260819-171724.zip`.

It changes the three local Ledger modes so their PostgreSQL services use a bind-mounted data directory selected by `LEDGER_DB_DATA_DIR`, matching the Diaries application pattern.

The Windows scripts now read two environment files in order:

1. the mode-specific file under `config/environments/`;
2. `config/environments/local.env`.

Because `local.env` is loaded second, it overrides the mode defaults. Copy `config/environments/local.env.example` to `config/environments/local.env`; the supplied example uses:

```text
LEDGER_DB_DATA_DIR=./data/database/common
```

With that value, development-infrastructure, local-docker-build, and local-published-smoke all use the same PostgreSQL data directory. Run only one of those modes at a time.

`local.env` is intentionally ignored by Git.

## Important migration note

Existing databases currently stored in Docker named volumes are not automatically copied to the new bind-mounted directory. Back up the database you want to keep before applying the change, then restore it after starting one of the modes with the new common directory.

## Reset behaviour

The three `reset-db.bat` scripts have been updated because `docker compose down -v` does not delete bind-mounted database data. They now stop the stack, explicitly delete the resolved `LEDGER_DB_DATA_DIR`, recreate it, and restart the selected mode. If all local modes point at the common directory, a reset from any one mode resets the database for all local modes.

The `files/` directory contains the complete replacement version of every changed source/documentation file, preserving repository-relative paths.
