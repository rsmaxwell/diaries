# Running Ledger with a Local Docker Build

Use this mode to run the whole Ledger stack locally from the current source tree.

This mode starts:

- `ledger-client`
- `ledger-server`
- `ledger-db`

It uses:

```text
compose.yaml
.env
```

and builds local images from:

```text
ledger-client/Dockerfile
ledger-server/Dockerfile
```

## When to use this mode

Use local Docker build when you want to:

- test the complete application from the current source tree
- confirm the client, server and database work together in containers
- validate Dockerfiles and Compose configuration
- run full-Docker smoke tests
- run full-Docker server API tests against a clean disposable database

## Architecture

```text
Browser
  |
  | http://localhost:4200
  v
ledger-client container
  |
  | Nginx serves the built Angular app
  | Nginx proxies /api/* requests
  v
ledger-server container
  |
  v
ledger-db container
```

## Start the local Docker build stack

From the top-level `ledger` project on Windows:

```bat
scripts\windows\local-docker-build\start.bat
```

Open the application:

```text
http://localhost:4200
```

## Stop the stack

```bat
scripts\windows\local-docker-build\stop.bat
```

## Check container status

```bat
scripts\windows\local-docker-build\status.bat
```

## View logs

View all logs:

```bat
scripts\windows\local-docker-build\logs.bat
```

View logs for one service:

```bat
scripts\windows\local-docker-build\logs.bat ledger-server
```

or:

```bat
scripts\windows\local-docker-build\logs.bat ledger-client
```

## Rebuild and restart one service

Rebuild the server image and restart the server container:

```bat
scripts\windows\local-docker-build\rebuild-server.bat
```

Rebuild the client image and restart the client container:

```bat
scripts\windows\local-docker-build\rebuild-client.bat
```

## Restart one service without rebuilding

```bat
scripts\windows\local-docker-build\restart-server.bat
scripts\windows\local-docker-build\restart-client.bat
```

## Reset the database

This deletes and recreates the local Docker build database volume. Use it when you want a clean local database.

The script then starts the Docker stack again, allowing Flyway migrations to recreate the database schema.

```bat
scripts\windows\local-docker-build\reset-db.bat
```

## Import sample data

Run this after the database and server are available:

```bat
scripts\windows\local-docker-build\import-sample-data.bat
```

The sample import creates:

- one customer
- one customer user
- one customer device
- one per-user product
- one per-device product
- one account-level product
- one per-user subscription
- one per-device subscription
- one account-level subscription

The script calls the normal REST API and captures the IDs returned by the server, so it does not assume that the sample records will have database IDs starting at `1`.

## Back up and restore the database

```bat
scripts\windows\local-docker-build\backup-db.bat
scripts\windows\local-docker-build\restore-db.bat
```

## Run smoke tests

Smoke tests check that the containers and basic HTTP endpoints are responding.

```bat
scripts\windows\local-docker-build\smoke-test.bat
```

## Run server API tests

The full-Docker server API test is intended for a clean, disposable development database.

It creates, updates and deactivates records using fixed test values. Do not run it after importing sample data, because the sample data uses some of the same product codes and the test may correctly fail with `409 Conflict`.

Recommended order when validating the API tests:

```bat
scripts\windows\local-docker-build\reset-db.bat
scripts\windows\local-docker-build\test-server-api.bat
```

If you also want to test the sample-data import, reset the database again before importing the sample data:

```bat
scripts\windows\local-docker-build\reset-db.bat
scripts\windows\local-docker-build\import-sample-data.bat
scripts\windows\local-docker-build\smoke-test.bat
```

## Linux equivalents

Linux whole-application helper scripts are in:

```text
scripts/linux
```

The corresponding scripts include:

```text
start.sh
stop.sh
status.sh
logs.sh
reset-db.sh
import-sample-data.sh
backup-db.sh
restore-db.sh
smoke-test.sh
test-server-api.sh
rebuild-server.sh
rebuild-client.sh
restart-server.sh
restart-client.sh
```

## Shared local PostgreSQL data

The Windows scripts load `config/environments/local-docker-build.env` first and `config/environments/local.env` second. `local.env` therefore supplies machine-local overrides.

To use the same PostgreSQL data as development-infrastructure and local-published-smoke, copy `config/environments/local.env.example` to `config/environments/local.env` and set:

```text
LEDGER_DB_DATA_DIR=./data/database/common
```

The PostgreSQL service bind-mounts this directory at `/var/lib/postgresql`. Run only one of the three local modes at a time when they share this directory.

