# Step 13 — Controlled cross-component development verification

## Status

**Completed locally (2026-09-30).** The controlled workstation run passed; its preserved `verified-run-20260930-192857/summary.json` records `PASSED`, no cleanup failures and no changes to live development/production databases or NAS content.

Step 13 adds a disposable cross-component verification runner. It does not change production
`diaries-web`, responder or client runtime source.

## Safety boundary

The runner is deliberately isolated from normal development and production state:

- the supplied backup is restored into a new PostgreSQL 18 tmpfs container;
- 0024/0025 schema application/assertion occurs only inside that restored database;
- Mosquitto, responder and web run in uniquely named owned containers/network;
- `/data/files` is native storage inside the owned responder container;
- synthetic Page scans are copied into the owned responder container;
- there is **no NAS mount** and no live development/production database connection;
- all fixture Images, Fragments, retained fault injection and physical-file failure are owned
  by the disposable run;
- cleanup removes only the containers/network created by that run.

The run modifies the restored fixture login solely to provide a known ADMIN credential for
supported responder RPC calls.

## Implementation

New validation entry points:

```text
scripts/windows/validation/verify-0026-step13.ps1
scripts/windows/validation/smoke-imagefragment-reader.cjs
```

The PowerShell wrapper:

1. requires Docker, Node, Python/Pillow, Playwright/MQTT client dependencies and Chrome/Edge (honouring an existing `CHROME_BIN` when supplied);
2. cleans responder/web build outputs, builds the exact current fat JARs and requires exactly one fresh JAR for each component;
3. invokes the Node runner with the supplied backup and a new evidence directory;
4. adds the candidate build log and regenerates evidence SHA-256 hashes;
5. requires `summary.json.status == PASSED` and no cleanup failures.

The Node runner verifies the following real path:

```text
restored PostgreSQL
    -> current responder JAR
    -> authenticated Mosquitto retained/RPC traffic
    -> current diaries-web JAR
    -> immutable projection / HTTP rendering
    -> loopback reverse proxy (/reader, /diaries-responder)
    -> real browser (desktop + mobile)
```

## Fixture coverage

The runner performs these checks in order:

1. starts responder with `imageFragmentWritesEnabled=false`;
2. creates a MARQUEE through `addFragment`, verifies browser rendering, and proves
   `addImageFragment` returns 403 while the gate is disabled;
3. enables the gate only in the fixture and restarts responder;
4. uploads nested-path catalogue Images through `uploadFile`;
5. creates IMAGE Fragments through `addImageFragment` covering:
   - Image selected;
   - no Image selected;
   - two Fragments sharing one Image, with real-browser rendering proved through both references;
   - strictly different Pages/dates (the run fails rather than weakening this coverage);
   - dedicated missing-file and missing-retained-metadata fault cases;
6. captures retained fixture payloads/hashes and verifies real HTTP bytes through the
   browser-visible `/diaries-responder` prefix;
7. exercises desktop/mobile month and source-page rendering, keyboard selection, deep links,
   and browser Back/Forward;
8. injects a fixture-only Image retained tombstone to prove `MISSING_METADATA` without
   changing the fixture database, then relies on responder restart to restore authoritative
   metadata;
9. moves only an owned fixture file aside inside the responder container and opens a fresh browser context to prove cache-independent browser `FILE_LOAD_FAILED`;
10. proves `deleteImage` returns 409 while the shared Image is referenced;
11. removes both fixture references through `deleteFragment`, then deletes the Image through
    `deleteImage` and verifies DB/file/retained cleanup;
12. restarts responder and web, verifies authoritative replay and unchanged surviving
    chronology, then records final database/retained evidence;
13. cleans up owned Docker resources in `finally`.

## Evidence produced by a successful run

The requested evidence directory contains, among other files:

- candidate responder/web JAR names and SHA-256 hashes;
- candidate build log;
- schema action record;
- selected baseline Page/date IDs;
- gate-disabled RPC response and MARQUEE screenshot;
- uploaded Image metadata and created fixture IDs;
- retained snapshots before faults, after delete and after restart;
- desktop/mobile month and source-page screenshots;
- shared-Image browser verification for both referring Fragments;
- missing-metadata and cache-independent missing-file screenshots/evidence;
- DeleteImage conflict/success responses;
- surviving chronology before/after restart;
- final fixture database rows;
- browser HTTP/network sample;
- selected responder/web/broker/database logs;
- explicit `cleanup.json`, `summary.json` and `SHA256SUMS.txt`.

## Verification command

See [verification-commands.md](verification-commands.md).

Verification completed successfully on 30 September 2026, see verified-run-20260930-192857.

