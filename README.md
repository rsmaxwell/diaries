# Diaries

Diaries is a personal diary/image annotation application consisting of an Angular editor, a Java responder/server, and a separate server-rendered read-only web projection.

The system is built around MQTT RPC and a retained MQTT topic tree. The client sends commands to the responder over MQTT, while the responder owns validation, persistence, locking rules, and publication of the resulting live object state. Persistent state is stored in PostgreSQL using JPA/Hibernate, and large image files are served separately by a static file server.

## Repository layout

```text
diaries/
  ARCHITECTURE.md
  README.md
  settings.gradle
  gradlew
  gradlew.bat
  versions.properties
  scripts/
  test/
  diaries-client/
  diaries-responder/
  diaries-web/
```

The three application child directories are:

| Project             | Purpose                                                                                       |
| ------------------- | --------------------------------------------------------------------------------------------- |
| `diaries-client`    | Angular/TypeScript browser application                                                        |
| `diaries-responder` | Java responder/server handling MQTT RPC, persistence, locking, and retained topic publication |
| `diaries-web`       | Java server-rendered, read-only projection of the canonical retained model                     |

`diaries-client` remains the sole interactive editor. `diaries-web` complements
it with ordinary GET/HEAD pages and cannot create or change diary content.
Both Java components are Gradle subprojects of this parent; the Angular client
is a Git submodule but is not a Gradle subproject.

## System overview

At a high level:

```text
Angular client
   |
   | MQTT RPC requests
   v
MQTT broker
   |
   | retained topic-tree updates
   v
Java diaries-responder
   |
   | JPA/Hibernate
   v
PostgreSQL database

Retained MQTT lookup topics
   |
   v
Java diaries-web
   |
   v
Read-only HTML pages

Static file server
   |
   v
Image and uploaded file content
```

The main architectural idea is:

```text
RPC requests express intent.
Retained MQTT topics publish reality.
The database is the durable source of truth.
```

The client should normally update its displayed state from live retained objects, rather than relying only on RPC replies.

## Main components

### diaries-client

The client is an Angular application. It is responsible for:

* user interaction and page layout
* displaying diaries, pages, fragments, marquees, and images
* signing in and maintaining access/refresh tokens
* sending MQTT RPC requests to the responder
* subscribing to retained live objects from the MQTT broker
* maintaining selected object and editing state
* reacting to topic-tree updates from the responder

More detailed client notes belong in `diaries-client/README.md`.

### diaries-responder

The responder is the authoritative server process. It is responsible for:

* authenticating and authorising MQTT RPC requests
* handling create, update, delete, lock, and unlock operations
* enforcing locking and idempotency rules
* managing JPA/Hibernate persistence
* publishing retained MQTT topic-tree state
* reconciling database and filesystem state on startup
* serving or coordinating static file/image metadata

More detailed responder notes belong in `diaries-responder/README.md`.

### diaries-web

The web projection subscribes only to canonical retained Diary, Page, Fragment
and Marquee lookup topics. It reconstructs relationships in memory and renders
accessible diary, day, scan and transcript pages. It has no MQTT publish/RPC,
database, JPA, NAS or mutation endpoint. The responder remains authoritative.

More detailed web notes belong in `diaries-web/README.md`.

### MQTT broker

The MQTT broker is used for two related purposes:

1. RPC transport between the client and responder.
2. Retained live-object publication from the responder to the client.

The responder should publish the resulting state after successful database changes, so clients can observe the latest state through subscriptions.

### PostgreSQL database

PostgreSQL stores the durable application state, including diaries, pages, fragments, marquees, and related metadata.

The database is the durable source of truth. The retained MQTT topic tree is a live distribution/cache layer derived from that state.

### Static file server

Large binary content, especially images, is served separately from MQTT. MQTT messages should contain references and metadata, not the image file contents themselves.

## Typical development workflow

Clone the top-level repository, including submodules if applicable:

```bash
git clone --recurse-submodules <repository-url>
cd diaries
```

If the repository has already been cloned without submodules:

```bash
git submodule update --init --recursive
```

Build or run the child projects from their own directories:

```bash
cd diaries-client
npm install
npm start
```

```bash
.\gradlew.bat :diaries-responder:build
.\gradlew.bat :diaries-web:build
```

## Design principles

* The responder is server-authoritative.
* The client presents and edits state but does not own persistence rules.
* Database updates should happen inside well-defined transactions.
* Retained MQTT messages should reflect committed state.
* Operations such as unlock and delete should be safe and idempotent where practical.
* Images and large files should be served by the static file server, not embedded in MQTT messages.
* Client and responder behaviour should be kept consistent, especially around locking, deletion, and retained topic updates.

## Related documentation

See also:

* `ARCHITECTURE.md` for a system-level architecture description.
* `diaries-client/README.md` for client-specific development notes.
* `diaries-responder/README.md` for responder-specific development notes.
* `diaries-web/README.md` for the read-only web projection.
