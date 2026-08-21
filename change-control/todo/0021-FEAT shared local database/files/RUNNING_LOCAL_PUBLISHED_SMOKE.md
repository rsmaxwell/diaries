# Running Ledger with Published Docker Images Locally

Use this mode after Jenkins has published images to Docker Hub and you want to prove that those published images can run locally without rebuilding either submodule.

This mode uses:

```text
compose.dockerhub.yaml
scripts/windows/local-published-smoke
```

It pulls images such as:

```text
docker.io/rsmaxwell/ledger-client:integration
docker.io/rsmaxwell/ledger-server:integration
```

The default image tag is:

```text
integration
```

## When to use this mode

Use local published-image smoke testing when you want to:

- check the images produced by Jenkins
- confirm Docker Hub images start correctly
- test a specific published image tag
- validate the image that will be deployed remotely
- avoid rebuilding local images from the current source tree

## Important difference from local Docker build mode

This mode does not build from local source. It uses already-published images.

It deliberately uses a separate Docker volume from the local Docker build stack, so it is safe to reset without deleting the normal local development database volume.

Do not run `local-docker-build` and `local-published-smoke` at the same time unless you override the client and server ports, because both modes default to:

```text
http://localhost:4200
http://localhost:8080
```

## Run the latest integration images

From the top-level `ledger` project on Windows:

```bat
set LEDGER_IMAGE_TAG=integration
scripts\windows\local-published-smoke\start.bat
scripts\windows\local-published-smoke\smoke-test.bat
```

Open the application:

```text
http://localhost:4200
```

## Pull images explicitly

```bat
set LEDGER_IMAGE_TAG=integration
scripts\windows\local-published-smoke\pull.bat
```

## Check container status

```bat
scripts\windows\local-published-smoke\status.bat
```

## View logs

View all logs:

```bat
scripts\windows\local-published-smoke\logs.bat
```

View logs for one service:

```bat
scripts\windows\local-published-smoke\logs.bat ledger-server
```

or:

```bat
scripts\windows\local-published-smoke\logs.bat ledger-client
```

## Stop the stack

```bat
scripts\windows\local-published-smoke\stop.bat
```

## Reset the smoke-test database

To delete the disposable smoke-test database volume and restart from clean published images:

```bat
scripts\windows\local-published-smoke\reset-db.bat
```

## Import sample data

Run this after the database and server are available:

```bat
scripts\windows\local-published-smoke\import-sample-data.bat
```

## Test a specific published image tag

```bat
set LEDGER_IMAGE_TAG=0.1.0-build-123
scripts\windows\local-published-smoke\start.bat
scripts\windows\local-published-smoke\smoke-test.bat
```

Replace `0.1.0-build-123` with the tag produced by Jenkins.

## Troubleshooting

If the wrong version appears to be running:

1. check `LEDGER_IMAGE_TAG`
2. pull the images again
3. restart the stack
4. check the client and server logs
5. confirm the browser is loading the expected URL

Useful commands:

```bat
set LEDGER_IMAGE_TAG=integration
scripts\windows\local-published-smoke\pull.bat
scripts\windows\local-published-smoke\stop.bat
scripts\windows\local-published-smoke\start.bat
scripts\windows\local-published-smoke\logs.bat
```

## Shared local PostgreSQL data

The Windows scripts load `config/environments/local-published-smoke.env` first and `config/environments/local.env` second. `local.env` therefore supplies machine-local overrides.

To use the same PostgreSQL data as the other local modes, copy `config/environments/local.env.example` to `config/environments/local.env` and set:

```text
LEDGER_DB_DATA_DIR=./data/database/common
```

The PostgreSQL service bind-mounts this directory at `/var/lib/postgresql`. Run only one of the three local modes at a time when they share this directory.

