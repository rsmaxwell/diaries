# 0008 - FEAT - four-mode build and deployment system

## Summary

Introduce a consistent four-mode build, run and deployment system for the Diaries application, following the successful pattern used by Ledger while preserving the architectural differences of Diaries.

The four supported modes will be:

1. development infrastructure;
2. local Docker build;
3. local published-image smoke test;
4. remote deployment.

Each mode will use a deliberately different Docker Compose stack and data set, but all modes must keep the Angular client, Java responder, PostgreSQL database, Mosquitto broker, retained MQTT topic state and static-file URLs mutually consistent.

## Background

Diaries consists of:

- the Angular/TypeScript `diaries-client`;
- the Java `diaries-responder`;
- PostgreSQL durable storage;
- Mosquitto MQTT transport and retained topic state;
- the responder static file server for diary images and uploaded files.

The current sources contain component build scripts, Dockerfiles, development scripts and existing Ansible material, but there is no single clearly documented and repeatable four-mode system equivalent to Ledger.

A consistent structure is required so that developers can distinguish between:

- running client and responder directly from source;
- testing locally built Docker images;
- testing the exact published production images;
- deploying those production images to a remote Linux machine.

## Required behaviour

The top-level Diaries project must provide four separate operating modes with unambiguous Compose files, scripts, configuration and documentation.

### Mode 1 — Development infrastructure

The Docker Desktop stack contains only:

- Mosquitto;
- PostgreSQL.

The application components run directly on the development machine:

- `diaries-client` runs through Angular development tooling;
- `diaries-responder` runs through Gradle, Java or the IDE.

The client and responder connect through host-published Mosquitto and PostgreSQL ports. The responder serves diary and uploaded files from a development-machine filesystem directory.

This mode is intended for fast day-to-day source development and debugging.

### Mode 2 — Local Docker build

The Docker Desktop stack contains:

- Mosquitto;
- PostgreSQL;
- a locally built `diaries-client` image;
- a locally built `diaries-responder` image.

The client and responder images are built from the current local source tree and run in Docker alongside their infrastructure dependencies.

This mode verifies:

- both Dockerfiles;
- local image construction;
- container configuration;
- Docker networking;
- health checks;
- complete-stack behaviour before image publication.

### Mode 3 — Local published-image smoke test

The Docker Desktop stack contains:

- Mosquitto;
- PostgreSQL;
- the production `diaries-client` image pulled from Docker Hub;
- the production `diaries-responder` image pulled from Docker Hub.

No application image may be built locally in this mode.

This mode verifies that the exact published images and requested image tag work together before remote deployment.

The smoke-test stack must use data and volumes separate from the day-to-day and local-build environments.

### Mode 4 — Remote deployment

The remote Linux stack contains:

- Mosquitto;
- PostgreSQL;
- the published production `diaries-client` image;
- the published production `diaries-responder` image.

Ansible playbooks install and configure the application on the target machine. The remote machine pulls versioned production images and does not build the Angular client or Java responder.

The deployment must provide persistent database, MQTT and diary-file storage, production secrets, startup and shutdown scripts, health checks, logs, backup and restore operations, smoke testing, update by image tag and rollback by image tag.

## Stack matrix

| Component | Development infrastructure | Local Docker build | Local published smoke | Remote deployment |
|---|---:|---:|---:|---:|
| PostgreSQL in Docker | Yes | Yes | Yes | Yes |
| Mosquitto in Docker | Yes | Yes | Yes | Yes |
| Client direct from source | Yes | No | No | No |
| Responder direct from source | Yes | No | No | No |
| Client locally built image | No | Yes | No | No |
| Responder locally built image | No | Yes | No | No |
| Client Docker Hub image | No | No | Yes | Yes |
| Responder Docker Hub image | No | No | Yes | Yes |
| Docker Desktop | Yes | Yes | Yes | No |
| Remote Linux host | No | No | No | Yes |
| Installed by Ansible | No | No | No | Yes |

## Design principles

### Component ownership

The lower-level projects continue to own their direct builds and component images.

`diaries-client` owns:

- Angular development startup;
- client tests;
- production client build;
- client Dockerfile;
- client image metadata;
- client-specific documentation.

`diaries-responder` owns:

- Gradle development startup;
- responder tests;
- responder distributable build;
- responder Dockerfile;
- responder image metadata;
- responder-specific documentation.

The top-level `diaries` project owns:

- shared Compose definitions;
- stack-level environment variables;
- coordinated image tags and versions;
- mode-specific scripts;
- full-stack health and smoke tests;
- production deployment integration;
- top-level operating documentation.

### One compatible client/responder release pair

The client and responder must normally use one coordinated Diaries release tag. This reduces the risk of deploying incompatible MQTT RPC operations, retained topic shapes, authentication behaviour or static-file URL conventions.

A separate override for client and responder tags may be retained for controlled compatibility or rollback testing, but the normal path must use one shared value such as:

```dotenv
DIARIES_IMAGE_TAG=integration
```

or:

```dotenv
DIARIES_IMAGE_TAG=0.1.0
```

### Separate data for every local mode

Development infrastructure, local Docker build and local published-image smoke test must not accidentally share PostgreSQL data, Mosquitto persistence or diary-file storage.

Each mode must use explicitly named volumes or host directories.

### Internal and browser-visible addresses

Container-to-container addresses differ from addresses used by the browser.

For example, inside Docker the responder may use:

```text
MQTT host: diaries-mqtt
Database host: diaries-db
```

The browser must use a host or reverse-proxy URL such as:

```text
ws://localhost:<port>/<path>
```

or:

```text
wss://<remote-host>/<path>
```

Docker service names must not be exposed in browser runtime configuration.

### Database and retained-state authority

The PostgreSQL database remains the durable source of truth. Retained MQTT topics are the live distributed state observed by the client.

Startup, health and smoke tests must account for responder database initialisation and retained-topic reconciliation. A responder container is not ready merely because its Java process has started.

## Proposed top-level structure

```text
diaries/
├── diaries-client/
├── diaries-responder/
├── compose.development.yaml
├── compose.yaml
├── compose.dockerhub.yaml
├── compose.production.yaml
├── .env.example
├── config/
│   ├── development/
│   ├── local-docker-build/
│   ├── local-published-smoke/
│   └── production/
├── scripts/
│   ├── windows/
│   │   ├── development-infrastructure/
│   │   ├── local-docker-build/
│   │   ├── local-published-smoke/
│   │   └── remote-deployment/
│   └── linux/
│       ├── start.sh
│       ├── stop.sh
│       ├── status.sh
│       ├── logs.sh
│       ├── smoke-test.sh
│       ├── backup.sh
│       ├── restore.sh
│       └── reset-data.sh
└── docs/
    ├── DEVELOPMENT_INFRASTRUCTURE.md
    ├── LOCAL_DOCKER_BUILD.md
    ├── LOCAL_PUBLISHED_SMOKE.md
    └── REMOTE_DEPLOYMENT.md
```

The final names may be adjusted to remain consistent with the established Ledger script layout.

## Scope

### Diaries client

- Confirm and document direct Angular development startup.
- Rationalise the existing client Dockerfile and image script.
- Build a production Angular image served by Nginx or the selected static web server.
- Load browser-visible MQTT and static-file settings from runtime configuration so that one published image can run locally and remotely.
- Expose client version and build information.
- Add a deterministic client health/version resource.
- Ensure Angular routes work when refreshed through the production web server.

### Diaries responder

- Confirm and document direct Gradle/Java development startup.
- Rationalise the existing responder Dockerfile, image script and deployment script.
- Externalise all environment-dependent responder configuration.
- Ensure the container runs with mounted configuration and diary-file storage.
- Add responder health and version information.
- Ensure readiness means PostgreSQL connection, MQTT connection, static-file initialisation and retained-state startup work are complete.
- Run the responder as a non-root container user where practical.

### PostgreSQL

- Define a health check.
- Use a separate database volume for each local mode.
- Use persistent host-mounted storage remotely.
- Define backup, restore and reset procedures.
- Keep credentials out of published images and committed production files.

### Mosquitto

- Configure MQTT TCP and MQTT over WebSockets.
- Define persistence, health checks, users and ACLs.
- Use separate broker persistence for each local mode.
- Use persistent storage remotely.
- Ensure browser clients receive only required topic permissions.
- Ensure the responder can publish retained application state and handle RPC request/reply topics.

### Static diary and uploaded files

- Use a development-machine directory in development-infrastructure mode.
- Use a separate volume or mounted directory in local Docker build mode.
- Use disposable or isolated storage in local published smoke mode.
- Use persistent host-mounted storage in remote deployment.
- Include these files in backup and restore operations.

### Deployment and operations

- Add four mode-specific Compose definitions.
- Add Windows scripts for the three Docker Desktop workflows and remote-controller calls.
- Add Linux operational scripts for the installed remote stack.
- Add or update Ansible roles and playbooks.
- Add coordinated version and image-tag handling.
- Add full-stack status, logs and smoke-test commands.
- Add update and rollback by image tag.

### Documentation

- Document the purpose and boundaries of each mode.
- Document startup, shutdown, status, logs, reset and smoke-test commands.
- Document expected URLs and ports.
- Document persistent and disposable data behaviour.
- Document versioning, image publication and remote deployment.
- Update the top-level README and architecture documentation where required.

## Implementation steps

### 1. Inventory and rationalise the existing build material

- [ ] Inventory all existing Diaries Dockerfiles, Compose fragments, image scripts, development scripts, responder deployment scripts and Ansible roles.
- [ ] Identify obsolete, duplicate or misleading scripts.
- [ ] Decide which existing files can be retained, moved, renamed or replaced.
- [ ] Record the current client and responder direct-development commands.
- [ ] Record all required ports, configuration files, credentials, volumes and filesystem paths.
- [ ] Confirm the current Docker Hub repository names for client and responder images.

### 2. Define common names and variables

- [ ] Define stable Compose service names for database, broker, responder and client.
- [ ] Define image repository names.
- [ ] Define the shared `DIARIES_IMAGE_TAG` variable.
- [ ] Define overridable client and responder image tags only if compatibility testing requires them.
- [ ] Define published host ports for each local mode.
- [ ] Define internal container ports.
- [ ] Define network names.
- [ ] Define mode-specific volume names or host directories.
- [ ] Define the production installation directory on the remote Linux host.
- [ ] Create a safe `.env.example` containing no production secrets.

### 3. Formalise direct client development

- [ ] Confirm `npm start` or the selected Angular command is the supported direct-development entry point.
- [ ] Confirm the development client connects to the host-published Mosquitto WebSocket listener.
- [ ] Confirm the development client uses the responder static-file server address reachable from the browser.
- [ ] Preserve useful MQTT development diagnostics.
- [ ] Document client tests and production build commands.
- [ ] Ensure direct-development configuration does not contain Docker service names.

### 4. Formalise direct responder development

- [ ] Confirm the supported Gradle, Java or IDE development startup command.
- [ ] Create or rationalise a safe example development configuration.
- [ ] Ignore the real credential-bearing development configuration.
- [ ] Configure the development responder to use host-published PostgreSQL and Mosquitto ports.
- [ ] Configure a development-machine diary/file root.
- [ ] Document responder build, test and run commands.
- [ ] Rationalise the existing development batch files without moving responder ownership to the top-level project.

### 5. Add development-infrastructure Compose mode

- [ ] Create `compose.development.yaml` at the top level.
- [ ] Include only PostgreSQL and Mosquitto services.
- [ ] Do not include client or responder services.
- [ ] Configure PostgreSQL credentials, database name, port and health check.
- [ ] Configure Mosquitto TCP and WebSocket listeners.
- [ ] Configure broker persistence, users, passwords and ACLs.
- [ ] Publish the required PostgreSQL, MQTT and WebSocket ports to the development machine.
- [ ] Create development-only database and broker volumes.
- [ ] Add Windows start, stop, status, logs and reset scripts.
- [ ] Verify the directly running responder and client can use the stack.
- [ ] Verify client MQTT RPC, retained-topic subscriptions and static-file access.

### 6. Rationalise the responder image

- [ ] Review the existing responder Dockerfile and `scripts/image.sh`.
- [ ] Use a repeatable multi-stage build where appropriate.
- [ ] Run responder tests before or during the image-build pipeline.
- [ ] Build the responder distributable artifact consistently.
- [ ] Copy only runtime material into the final image.
- [ ] Mount responder configuration rather than embedding production secrets.
- [ ] Mount diary and uploaded-file storage.
- [ ] Run as a non-root user where practical.
- [ ] Add image labels for version and source revision.
- [ ] Add responder health and readiness support.

### 7. Rationalise the client image

- [ ] Review the existing client Dockerfile and `scripts/image.sh`.
- [ ] Use `npm ci` and the lock file for repeatable builds.
- [ ] Run client tests before or during the image-build pipeline.
- [ ] Build the Angular production output.
- [ ] Serve it through Nginx or the selected production static web server.
- [ ] Add SPA route fallback support.
- [ ] Add runtime configuration for broker WebSocket and static-file URLs.
- [ ] Ensure one published image can be configured differently for local smoke and remote deployment.
- [ ] Add client version and source-revision metadata.
- [ ] Add a deterministic health/version resource.

### 8. Add local Docker build mode

- [ ] Create the top-level `compose.yaml` for the local source-build stack.
- [ ] Include PostgreSQL, Mosquitto, responder and client services.
- [ ] Add `build:` definitions for both application services.
- [ ] Build the responder from the current local responder source.
- [ ] Build the client from the current local client source.
- [ ] Configure internal container DNS names for responder-to-database and responder-to-broker connections.
- [ ] Configure browser-visible URLs separately.
- [ ] Add health checks to all services.
- [ ] Add health-based dependency ordering where supported.
- [ ] Create local-build-specific database, broker and file volumes.
- [ ] Add Windows build, start, stop, status, logs, reset and smoke-test scripts.
- [ ] Verify persistence across normal container recreation.
- [ ] Verify a clean reset removes only local-build data.

### 9. Add application-level local Docker smoke tests

- [ ] Verify all four containers are running and healthy.
- [ ] Verify the client web application is reachable.
- [ ] Verify the responder health/version endpoint.
- [ ] Verify PostgreSQL connectivity.
- [ ] Verify Mosquitto TCP connectivity.
- [ ] Verify Mosquitto WebSocket connectivity.
- [ ] Perform a minimal MQTT RPC request and validate its reply.
- [ ] Verify the expected retained-topic update.
- [ ] Verify a static diary or uploaded file can be retrieved.
- [ ] Capture client, responder, broker and database logs on failure.

### 10. Add coordinated image publication

- [ ] Define how the Diaries release version is supplied to both component builds.
- [ ] Record the top-level, client and responder commit revisions.
- [ ] Build and test both component images from the intended compatible revision set.
- [ ] Publish integration tags after successful combined verification.
- [ ] Publish immutable version tags for releases.
- [ ] Avoid using `latest` as the normal remote-deployment selector.
- [ ] Ensure client and responder image versions are visible at runtime.
- [ ] Ensure release or deployment jobs depend on successful combined client/responder verification.

### 11. Add local published-image smoke mode

- [ ] Create `compose.dockerhub.yaml`.
- [ ] Include PostgreSQL, Mosquitto, responder and client services.
- [ ] Do not include any application `build:` definitions.
- [ ] Pull client and responder production images from Docker Hub.
- [ ] Use `DIARIES_IMAGE_TAG` as the normal shared tag selector.
- [ ] Set an appropriate pull policy so stale local images are not silently reused.
- [ ] Create smoke-specific database, broker and file volumes.
- [ ] Add Windows pull, start, stop, status, logs, reset and smoke-test scripts.
- [ ] Verify both running image versions match the requested tag.
- [ ] Run the same application-level smoke tests used for the local Docker build.
- [ ] Ensure cleanup can remove the complete disposable smoke-test data set.

### 12. Define production networking and public URLs

- [ ] Decide whether the remote stack uses its own network or an infrastructure-owned external network.
- [ ] Define the browser URL for the Angular application.
- [ ] Define the secure MQTT WebSocket URL.
- [ ] Define the static diary/file URL.
- [ ] Configure the reverse proxy and WebSocket upgrade headers where required.
- [ ] Ensure HTTPS pages do not attempt insecure WebSocket or HTTP file access.
- [ ] Ensure internal Compose service names never appear in browser configuration.

### 13. Add production Compose mode

- [ ] Create `compose.production.yaml` or an Ansible-rendered equivalent.
- [ ] Include PostgreSQL, Mosquitto, responder and client services.
- [ ] Use published versioned images only.
- [ ] Do not build source on the target machine.
- [ ] Use persistent host-mounted database storage.
- [ ] Use persistent host-mounted Mosquitto storage.
- [ ] Use persistent host-mounted diary and uploaded-file storage.
- [ ] Mount rendered responder and broker configuration.
- [ ] Configure restart policies and health checks.
- [ ] Keep secret values out of committed files and image layers.

### 14. Implement Ansible remote deployment

- [ ] Review and rationalise the existing Diaries, Mosquitto and PostgreSQL Ansible material.
- [ ] Create or update a top-level Diaries deployment playbook.
- [ ] Create a coherent Diaries role or coordinated role set.
- [ ] Define defaults for paths, network names, ports, image repositories and image tags.
- [ ] Store production credentials and token secrets in Ansible Vault variables.
- [ ] Render `.env`, responder configuration, Mosquitto configuration, passwords and ACLs.
- [ ] Use `no_log: true` for secret-bearing tasks.
- [ ] Create target directories and apply appropriate ownership and permissions.
- [ ] Install Compose and operational scripts.
- [ ] Pull the requested production images.
- [ ] Start or update the stack.
- [ ] Wait for health checks.
- [ ] Run the remote smoke test.
- [ ] Report the deployed client and responder versions.

### 15. Add remote operating scripts

- [ ] Add Linux `start.sh`.
- [ ] Add Linux `stop.sh`.
- [ ] Add Linux `status.sh`.
- [ ] Add Linux `logs.sh`.
- [ ] Add Linux `smoke-test.sh`.
- [ ] Add Linux database and file backup scripts.
- [ ] Add Linux restore scripts.
- [ ] Add a guarded remote reset script if operationally required.
- [ ] Add Windows wrappers that invoke the Ansible controller or remote scripts consistently.
- [ ] Keep remote scripts independent of the development machine's local `.env` file.

### 16. Add backup and restore support

- [ ] Back up PostgreSQL using a logical database dump.
- [ ] Back up diary images and uploaded files.
- [ ] Record application image tags, component versions and backup timestamp in a manifest.
- [ ] Decide whether Mosquitto persistence is backed up or reconstructed from database state.
- [ ] Test restore into a clean environment.
- [ ] Verify restored database records.
- [ ] Verify restored files.
- [ ] Verify responder startup reconciliation.
- [ ] Verify retained-topic state and client display after restore.

### 17. Add update and rollback by image tag

- [ ] Deploy an initial version tag remotely.
- [ ] Create representative application data and files.
- [ ] Deploy a newer compatible version tag.
- [ ] Verify data and files remain intact.
- [ ] Run the remote smoke test.
- [ ] Roll back to the previous version tag.
- [ ] Verify data and files remain intact.
- [ ] Run the remote smoke test again.
- [ ] Document compatibility restrictions where database or MQTT schema changes prevent simple rollback.

### 18. Update documentation

- [ ] Add a top-level mode comparison table.
- [ ] Document development-infrastructure startup and direct client/responder commands.
- [ ] Document local Docker build commands.
- [ ] Document local published-image smoke commands.
- [ ] Document remote deployment and rollback commands.
- [ ] Document all ports and URLs.
- [ ] Document mode-specific volumes and reset behaviour.
- [ ] Document image versioning and publication.
- [ ] Document logs, health checks and failure diagnostics.
- [ ] Update `ARCHITECTURE.md` where the deployment topology is described.

### 19. Final four-mode validation

- [ ] Start development infrastructure and run client and responder directly.
- [ ] Complete a representative create/update/read workflow.
- [ ] Stop development infrastructure cleanly.
- [ ] Build and start the complete local Docker stack from source.
- [ ] Run the full local smoke test.
- [ ] Reset only the local-build data.
- [ ] Pull and start the published production images locally.
- [ ] Run the published-image smoke test.
- [ ] Confirm no local application image build occurred.
- [ ] Deploy the same image tag remotely using Ansible.
- [ ] Run the remote smoke test.
- [ ] Test restart, update, rollback, backup and restore.
- [ ] Record final commands, results and Git references.

## Acceptance criteria

- [ ] The four modes are clearly documented and have separate entry points.
- [ ] Development-infrastructure mode starts only PostgreSQL and Mosquitto in Docker.
- [ ] The client and responder run directly from source in development-infrastructure mode.
- [ ] Local Docker build mode builds and runs both application images from the current source tree.
- [ ] Local published-image smoke mode pulls both production application images from Docker Hub and contains no local application build definitions.
- [ ] Remote deployment uses Ansible to install and configure the complete stack on a remote Linux machine.
- [ ] The remote host pulls versioned production images and does not build application source.
- [ ] Each local mode uses separate database, broker and file data.
- [ ] Client runtime configuration uses browser-reachable MQTT WebSocket and static-file URLs.
- [ ] Responder configuration uses correct host addresses in direct-development and Docker modes.
- [ ] PostgreSQL, Mosquitto, responder and client have useful health or readiness checks.
- [ ] Smoke tests verify MQTT RPC replies and resulting retained-topic state.
- [ ] Client and responder versions and source revisions are visible.
- [ ] A shared image tag selects a compatible client/responder release pair by default.
- [ ] Production secrets are not committed or embedded in images.
- [ ] Persistent remote database and diary-file data survive container replacement, application update and rollback.
- [ ] Backup and restore have been tested end to end.
- [ ] Relevant client, responder, broker and deployment logs are retained or displayed when a smoke test fails.
- [ ] Existing useful component build and Ansible material has been rationalised rather than duplicated unnecessarily.

## Test evidence

### Development infrastructure

```text
Commands:
Result:
```

### Local Docker build

```text
Commands:
Requested version:
Client version:
Responder version:
Result:
```

### Local published-image smoke test

```text
Commands:
Requested image tag:
Pulled client image:
Pulled responder image:
Result:
```

### Remote deployment

```text
Target host:
Ansible command:
Requested image tag:
Deployed client version:
Deployed responder version:
Smoke-test result:
```

### Update and rollback

```text
Initial version:
Updated version:
Rollback version:
Data-persistence result:
File-persistence result:
Smoke-test result:
```

### Backup and restore

```text
Backup command:
Backup archive:
Restore command:
Database verification:
File verification:
Retained-state verification:
Result:
```

## Git references

### Top-level Diaries repository

- Branch:
- Commits:
- Pull request:

### Diaries client

- Branch:
- Commits:
- Pull request:

### Diaries responder

- Branch:
- Commits:
- Pull request:

### Ansible playbooks

- Branch:
- Commits:
- Pull request:

## Completion summary

Complete this section when the feature is finished.

Record:

- the final four-mode file layout;
- final Compose filenames;
- final image repository names and versioning rules;
- final local and remote URLs;
- final persistent-storage locations;
- test results for all four modes;
- update and rollback results;
- backup and restore results;
- known limitations or follow-on changes.
