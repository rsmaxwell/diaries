# 0027 Step 11 evidence — action state, accessibility and error handling

Step 11 completes the ImageFragment authoring UI-state pass without changing the responder contract, Fragment persistence model or retained topic shapes.

Evidence in this directory:

- `action-state-accessibility-error-handling.md` — implemented client behaviour and invariants.
- `static-contract-check.txt` — 32 source assertions covering derived action state, duplicate suppression, accessibility, keyboard/focus behaviour, status-specific errors and non-optimistic state.
- `authoring-error-executable-check.txt` — executable TypeScript check of 400/401/403/409/500 and timeout message mapping.
- `responder-contract-check.txt` — source/test inspection confirming the existing responder status contract consumed by the client.
- `typescript-parse-check.txt` — parser validation for the complete client TypeScript source tree.
- `angular-test-attempt.txt` — Angular/Karma invocation and environmental blocker (`ng: not found`).
- `npm-ci-offline-attempt.txt` — dependency bootstrap attempt showing the offline cache lacks `zone.js`.
- `changed-files.txt` — Step 11 package inventory.
- `source-files.sha256` — SHA-256 hashes for Step 11 package files.

## Result

ImageFragment actions now have one shared deterministic state model. Add, Select/replace and Clear cannot overlap or open duplicate workflows. The toolbar and Image-reference panel expose explicit disabled/busy states, labels and titles, and the chooser removes non-selectable catalogue entries from the tab order while supporting Space selection for valid entries. Dialogs request first-tabbable autofocus and focus restoration.

The authoring workflows now distinguish validation/stale state (400), authentication expiry (401), the ImageFragment deployment gate (403), conflicts/locks (409), and unconfirmed/internal failures (500/timeout). A 403 is therefore no longer conflated with a failed sign-in. Failed Image-reference mutations still never patch `imageId` optimistically; retained Fragment/Image topics remain the only committed UI truth.

No responder production code is changed by Step 11. The existing responder contract was inspected and recorded. Full Angular execution could not run in this sandbox because the supplied source has no installed Angular CLI/dependencies and the offline npm cache lacks `zone.js`; those exact failures are retained rather than represented as passing tests.
