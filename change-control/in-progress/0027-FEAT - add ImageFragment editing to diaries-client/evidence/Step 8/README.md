# 0027 Step 8 evidence — ImageFragment Image-reference editing

Step 8 implements attach/replace/clear editing for an existing IMAGE Fragment without changing responder production code.

Evidence in this directory:

- `image-reference-editing.md` — implemented workflow, lock boundary and retained-state authority.
- `static-contract-check.txt` — client/responder source assertions for every Step 8 contract boundary.
- `focused-model-validation.txt` — executable TypeScript model checks for IMAGE guard and preserve/set/clear wire semantics.
- `typescript-parse-check.txt` — parser validation of every changed TypeScript production/spec file.
- `angular-test-attempt.txt` — focused Angular/Karma invocation and environmental blocker (`ng: not found`).
- `changed-files.txt` — Step 8 package inventory.
- `source-files.sha256` — hashes of changed production/test files and Step 8 documentation/evidence inputs.

## Result

The implementation satisfies the Step 8 source-level acceptance criteria. Attach/replace and clear use the explicit Step 6 mutation API only after the existing Fragment lock is acquired and a newly retained locked Fragment has been observed. Successful updates do not send a redundant unlock; failed updates use the existing failed-edit unlock fallback. The UI remains retained-state-driven and permits repair of a missing/tombstoned Image reference.

The Angular tests are included but could not execute in this sandbox because the cumulative source bundle has no `node_modules` and therefore no local Angular CLI. This is an environment/bootstrap limitation, not reported as a passing test run.
