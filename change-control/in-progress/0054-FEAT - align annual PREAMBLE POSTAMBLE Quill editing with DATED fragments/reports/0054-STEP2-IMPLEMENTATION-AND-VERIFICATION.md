# 0054-FEAT — Step 2 integrated change package and verification plan

**Prepared:** 26 November 2026. **Status:** Implementation packaged; build/test gate NOT PASSED.

## Source of truth and provenance

Changes are based on `diaries-sources-20261126-190728.zip` (UTC 19:07:35).
At capture: parent `main` `f79c3f0a641103cfa2913dfbb784583650b300c1`
with `?? change-control/in-progress/`; Client `main` `cc826a8254b0e6d989755dc880d3023dae9e3416` clean;
Responder `main` `a49c6abd0ce005d58eb516770f6515313e40cdf6` clean;
Reader `main` `363ca8f425b811eeedff47486092b1f63c403ab0` clean.
These are metadata captured by the source bundle, **not** a freshly inspected Windows checkout.
Check Git again before applying the package. Preserve all pre-existing local changes.

## Contract and implementation

Step 1 contract A–F is accepted by the owner continuing to Step 2.

- Shared toolbar configuration, retaining the existing DATED inline-image picker and omitting image insertion for annual TEXT.
- Annual Quill creation and editing expose font, size, text and highlight colour alongside existing controls.
- Annual editor now has dedicated responsive styling and an explicit HTML 4096-character count.
- Existing TEXT editing captures the original server HTML; a no-op or equivalent Quill Delta unlocks without sending an update RPC.
  Existing relative image references remain untouched for no-op/cancel; a genuine edit passes the HTML through existing RPCs.
- Unchanged IMAGE link saves now check unlock success (previously ignored).
- A diary input change queues a refresh behind a busy operation, and releases an existing lock before replacing the subscription.
- If destruction occurs during lock acquisition, the acquired lock is released. If an in-flight save fails after navigation,
  its lock is released best-effort, with an alert on failure; no unlock races a successful in-flight save.
- Reader allowlists known Quill class tokens (including combinations), applies OWASP's safe CSS policy for editor colour styles,
  and defines Reader CSS for align/font/size classes. Existing script/URL protection remains.
- New Jasmine annual-editor unit tests and a Reader sanitizer regression test cover the critical workflows.
- No change to responder, schema, annual IMAGE catalogue linkage, deployment, or Playbooks.

## Verification completed in the analysis container

- PASS: TypeScript **syntax/transpilation-only** checks for annual editor TS, new annual editor Jasmine TS,
  shared toolbar TS, and DATED text-panel TS using installed TypeScript compiler.
- BLOCKED: Angular dependency install. `npm ci --offline --no-audit --no-fund` failed with `ENOTCACHED` for zone.js.
  An online npm attempt exited with `Exit handler never called!` (npm failure). Neither build nor Karma suite ran.
- BLOCKED: `./gradlew :diaries-web:test --offline --tests com.rsmaxwell.diaries.web.rendering.RenderingSafetyTest`
  could not download the Gradle distribution. No Java compile or JUnit tests were performed.
- NOT RUN: browser, MQTT integration, production deploy or acceptance smoke tests.

## Commands to run on the Windows 11 PC — Cygwin Bash terminal

First, review checkout state (the parent may have other untracked change-control files):

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
git status --short --branch
git submodule status
(cd diaries-client && git status --short --branch && git rev-parse HEAD)
(cd diaries-web && git status --short --branch && git rev-parse HEAD)
```

After applying this ZIP with Beyond Compare 4 and checking its diffs, run consolidated tests:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries/diaries-client
npm ci
npx ng test --watch=false --browsers=ChromeHeadless --include=src/app/diary/annual-editor/annual-editor.component.spec.ts
npm run build
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
./gradlew :diaries-web:test --tests 'com.rsmaxwell.diaries.web.rendering.RenderingSafetyTest'
```

Capture outputs under this feature's `reports/` or `evidence/` directory. A failed check must remain failed, not be interpreted as passed.
Then test PREAMBLE and POSTAMBLE create/edit/save/reload, unchanged/cancel, failure/retry, failed unlock,
year/diary switch, Reader colours/fonts/link safety, DATED text image picker, and annual IMAGE catalogue/ordering.
Do not deploy until test evidence and owner approval.

## Rollback

Before application, note the three checkout revisions and preserve any local edits. Roll back by restoring
only the files listed in this package from the recorded prior revisions, or reverse the reviewed changes
in Beyond Compare 4. No database changes are needed. Do not reset unrelated untracked work.
