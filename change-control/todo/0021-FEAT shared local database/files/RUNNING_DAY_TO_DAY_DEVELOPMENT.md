# Running Ledger for Day-to-Day Client and Server Development

Use this mode when you are actively coding and want fast feedback, hot reload, IDE debugging and lower-level tests.

In this mode, PostgreSQL runs in Docker, while the Java server and Angular client run directly from their submodule source trees:

```text
ledger-server  -> gradle bootRun
ledger-client  -> ng serve
database       -> PostgreSQL container
```

This workflow belongs mainly to the lower-level `ledger-server` and `ledger-client` projects. The top-level `ledger` project is primarily for whole-application Docker orchestration, published-image smoke testing and remote deployment.

## When to use this mode

Use this mode when you want to:

- debug server code in the IDE
- use Angular development server hot reload
- run focused Gradle or npm tests
- iterate quickly on client/server changes
- avoid rebuilding Docker images for every source change

Do not use this mode as the final whole-stack validation before publishing images or deploying remotely. For that, use local Docker build or published-image smoke testing.

## Typical service layout

```text
Browser
  |
  | http://localhost:4200
  v
Angular development server
  |
  | API requests
  v
Spring Boot server
  |
  v
PostgreSQL container
```

## Start from a clean checkout

From the top-level project:

```bash
git clone --recurse-submodules git@github.com:rsmaxwell/ledger.git
cd ledger
```

For an existing checkout:

```bash
git pull --recurse-submodules
git submodule update --init --recursive
```

## Start the database

The exact database-only workflow is owned by the server project. The top-level Docker scripts are intended for whole-application modes, so avoid starting the full local Docker stack if you intend to run the server and client directly.

Use the `ledger-server` documentation and scripts for the current local database setup.

## Run the server

Change into the server project and run the Spring Boot application:

```bash
cd ledger-server
gradle bootRun
```

The server owns:

- local Java/Spring development
- Gradle builds
- server-side tests
- server-local helper scripts
- Flyway migrations
- JPA/PostgreSQL integration

The server API normally listens on:

```text
http://localhost:8080
```

## Run the client

In a separate terminal, change into the client project and run the Angular development server:

```bash
cd ledger-client
npm install
ng serve
```

The client normally listens on:

```text
http://localhost:4200
```

Open the application in a browser at:

```text
http://localhost:4200
```

## Test the server

Focused server tests belong in the `ledger-server` project. For example:

```bat
ledger-server\scripts\windows\test-local.bat
```

You can also run Gradle tests directly from `ledger-server`.

## Test the client

Focused client tests belong in the `ledger-client` project and should be run using the client project's npm/Angular workflow.

## Notes

This mode is best for development speed. It does not prove that the final Docker images work. After making changes, validate the whole application using:

- `RUNNING_LOCAL_DOCKER_BUILD.md` for current source-tree images
- `RUNNING_LOCAL_PUBLISHED_SMOKE.md` for Jenkins/Docker Hub images

## Shared local PostgreSQL data

The local Windows scripts load two environment files, in this order:

1. `config/environments/development-infrastructure.env`
2. `config/environments/local.env`

`local.env` is machine-local and overrides the mode defaults. To share one PostgreSQL database with the other local modes, copy `config/environments/local.env.example` to `config/environments/local.env` and keep:

```text
LEDGER_DB_DATA_DIR=./data/database/common
```

The development-infrastructure PostgreSQL container bind-mounts that directory at `/var/lib/postgresql`. The Java server still connects through the published Windows host port (normally `localhost:5433`). Do not run more than one local mode at the same time when they share this data directory.

