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

Retained Diary/Page/Fragment/Marquee/Image lookup topics
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
diaries/images/{imageId}
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
Diary, Page, Fragment, Marquee and Image lookup topics, rebuilds an in-memory model on
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

## Durable storage pairing and environment-neutral file identity

The durable application dataset has two mutable sides:

```text
PostgreSQL application rows
        +
selected mutable Files root
```

They must be selected as one pair. An execution-mode name is not sufficient to identify the dataset because local mode defaults can be overridden. The effective local selection is calculated by loading the mode environment and then `config/environments/local.env`; the second file wins.

Committed defaults keep the three local modes isolated, but the normal developer override may intentionally make all three use:

```text
./data/database/common
files-development-common
```

`DIARIES_DB_DATA_DIR` and `DIARIES_FILES_DIR` must therefore be overridden together. Switching only one side can associate catalogue rows with the wrong bytes and is rejected by the supported Windows tooling. Removing both common overrides returns each mode to its committed isolated database/Files pair.

`DIARIES_FILES_DIR` is intentionally only a validated leaf-directory selector. The physical path is resolved by the environment:

```text
Docker/local:   ${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR} -> /data/files
Direct Windows: <responder diaries.root>/<DIARIES_FILES_DIR>
Production:     ${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR} -> /data/files
```

Production obtains the leaf from the Ansible variable `diaries_files_dir`; it has no implicit role default and is rendered as `DIARIES_FILES_DIR`.

This storage selection does **not** alter application identity. The original diary-page scan tree remains `${DIARIES_NAS_CONTENT_PATH}/diaries` (shared/read-only in Docker/production), while mutable uploaded/catalogued content uses the selected Files root. The responder exposes mutable bytes under the stable `/files/...` HTTP namespace, and `Image.relativePath` remains relative to the selected Files root. Environment/mode names must never be persisted in that relative path simply because the physical root changes.

Retained MQTT state is not a third durable side of the dataset. It is broker/mode-specific live state that can be rebuilt from the matching database.

### Backup, restore and rollback consequence

A database dump is not a complete Diaries dataset backup. A recoverable backup consists of the database dump plus the **matching** mutable Files snapshot/copy and enough path/checksum identity to prove the pairing. Capture both while mutable responder writers are frozen.

For restore, first select and verify the target database/Files pair, keep the responder stopped, restore the matching Files snapshot and database dump, then reconcile before writes resume. A database-only restore may be valid for a deliberate operation, but it must be treated as potentially requiring Files reconciliation.

If two formerly shared datasets have changed independently, never roll them back by silently pointing both at one shared Files root. Keep the independent roots, restore matched pairs, and reconcile explicitly; destructive Image/File operations should remain disabled until the relationship is understood.

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


## Hybrid Fragment ownership — 0054 calendar-year model (supersedes 0029 annual ownership)

A Diary represents both the physical book and its digital edition. Physical Pages (including covers if represented as Pages) own **DATED** content. Editorial annual sections own Fragments at the **calendar-year** level: they do not need to be associated with a physical Page.

```text
Diary
├── Pages (physical book surfaces)
│   └── DATED Fragments, ordered within diary date: TEXT | IMAGE
│       └── optional Marquee (0..1) on the scanned Page
Calendar year (independent of physical Diary)
├── PREAMBLE Fragments, ordered: TEXT | IMAGE; no Page/Marquee/Diary
└── EPILOGUE Fragments, ordered: TEXT | IMAGE; no Page/Marquee/Diary
```

Every Fragment has exactly one **placement** (`PREAMBLE`, `DATED`, `EPILOGUE`) and one **type** (`TEXT`, `IMAGE`). `TEXT` covers transcription and editorial content; `IMAGE` references a reusable Catalogue Image. The old type `MARQUEE` is retired: a Marquee is a *separate, optional scanned-Page position*, never a content type.

**Exclusive ownership by placement:**

| Placement | Required owner | Page | Marquee | Rendering |
|---|---|---|---|---|
| `DATED` | An existing Page (which identifies its Diary) | Required | Optional 0..1 | Under its diary-date heading |
| `PREAMBLE` | Calendar year only | Must be absent | Must be absent | Before that year's first dated heading |
| `EPILOGUE` | Calendar year only | Must be absent | Must be absent | After that year's final dated entry |

`Fragment.year` identifies the annual owner irrespective of the physical Diary from which the editor was opened. `fragment.diary_id`, `page_id`, `month` and `day` are NULL for PREAMBLE/EPILOGUE; DATED ownership remains derived from its Page and physical Diary. The 0054 migration preserves original associations in feature evidence. The SQL migration and coordinated deployment are prerequisites for applying this contract to a running system.

All placements support TEXT and IMAGE. An IMAGE Fragment references a Catalogue Image; the catalogue owns independently optional **caption** and **alternative text**, while the occurrence owns its independently optional HTTP(S) **image-click link**. Caption and link may be present simultaneously. Page-specific commentary is a TEXT Fragment, not a per-occurrence caption. Marquees are permitted only for DATED Fragments and derive their Page via the Fragment; the redundant persisted `marquee.page_id` is to be removed. Preserve derived `Fragment.marqueeId` in retained contracts where needed.

The editorial reading order for each **calendar year** is PREAMBLE (by stable sequence/ID), then DATED (date order, then established Page/Fragment ordering), then EPILOGUE (stable sequence/ID), before the next year. PREAMBLE/EPILOGUE have no fabricated dates or date headings, and are not inserted into a Page's fragment list. Both editor and public reader must present them consistently; year-level editing must not require selecting an arbitrary Page.

**Approved existing-content classification:** production Fragments 1/2/3 → PREAMBLE of 1828, 387 → 1829, 806 → 1830, 1177 → 1831, 1563/1564 → 1832, 1926 → 1834, previously associated with the verified physical Diaries, before migration to year-only ownership. These are the nine known annual editorial Fragments. Preserve their content, order, useful links and historical HTML evidence; simplify decorative HTML for 1/2/3 only after review. Fragments 1738 (1832-06-27) and 2061 (1834-05-14) are **DATED** editorial TEXT, with candidate Pages 1005 (`img3018`) and 1078 (`img2706`) respectively, subject to guarded verification. The 49 additional development-only Page-less Fragments require separate 0028 provenance reconciliation; do not blindly migrate, delete or duplicate them. No current EPILOGUE records are known; test with synthetic data.

**Migration status:** this is the approved *target*, not the deployed contract. PostgreSQL and existing clients still have nullable Page/type, `MARQUEE` values and the redundant Marquee Page mapping. The new annual Diary owner, placement, JSON/MQTT contracts, schema constraints and editor/reader behaviour are pending coordinated implementation. No SQL mutation or deployment is authorised by this documentation.

**Change-control:** 0054 changes the earlier 0029 Diary-owned annual design. The name `POSTAMBLE` is a legacy database value converted to `EPILOGUE` by 0054; it is not an accepted ongoing placement. Calendar-first public Reader navigation is delivered separately by 0053.

## ImageFragment authoring architecture

MARQUEE and IMAGE Fragments share one durable `Fragment` chronology and the same locking/version/normalisation rules, but their media relationships are deliberately different:

```text
MARQUEE -> authoritative pageId + Marquee relationship; imageId absent/null
IMAGE   -> authoritative pageId + optional catalogue Image, optional same-Page Marquee,
           optional validated per-Fragment external image-click link
```

The reusable `Image` entity is catalogue metadata stored in PostgreSQL and published as retained `diaries/images/<id>` state. Its physical bytes live under the selected mutable Files root and are presented through the stable `/files/...` HTTP namespace. An `Image.relativePath` is relative to the selected Files root; it is not an absolute URL and does not encode an execution mode.

The Angular editor resolves IMAGE relationships from retained state:

```text
Fragment.imageId
   -> retained diaries/images/<id>
   -> CatalogueImage metadata
   -> runtime Files URL
   -> HTTP image bytes
```

This separates identity from presentation: the database Image ID is the relationship key; MQTT carries metadata/state; HTTP carries bytes.

### ImageFragment create/update contract

The responder remains authoritative for Page ownership, Fragment type, locking, optimistic version checks, Image existence and the authoring gate.

Creation uses the explicit `addImageFragment` RPC. Normal creation chooses one already-catalogued Image first and sends its positive ID. The responder creates `type=IMAGE`, initially without a Marquee, and participates in the same date/sequence normalisation as MARQUEE creation. Under 0051, a same-Page Marquee can subsequently be attached, edited or removed without changing the Image relationship or the independent optional link.

Updates use tri-state `imageId` semantics:

```text
imageId omitted   -> preserve the current Image reference
imageId=<id>      -> deliberately attach/replace the Image reference
imageId=null      -> deliberately clear the Image reference
```

Ordinary transcription/date/sequence edits and mixed-type reorder use the omit/preserve path. Only explicit Image-reference actions send the `imageId` key. This keeps normal editing usable when Image-reference authoring is disabled and prevents accidental relationship mutation.

### 0051 IMAGE extensions and reader presentation

`Fragment.imageLinkUrl` is optional and stored in nullable PostgreSQL `fragment.image_link_url` (`VARCHAR(4096)`). It is **per Fragment occurrence**, not a property of the shared `Image`. A valid HTTP(S) destination may include path, query and fragment. The responder validates link SET/CLEAR intent under locking, authorisation and optimistic versioning; omitted link fields preserve existing values on ordinary edits. Do not guess/derive destinations from filenames or fetch them during migration.

IMAGE fragments now support **zero or one same-Page Marquee**, with independent source-page selection/highlighting. Both client and public reader distinguish opening an image's external link from selecting its source page or moving/editing its Marquee. Removing a Marquee never deletes the Fragment, link, catalogue Image or file; deletion of a Fragment removes only its dependent Marquee/Fragment state and leaves the reusable Image intact.

The editor Day Reader shows `Image ID: N` **after Position**, then the full catalogue image **beneath the header**, followed by transcription text. Missing catalogue metadata results in an unavailable/no-Image presentation, not a fabricated URL. Legacy MARQUEE embedded-image HTML continues to render until separately reviewed 0028 migration. 0029 final constraint cleanup must not reinstate the obsolete IMAGE/no-Marquee invariant.

### Delete boundaries

`deleteFragment` is type-aware. Deleting an IMAGE Fragment deletes the Fragment and its retained Fragment aliases only. It never cascades into Image deletion. The reusable Image row, retained Image metadata and physical file remain until a separate catalogue deletion is requested. That Image deletion is reference-aware and is rejected while any Fragment still refers to the Image.

### Permanent IMAGE authoring and rollback compatibility

IMAGE creation, catalogue-image attachment/replacement/clearing, external HTTP(S) links,
and optional same-Page Marquees are supported permanent Editor operations. The two
rollout-only responder JSON properties (`imageFragmentWritesEnabled` and
`imageFragmentExtensionsWritesEnabled`) and their Ansible variables were removed
in the 0051 Step 5 cleanup. No deployment flag can disable IMAGE mutations; security
continues to depend on active Editor authorisation, valid locks and versions,
transactional consistency, reference checks, and link/Marquee validation.

Development configurations and production templates must **omit** the retired JSON
keys. A new responder does not accept these legacy keys; remove them from local
`%USERPROFILE%\.diaries\responder.json` and `responder.docker.json` before
running a cleaned-up responder. Production deployment must upgrade the Ansible
responder JSON template and the compatible rebuilt responder image **together**.

After 0051 extension records have been written, pre-0051 responder/reader versions
are not supported rollback targets. Disabling the obsolete feature switches is no
longer an available rollback. Use compatible application images and established
matched database/Files backup and recovery procedures as appropriate; no schema
columns or records are deleted during this cleanup.

0027 production verification used client `0.0.9-build-76`, responder `0.0.9-build-84` and reader `0.0.9-build-8`. The controlled lifecycle verified create, ordinary preserve edits, replace, clear, reattach, delete guard, restart/replay, reader/editor agreement and cleanup.

## Annual reading flow — hybrid Diary-year ownership (0029 approved target)

Annual editorial Fragments are **not** Page Fragments. See the authoritative [hybrid Fragment ownership model](#approved-hybrid-fragment-ownership-model--0029-target-2026-11-25-pending-implementation) above. The three placements determine both ownership and presentation: `DATED` belongs to a Page; `PREAMBLE` and `EPILOGUE` belong to a calendar year independently of physical Diaries and have no Page or Marquee. All types remain TEXT or IMAGE; image captions live in the catalogue. The feature's migration and acceptance details are recorded under `change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/`.

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
