# 0051 — Implementation steps and acceptance gates

**Steps 1–5 CLOSED.** Steps 1–3 were accepted on 20 November 2026. Step 4 production rollout and Step 5 permanent authoring-gate cleanup, documentation and handoff were accepted under the owner’s explicit approval of formal 0051 feature closure on **21 November 2026**. See [formal closure](evidence/Step%205/0051-FORMAL-CLOSURE-20261121.md).

Step 1 evidence and contract are indexed in [Step 1 evidence](evidence/Step%201/README.md).
Step 2 source changes, the first failed test-compilation run, corrected tests,
the 0025 same-session migration-runner correction and the final successful
integration receipt are indexed in [Step 2 evidence](evidence/Step%202/README.md).
Production schema, deployment and controlled extension-write activation were
subsequently verified on 20–21 November; see the Step 4 acceptance review and
production evidence register. 0028 production migration remains paused and is
not authorised by 0051 activation.

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

**CLOSED on 21 November 2026 under explicit owner approval of 0051 formal closure.** The original production rollout and owner functional checks passed; follow-on permanent gate retirement is recorded in Step 5.
The [Step 4 production acceptance review](evidence/Step%204/STEP4-PRODUCTION-ACCEPTANCE-REVIEW-20261121.md)
and [evidence register](evidence/Step%204/STEP4-PRODUCTION-EVIDENCE-REGISTER-20261121.md)
record the 0028 compatibility-tool changes, protected published-image rollback
rehearsal PASS, corrected Day Reader client build-79, deployed responder 85 and
web 9, healthy production services and backups, the 21 November enabled write
gate, and owner-confirmed production functional checks. The separate post-build-79
`local-docker-build` run was not evidenced; the review records this limitation.
The [original handoff](evidence/Step%204/STEP4-HANDOFF-20261120.md) remains
historical planning evidence and must not be treated as the current deployment status.

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

## Step 5 — Accept capability and hand off 0028

**CLOSED on 21 November 2026.** Durable documents and 0028/0029 handoff were
committed, responder build-86 was published and deployed with gate-free Playbooks,
Java regression and local/production acceptance passed, and final evidence was
committed in parent `bb9a1cb`. The owner expressly approved formal 0051 closure.
See the [Step 5 plan](evidence/Step%205/STEP5-ACCEPTANCE-AND-CLOSURE-PLAN-20261121.md)
and [0028/0029 handoff](evidence/Step%205/STEP5-0028-0029-HANDOFF-20261121.md).

- Record acceptance against every criterion, actual builds/revisions and
  deployment evidence. Update active architecture and component documentation.
- Confirm 0029's planned constraints allow valid IMAGE Marquees; no destructive
  cleanup or legacy-field removal occurs as part of this feature.
- Classify introduced tools as permanent operational, permanent regression or
  historical feature tooling; remove temporary deployed helpers at close-out.
- Record the explicit 0028 resumption handoff. Reconcile fresh DB/Files evidence
  before reusing prior reviewed decisions; resume its own rehearsal/apply gates.
- 0051 was marked complete only after the required evidence was accepted and the
  owner expressly approved formal closure on 21 November 2026. This does not
  authorise migration of legacy data under 0028.

**Gate:** accepted capability and traceable handoff. 0028 remains a distinct
migration with its own outstanding decisions and production approval.

## Formal completion record — 21 November 2026

- **Step 4: CLOSED** — initial compatible production activation and owner acceptance; see its original evidence register.
- **Step 5: CLOSED** — production responder `0.0.9-build-86`, gate-free responder JSON/Playbooks, all five containers healthy, local five-test GUI acceptance, owner production browser acceptance, Playbooks contract pass, and committed evidence.
- Parent implementation `94d2b91`, final acceptance evidence `bb9a1cb`; responder `4109c37`; Playbooks `417de08`; controller `8efacfa`.
- The old development flags were deliberately retired and are not a runtime rollback mechanism; older binaries are not safe for new-format IMAGE records.
- The separate 0028 migration and 0029 lifecycle work remain controlled by their own gates; 0052 stays TODO.

[Formal closure record](evidence/Step%205/0051-FORMAL-CLOSURE-20261121.md) and [production acceptance receipt](evidence/Step%205/STEP5-PRODUCTION-CLEANUP-ACCEPTANCE-20261121.md).
