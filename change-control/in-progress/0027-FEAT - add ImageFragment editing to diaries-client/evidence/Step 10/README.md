# 0027 Step 10 evidence — mixed navigation, day view and deletion

Step 10 completes the mixed MARQUEE/IMAGE reader and deletion behaviour without splitting the Fragment chronology.

Evidence in this directory:

- `mixed-navigation-dayview-deletion.md` — implemented presentation, navigation and delete semantics.
- `static-contract-check.txt` — 25 source assertions covering one chronology, authoritative navigation, Fragment-only deletion and responder reference guards.
- `typescript-parse-check.txt` — parser validation for all changed TypeScript production/spec files.
- `angular-test-attempt.txt` — Angular/Karma invocation and environmental blocker (`ng: not found`).
- `responder-test-attempt.txt` — focused responder test invocation and environmental blocker (Gradle 9.6.1 is not cached and `services.gradle.org` is unreachable).
- `changed-files.txt` — Step 10 package inventory.
- `source-files.sha256` — hashes for Step 10 changed source/test/documentation/evidence files.

## Result

The day reader now identifies MARQUEE versus IMAGE entries while keeping one `Fragment.sequence` list. IMAGE navigation is explicitly covered using the retained Fragment `pageId` and clears Marquee selection. IMAGE Fragment deletion is covered as a `deleteFragment`-only operation; the reusable Image catalogue row/file is not touched and the UI states that fact.

Image catalogue deletion remains a separate responder-guarded action. Existing responder integration coverage proves a referenced Image returns 409 and becomes deletable only after all Fragment references are cleared/deleted. The Files dialog now makes the referenced 409 reason explicit while retaining a separate missing-file conflict message.

The Angular and Gradle suites could not execute in this sandbox because required local dependencies/distributions are absent. Those exact bootstrap failures are retained here and are not represented as passing test runs.
