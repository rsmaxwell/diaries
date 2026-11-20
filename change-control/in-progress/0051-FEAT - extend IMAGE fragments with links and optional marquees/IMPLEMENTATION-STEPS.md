# 0051 — Implementation steps and acceptance gates

**Steps 1, 2 and 3 CLOSED by explicit owner approval on 20 November 2026. Step 4 migration handoff and compatible rollout OPEN; Step 5 final acceptance OPEN.**

Step 1 evidence and contract are indexed in [Step 1 evidence](evidence/Step%201/README.md).
Step 2 source changes, the first failed test-compilation run, corrected tests,
the 0025 same-session migration-runner correction and the final successful
integration receipt are indexed in [Step 2 evidence](evidence/Step%202/README.md).
No production database or service changes have been performed. Compatible
rollout, production verification and 0028 handoff remain in Steps 4–5; 0028
continues paused.

## Step 1 — Freeze the baseline and finalise the contract

Deployed service identities, existing IMAGE authoring gate and real DB constraints
were verified read-only on 20 November. The Cygwin static source baseline
passed 12/12 checks; targeted responder/web Gradle tests passed and the
Angular Chrome Headless selection passed 39/39. These establish a
**current-code regression baseline**, not 0051 new-feature integration.
The owner accepted the cross-component contract and the coverage boundary
on 20 November 2026. **Step 1 CLOSED; prior baseline evidence remains unchanged.**

- Record parent/submodule revisions, dirty state and actual deployed versions.
- Audit all IMAGE/no-Marquee assumptions across database constraints, native
  queries, entities/DTOs, handlers, locking, deletion, retained publication,
  client projection/authoring and web rendering.
- Freeze existing behaviour using synthetic linked/unlinked and
  Marquee-present/absent examples. Confirm the existing Day reader Image label.
- Finalise URL field/schema names, size, validation and omitted/set/clear
  semantics, plus IMAGE Marquee attach/edit/remove and same-Page rules.
- Define safe deployment activation, old-writer compatibility and rollback
  boundaries before new combinations become writable.

**Gate:** reviewed cross-component contract, data-preservation decisions and
test matrix. No legacy production mutation. Keep 0028 paused.

## Step 2 — Implement persistence, responder and retained contracts

**CLOSED by explicit owner acceptance on 20 November 2026.** See the
[Step 2 acceptance review](evidence/Step%202/STEP2-ACCEPTANCE-REVIEW-20261120.md).
The owner's final responder Gradle test task passed (`BUILD SUCCESSFUL`),
and disposable PostgreSQL/MQTT run `c1759df22f5f` passed 2/2 JUnit tests
with checked SHA-256 evidence. Historical failed runs were retained.
The migration was exercised twice on a disposable fixture, with no changes
to existing data hashes. The production schema has not been migrated.
The [Step 2 closure receipt](evidence/Step%202/STEP2-CLOSURE-20261120.md)
records the owner's acceptance without replacing the original review or historical failures.

- Add repeatable nullable URL schema support and all entity/DTO/native-query
  mappings; preserve existing data and legacy compatibility windows.
- Implement validated URL writes and optional IMAGE Marquees through existing
  permissions, lock and optimistic-version paths. Ensure normal edits cannot
  clear fields merely because old request payloads omit them.
- Reconcile relationship validation and deletion: preserve geometry/identity,
  reject cross-Page/duplicate association, and delete only intended dependants.
- Publish committed Fragment/Marquee state, correct removal tombstones and
  restart replay. Preserve shared Image records and file bytes.
- Exercise rollback on mutation failure, stale versions, concurrent edits,
  null/omitted fields, unsafe URLs and representative encoded map destinations.

**Gate:** responder tests/build and database/RPC/retained integration checks
pass with exact outputs. Schema upgrade and rollback limits are documented.

## Step 3 — Implement editor, reader and Day reader identity

**CLOSED by explicit owner approval on 20 November 2026.** The [Step 3 acceptance review](evidence/Step%203/STEP3-ACCEPTANCE-REVIEW-20261120.md) records passing Angular/web tests, the disposable public-reader run `20261120T140504Z-fe13662e`, and the signed-in editor run `20261120T150113Z-d8ec629c`, including six visually reviewed screenshots. The 390px diary heading is visually clipped but navigation and controls remained visible; this is recorded as a non-blocking presentation observation, not a verified pre-existing defect. The [closure receipt](evidence/Step%203/STEP3-CLOSURE-20261120.md) records owner acceptance. No production deployment or migration is implied.

- Extend client models/projections and link controls; remove obsolete
  IMAGE/no-Marquee rejections only where the new contract supports them.
- Extend source selection/geometry authoring and linked-media rendering while
  separating link activation from fragment selection and drag/reorder.
- Update web parsing/projection and both source-page and month templates with
  safe clickable media and independent source-highlight controls.
- Show `Image ID: N` immediately after Position in the editor Day reader,
  preserving null-reference and metadata-pending states.
- Test both UIs with all four link/Marquee combinations, keyboard navigation,
  responsive layouts, missing media, ordinary MARQUEE and legacy HTML cases.

**Gate:** relevant client/web suites and production builds pass; capture
cross-component local smoke and visual evidence rather than unit tests alone.

## Step 4 — Update migration handoff and rehearse compatible rollout

**Publication workflow agreed (20 November 2026):** Jenkins on `pluto` publishes the intended pinned parent/submodule revisions. Windows checks the selected published images against the existing `local-published-smoke` Compose configuration and runs the rollback rehearsal with isolated synthetic Files and the frozen database fixture, never its writable NAS mount. See [Jenkins published-image verification plan](evidence/Step%204/STEP4-JENKINS-PUBLISHED-SMOKE-PLAN-20261120.md). No production deployment, migration or gate activation has occurred.

**OPEN — offline migration compatibility implementation prepared; rollout rehearsal and
production checks remain outstanding.** [Step 4 source review](evidence/Step%204/STEP4-MIGRATION-COMPATIBILITY-IMPLEMENTATION-20261120.md).
The [disposable three-image rehearsal](evidence/Step%204/STEP4-DISPOSABLE-ROLLOUT-REHEARSAL-20261120.md) is prepared; Docker execution and recorded acceptance are pending.
Follow the [Step 4 handoff and preconditions](evidence/Step%204/STEP4-HANDOFF-20261120.md). This is the next substantial implementation stage, not an accepted or deployed step.

- Amend 0028's design, manifest schema, review portal/checker and tests for
  explicit URL and Marquee preservation. Preserve original review evidence;
  version any transformed draft and report differences without auto-signoff.
- Verify synthetic migration extraction retains exact destinations and
  Marquee IDs/geometry. Keep production legacy conversion out of 0051.
- Rehearse schema and coordinated component rollout in an isolated environment
  using the supported backup process; exercise restart/replay and rollback.
- Verify local-docker-build and local-published-smoke behaviour with actual
  image/build identities before controlled production activation.
- Deploy compatible capability under the agreed gate, verify production
  behaviour and document when older binaries cease to be safe rollback targets.

**Gate:** supported behaviour exists in production and migration tools model
it accurately. Passing a draft checker alone does not satisfy this gate.

## Step 5 — Accept capability and resume 0028

- Record acceptance against every criterion, actual builds/revisions and
  deployment evidence. Update active architecture and component documentation.
- Confirm 0029's planned constraints allow valid IMAGE Marquees; no destructive
  cleanup or legacy-field removal occurs as part of this feature.
- Classify introduced tools as permanent operational, permanent regression or
  historical feature tooling; remove temporary deployed helpers at close-out.
- Record the explicit 0028 resumption handoff. Reconcile fresh DB/Files evidence
  before reusing prior reviewed decisions; resume its own rehearsal/apply gates.
- Do not mark 0051 complete, migrate legacy data, commit or push solely because
  this planning document lists those later steps.

**Gate:** accepted capability and traceable handoff. 0028 remains a distinct
migration with its own outstanding decisions and production approval.
