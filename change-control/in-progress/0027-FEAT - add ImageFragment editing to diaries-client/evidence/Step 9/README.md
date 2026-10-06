# 0027 Step 9 evidence — type-neutral text/date/sequence editing and locking

Step 9 verifies that the existing Fragment editor and day-ordering lifecycle remain type-neutral for explicit IMAGE Fragments, and fixes one save/selection lock race exposed by that verification.

Evidence in this directory:

- `type-neutral-editing-and-locking.md` — implemented behaviour, regression matrix and the save/switch race fix.
- `static-contract-check.txt` — 26 client/responder source assertions covering ordinary update paths, lock cleanup, gate-disabled preservation, retained publication and mixed normalisation.
- `focused-model-validation.txt` — executable TypeScript check proving IMAGE text/date/sequence ordinary updates omit `imageId` on the wire while retaining local Image identity.
- `typescript-parse-check.txt` — TypeScript parser validation of all changed production/spec files.
- `angular-test-attempt.txt` — focused Angular/Karma invocation and environmental blocker (`ng: not found`).
- `responder-test-attempt.txt` — focused responder test invocation and environmental blocker (Gradle 9.6.1 is not cached and `services.gradle.org` is unreachable).
- `changed-files.txt` — Step 9 package inventory.
- `source-files.sha256` — hashes of the Step 9 changed production/test files and evidence inputs.

## Result

The Step 9 implementation is complete at source/regression level. IMAGE body and date editing use the same Fragment lock and ordinary `updateFragment` path as MARQUEE, so `imageId` remains omitted and therefore preserved. Mixed MARQUEE/IMAGE reorder continues to use one chronology and consumes responder-normalised retained Fragment state including authoritative versions and Image references.

Verification also identified and corrected an existing asynchronous save race: completion of a save for Fragment A can no longer clear, roll back or unlock newly selected Fragment B. Destruction or selection change while a body/date lock is still being acquired now releases any late lock instead of leaking it. A failed save explicitly cleans up the lock for the Fragment ID that initiated the request.

The responder source/tests already prove that `imageFragmentWritesEnabled=false` blocks Image-reference mutations while an ordinary IMAGE update with omitted `imageId` remains allowed, and that normalisation/publishing preserve the persisted Image relationship.

The Angular and Gradle suites could not execute in this sandbox because dependencies/distributions are not locally available. Those exact bootstrap failures are retained here and are not represented as passing test runs.
