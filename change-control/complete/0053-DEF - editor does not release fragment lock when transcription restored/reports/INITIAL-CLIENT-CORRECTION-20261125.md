# 0053-DEF — Initial client correction and evidence, 25 November 2026

**Status:** Candidate implementation for local review; not built, deployed or accepted.

## New observations from GUI

Normal-speed typing, restoring transcription to its visible original value and waiting for broker propagation left the lock held. The first editor's Save button appears still active in the provided screenshot (`Fragment 85`, diary 1, page 692). The other window showed `Locked` rather than `Locked by another window`. The screenshot cannot itself establish the underlying HTML or session values.

This makes the prior interpretation as primarily a fast RPC race too narrow. In the 24 November client source `hasEdits` compares HTML strings directly, so Quill's harmless markup normalisation can keep a transcription artificially dirty. The original unlock only detects a `true`→`false` edge, so it cannot release while dirty remains true. The second-window button is based on matching both user ID and server-issued session ID; duplicated tabs may inherit those through `sessionStorage`.

## Candidate implementation

- Compare Quill canonical rich-text Delta operations when raw HTML differs, preserving meaningful text, style and embedding changes. Use the same semantic equality to avoid rewriting unchanged source text during date-only Saves.
- Replace a single dirty-state edge observer with ongoing lock-state reconciliation; sequence each Fragment's lock/unlock RPC and prevent Save during a transition. Preserve fragment ID across late responses and navigation.
- When a duplicate tab is detected using a same-origin `BroadcastChannel`, force the copied tab through a fresh sign-in to obtain a distinct server-issued lock session ID; do not merely fabricate a new client ID that the responder will not recognise.
- Add Jasmine tests for normal-speed undo with equivalent Quill HTML, late lock reply, re-edit during unlock, and same-user different-session labelling.

## Evidence and limitations

- Source input: `diaries-sources-20261124-090430.zip`. This source archive contains no `.git` metadata; the live Windows branch, submodule pins and uncommitted working changes could not be verified here.
- Static TypeScript parsing of the three changed TypeScript files: PASS (using installed global TypeScript parser).
- Local `npm ci --no-audit --no-fund`: **FAIL** (`npm error Exit handler never called!`); see `evidence/local-tool-checks/npm-ci.log`. Therefore neither the Angular test suite nor a production build is claimed as passed.
- No running editor/responder/MQTT/DB environment was available from this container, so the two-window UI, DB version, retained topic and logs remain **NOT VERIFIED**.
- No production files, databases, deployments, or snapshot datasets changed.

## Consolidated acceptance on Windows development environment

1. Before applying either ZIP, compare paths in Beyond Compare and check the parent and client Git statuses. Preserve locally newer edits.
2. In Windows **Cygwin** at the Diaries parent root, verify: `git status --short --branch; git submodule status; git -C diaries-client status --short --branch`.
3. From Windows **Cygwin** in `diaries-client`: `npm ci`; `npm test -- --watch=false --browsers=ChromeHeadless`; `npm run build`. Record exit codes and full logs under this feature's `evidence/`.
4. In two **independently signed-in** development editor windows, check ordinary edit/undo and manually deleting a character: Save deactivates and unlock publishes automatically. Verify lock visibility on the other window and no database version change.
5. Repeat with a **duplicated tab**: the copy must require a fresh sign-in (different server-issued session) and subsequently show `Locked by another window` while the first is editing.
6. Re-edit during unlock, switch Fragments while a lock request is pending, open/close date picker without changes, change date, Save, and check IMAGE as well as MARQUEE Fragments. Verify MQTT retained state and responder logs; do not disturb production or previously reviewed 0028 migration data.
7. Only after accepted tests update this report with exact Git revisions, evidence receipts and deployment/rollback results. Leave 0053 under `in-progress` pending formal closure.
