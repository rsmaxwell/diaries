## Diaries Architecture

The Diaries application is an **Angular editor + MQTT RPC responder + retained
MQTT topic tree + PostgreSQL database + static file server + read-only web
projection** system.

At a high level:

```text
Angular client
   |
   | MQTT RPC requests
   v
MQTT broker  <--------------------------+
   |                                     |
   | retained topic-tree updates          |
   v                                     |
Java diaries-responder                  |
   |                                     |
   | JPA/Hibernate                       |
   v                                     |
PostgreSQL database                     |
                                         |
Static image/file server ---------------+

Retained Diary/Page/Fragment/Marquee lookup topics
   |
   v
Java diaries-web
   |
   | server-rendered GET/HEAD only
   v
Public reader browser
```

## Main components

### 1. `diaries-client`

The Angular/TypeScript client is responsible for the user interface.

It displays diaries, fragments, marquees, images, selection state, editing state, and so on. It communicates with the responder through MQTT, rather than direct HTTP API calls.

Key client-side responsibilities:

* sign in and maintain access/refresh tokens
* subscribe to retained live objects in the MQTT topic tree
* send MQTT RPC requests such as create, update, delete, lock, unlock
* maintain selected diary/page/fragment/marquee state
* update the UI reactively from MQTT topic updates
* serve/display image URLs from the static file server

The client should generally treat the retained MQTT topic tree as the live model of the application.

---

### 2. MQTT broker

The broker has two roles:

#### RPC transport

The client sends request messages to the responder over MQTT. The request includes things like:

* operation name
* arguments
* access token in user properties
* response topic
* correlation data

The responder replies on the requested reply topic, using the correlation data so the client can match replies to requests.

#### Retained topic tree

The responder publishes application state as retained MQTT messages, for example:

```text
diaries
diaries/{diaryId}
diaries/pages/{pageId}
diaries/fragments/{fragmentId}
diaries/marquees/{marqueeId}
```

The exact topic names may differ slightly in the current code, but architecturally the idea is:

```text
database state -> responder -> retained MQTT objects -> client live model
```

This is important: the client should not have to infer long-term state only from RPC replies. RPC replies say whether the operation succeeded; retained messages carry the latest object state.

---

### 3. `diaries-responder`

The Java responder is the authoritative server process.

Its responsibilities are:

* authenticate and authorise MQTT RPC requests
* perform database transactions
* enforce locking rules
* update fragments/marquees/diaries/pages
* publish updated retained topic-tree objects
* reconcile database state with filesystem/image state on startup
* serve or coordinate static image metadata
* return RPC replies to the client

For consistency, the responder should be the single place where rules are enforced. For example:

* whether a user may update a fragment
* whether a fragment is locked
* whether an unlock request is idempotent
* whether deleting a marquee also touches a fragment
* whether startup normalisation republishes retained messages

The client may prevent obvious invalid actions, but the responder must still enforce correctness.

---

### 4. `diaries-web`

`diaries-web` is a sibling Java process and read-only projection. It does not
replace `diaries-client`. It subscribes to the responder's canonical retained
Diary, Page, Fragment and Marquee lookup topics, rebuilds an in-memory model on
startup/reconnect, and atomically serves immutable generations as HTML.

It has no database connection, JPA model, MQTT publish/RPC path, authentication
editor flow, file mutation or content-changing HTTP route. Scans continue to be
served by the existing responder/static route. Editors continue to use
`diaries-client`; only `diaries-responder` changes durable/canonical state.

---

### 5. PostgreSQL / JPA model

PostgreSQL stores the persistent application model.

Likely entities include:

```text
Diary
Page
Fragment
Marquee
User / role / lock info
```

The important architectural point is that the database is the durable source of truth, while the MQTT retained topic tree is the live distribution/cache layer.

So the data flow should be:

```text
RPC request
   -> validate
   -> transaction
   -> update database
   -> commit
   -> publish retained MQTT state
   -> RPC success reply
```

For failure cases, ideally:

```text
RPC request
   -> validate
   -> transaction fails / validation fails
   -> rollback
   -> RPC error reply
   -> no retained state change
```

---

### 6. Static file server

Images are not stored directly in MQTT.

The architecture is more likely:

```text
image file on filesystem
   -> served by static file server
   -> client displays URL
```

Fragments or marquees may reference images by URL/path/id, but the actual binary image data should remain outside MQTT.

This keeps MQTT messages small and makes image display/cache behaviour simpler.

---

## Typical operation flow

### Create fragment + marquee

```text
Client
  sends createFragment/createMarquee RPC
        |
        v
Responder
  checks token/role
  starts DB transaction
  creates Fragment
  creates associated Marquee
  commits
  publishes retained Fragment object
  publishes retained Marquee object
  replies success
        |
        v
Client
  receives RPC success
  also receives retained topic updates
  UI updates from live object streams
```

The cleanest design is that the RPC reply may include the new IDs or full objects, but the client’s long-term displayed state should come from retained/live subscriptions.

---

### Update fragment text

```text
Client locks fragment
  -> responder records lock

Client edits locally

Client sends updateFragment RPC
  -> responder checks caller owns lock
  -> updates DB
  -> preserves/updates lock state according to intended rule
  -> publishes retained fragment
  -> replies success

Client unlocks or responder unlocks as part of save policy
```

The important design choice is whether update should automatically release the lock or whether unlock is a separate explicit operation. Whichever rule you choose, both client and responder should agree.

---

### Delete fragment

```text
Client requests delete
        |
        v
Responder
  checks authorisation
  checks lock ownership/rules
  deletes dependent marquee(s) if needed
  deletes fragment
  publishes retained delete/tombstone or clears retained topic
  replies success
        |
        v
Client
  removes object from UI when retained state disappears/changes
```

This is one of the areas where the client and responder must be especially consistent. If the responder deletes an object, later unlock calls for that object should probably be **idempotent**:

```text
unlock missing fragment -> 200 OK or 404-style benign response, not 500
```

The key point is that “already gone” is not a server error.

---

## Retained topic-tree principle

A good rule for the Diaries architecture is:

> RPC changes intent; retained topics show reality.

So:

* the client sends commands using RPC
* the responder validates and mutates durable state
* the responder republishes the resulting live state
* the client updates from subscriptions

This avoids the client having to guess too much after operations like delete, rollback, lock expiry, or startup reconciliation.

---

## Startup reconciliation

On responder startup, it compares filesystem/database/topic-tree state and republishes or normalises objects.

The intended architecture should be:

```text
filesystem + database
   -> responder reconciliation
   -> missing DB rows added if needed
   -> obsolete/inconsistent rows fixed if needed
   -> retained MQTT state republished only when useful
```

There will be a significant amount of work on restart, resulting in no new entries when the responder is reconciling correctly. Updates will occur when the database and the topic tree differ.

---

## Locking architecture

For fragments and marquees, the clean model is:

```text
lock owner
lock timestamp
lock type / object type
```

Then operations can follow this pattern:

```text
update object:
  allowed if unlocked or locked by caller

delete object:
  allowed if unlocked or locked by caller

unlock object:
  allowed if locked by caller, admin, expired, or object missing
```

## Suggested architecture boundary

A useful split is:

```text
Client:
  presentation
  local interaction state
  selected object state
  optimistic UI only where safe
  subscriptions to live MQTT objects

Web projection:
  subscription-only retained model consumer
  immutable in-memory generations
  sanitized server-rendered GET/HEAD pages
  no editing or persistence

Responder:
  validation
  authorisation
  locking
  transactions
  retained topic publication
  idempotency
  database/filesystem reconciliation

MQTT broker:
  transport
  retained live object cache

PostgreSQL:
  durable source of truth

Static file server:
  image/file bytes
```

## One-sentence summary

Diaries is best viewed as a **server-authoritative, MQTT-distributed application**: the Angular client sends commands, the Java responder owns validation and persistence, PostgreSQL stores durable state, retained MQTT topics distribute live objects, and the static file server serves large image content.
