# 0051-FEAT - Extend IMAGE fragments with links and optional Marquees

## Type

Feature

## Status

**In progress — Steps 1, 2 and 3 CLOSED by explicit owner approval; Steps 4–5 OPEN.**

The [Step 1 evidence](evidence/Step%201/README.md) contains the approved
cross-component contract and pre-change regression baseline. The responder
Step 2 implementation has been applied and tested on the owner's Windows
working copy. The full responder Gradle test task completed successfully on
20 November 2026 after correction of two test-source compilation errors and
one stale legacy-invariant assertion. The disposable PostgreSQL/MQTT integration
run `c1759df22f5f` reported PASSED, with two JUnit integration tests, no
failures/errors/skips, idempotent schema migration and preserved existing
values. The owner independently checked its `result.json`, JUnit summary and
SHA-256 manifest. See the [Step 2 acceptance review](evidence/Step%202/STEP2-ACCEPTANCE-REVIEW-20261120.md).

**Step 2 CLOSED** by explicit owner approval on 20 November 2026, following the verified responder regression and isolated PostgreSQL/MQTT run. See the [Step 2 closure record](evidence/Step%202/STEP2-CLOSURE-20261120.md).
Step 3 implementation and its local verification have run in the owner's Windows working copy. The Angular production build, 240/240 Chrome Headless tests, corrected targeted web-reader HTTP tests, integrated public-reader smoke `20261120T140504Z-fe13662e`, and signed-in Angular editor acceptance run `20261120T150113Z-d8ec629c` all passed. The six editor screenshots and JSON receipts were reviewed on 20 November; the [Step 3 acceptance review](evidence/Step%203/STEP3-ACCEPTANCE-REVIEW-20261120.md) records scope, limitations and a non-blocking mobile heading observation. Step 3 was formally CLOSED by explicit owner approval on 20 November 2026; see the [Step 3 closure receipt](evidence/Step%203/STEP3-CLOSURE-20261120.md) and [Step 3 evidence](evidence/Step%203/README.md).
This is local and isolated verification only. No production migration,
deployment, feature-gate activation or 0028 conversion has occurred.
Step 4 now has an [offline migration compatibility review](evidence/Step%204/STEP4-MIGRATION-COMPATIBILITY-IMPLEMENTATION-20261120.md)
from the refreshed 15:28 source bundle. It does not close Step 4 or authorise
0028 conversion or live deployment. The separate 0051 extension-write gate
must remain disabled during coordinated rollout.
The [disposable Step 4 rollout/rollback rehearsal](evidence/Step%204/STEP4-DISPOSABLE-ROLLOUT-REHEARSAL-20261120.md) is prepared for Windows PowerShell 7 but has **not been run**. It uses uniquely tagged local images and checks historic production image IDs; it does not deploy or change any production state.
The Step 4 rollout workflow now uses the existing **Jenkins/Docker Hub published images** and the Windows `local-published-smoke` image selection, with disposable test data for mutating rollback checks. See the [Jenkins-published image rehearsal plan](evidence/Step%204/STEP4-JENKINS-PUBLISHED-SMOKE-PLAN-20261120.md). The replacement local-build rehearsal is retired; no Jenkins publication or production rollout has yet occurred.

The [Step 4 handoff](evidence/Step%204/STEP4-HANDOFF-20261120.md) sets out the next
implementation and deployment-rehearsal boundaries without modifying 0028 drafts. The
[implementation plan](IMPLEMENTATION-STEPS.md) remains authoritative for the
remaining migration-handoff, compatible-rollout and final acceptance gates in Steps 4–5.

## Priority

High — prerequisite for resuming
[0028 legacy image migration](../../in-progress/0028-FEAT%20-%20migrate%20reviewed%20legacy%20embedded-image%20fragments/README.md).

## Opened

2026-11-20

## Summary

Extend the existing IMAGE Fragment to support an optional clickable-image URL
and an optional source-page Marquee. In the editor's **Day reader** tab, display
the referenced **Image ID immediately after Position** in the fragment header.
No new Fragment type is required.

This allows 0028 to preserve both an image's external click destination and its
existing source-page highlight when converting approved legacy HTML fragments.
It does not itself authorise or execute the legacy conversion.

## Background and observed behaviour

- The frozen 0028 evidence identifies 30 candidate fragments with an anchor
  wrapping an image. Each has one destination: 29 HTTPS and one HTTP. None has
  an explicit `target` or `rel` attribute. These are historical observations,
  not a fresh production inventory or proof that external destinations work.
- Of those 30, 22 also have an existing Marquee relationship. Current IMAGE
  contracts prohibit Marquees, forcing removal or retention as legacy HTML.
- Current web templates render IMAGE media separately from fragment text.
  Their image-file fallback does not preserve an external click destination.
- The client currently rejects Image-reference edits when `marqueeId` is
  non-null. Model, mutation, locking and selection assumptions must change
  together; a reader-only patch is insufficient.
- `diaries-client/src/app/dayview/dayview.component.html` already places an
  `Image N` label after Position for typed IMAGE fragments. Its helper returns
  `No Image selected` for an unattached IMAGE. This request makes the identity
  explicit as `Image ID: N` and verifies that behaviour with optional Marquees;
  it is not a claim that the header has no existing Image indicator.

Private captions, source HTML, URLs, reviewer drafts and per-fragment evidence
remain in 0028's ignored `evidence/Step 1/private/` tree. Do not copy them into
public change-control records or test fixtures; use synthetic fixtures.

## Expected behaviour and target contract

### Extend IMAGE, retain existing type identities

```text
Fragment -> one authoritative Page under the established ownership contract
MARQUEE  -> zero or one Marquee; no catalogue Image; no image-click URL
IMAGE    -> zero or one catalogue Image; zero or one Marquee; optional image-click URL
Image    -> reusable by zero or more Fragments
Marquee  -> belongs to exactly one Fragment; at most one per Fragment
```

The nullable legacy Page/type compatibility window remains until 0028/0029
resolve it. This feature does not introduce global NOT NULL cleanup.

`imageLinkUrl` is the proposed public field, backed by a nullable Fragment
column such as `image_link_url`. Confirm the exact names and storage limits in
Step 1 and use them consistently in DB, DTOs, RPC, retained JSON and both UIs.
The URL belongs to the Fragment, not reusable Image metadata: two occurrences
of one Image can link to different destinations.

### Image-wrapping link

- A null link preserves today's plain-image behaviour. A valid non-null link
  makes the displayed image clickable, including keyboard activation.
- Support absolute HTTP and HTTPS URLs, including existing HTTP links. Reject
  executable/non-web schemes, protocol-relative URLs, malformed inputs and
  control characters. Enforce validation on the responder and safe rendering
  in consumers; do not rely only on the browser input control.
- Preserve the semantic destination, including path, query and URL fragment.
  HTML entity decoding/escaping must not double-encode or corrupt the URL.
  Do not fetch destinations as part of saving or migrating a link.
- Default to ordinary same-tab navigation, matching the observed legacy
  anchors. New-window preferences and arbitrary anchor attributes are outside
  this feature unless separately designed and reviewed.
- Keep the existing image-file fallback distinct from the external link.
  A missing/unresolved Image must not create a misleading clickable image.
- Editor controls allow deliberate add, edit and clear, with clear validation
  feedback and the existing Fragment authorisation, version and lock checks.
- Omitted link in an update means **preserve**; explicit clear means **remove**.
  Prove the clear representation survives the RPC library's null-handling
  path. Ordinary text/date/order/image edits must not silently erase the link.
- Clearing or replacing an Image reference preserves the Fragment link unless
  explicitly changed. An unattached IMAGE may retain a dormant link; the
  editor must show it so replacement cannot attach an unnoticed destination.

### Optional source-page Marquee

- IMAGE fragments support both absent and present Marquees. Existing IMAGEs
  without one and ordinary MARQUEE fragments retain their behaviour.
- Preserve an existing Marquee's ID, geometry, version and Page association
  when the migration later converts its Fragment. No placeholder rectangle,
  duplicate association or forced deletion is needed to satisfy type rules.
- Where Marquee currently stores `page_id`, it must agree with the Fragment's
  authoritative Page. Reject cross-Page and duplicate relationships; do not
  silently reparent an existing Marquee or alter geometry.
- Support authorised create, select/highlight, geometry editing and explicit
  removal through the existing Marquee workflow extended to IMAGE. Reuse
  established Fragment/Marquee locks and optimistic concurrency, including
  conflict and stale-version behaviour.
- Removing a Marquee leaves the IMAGE Fragment, Image reference, link and
  Page intact. Deleting the Fragment removes its dependent Marquee and retained
  topics but never deletes the catalogue Image or file.
- Clicking the image follows the external link. A separate accessible
  **Show on source page** control selects/highlights its Marquee. Fragment
  selection, drag/reorder and link navigation must not trigger each other.
- A fragment without a Marquee can still navigate to its source Page without
  inventing a highlighted region. Unresolved retained relationships recover
  on replay/reconnect without deleting valid persisted relationships.

### Day reader Image ID

- In the editor Day reader header, show `Image ID: 9` immediately after the
  existing `Position ...` field for an IMAGE with reference ID 9, whether or
  not it has a Marquee or link.
- Read the ID from the Fragment's authoritative `imageId`, including when
  catalogue metadata has not arrived. Never substitute a filename, Page ID,
  caption, suffix match or Marquee ID.
- Show `No Image selected` for an IMAGE with no reference. Do not show an
  invented Image ID for legacy HTML or MARQUEE fragments.
- Update from retained state after Image replacement/clear; preserve responsive
  layout, keyboard access, fragment selection and date-wide ordering.

## Scope across components

| Component | Required work |
|---|---|
| PostgreSQL / responder | Repeatable additive schema change; entity and native-query DTO mapping; link validation; optional-Marquee invariant; mutation/locking/deletion/replay audit |
| MQTT RPC / retained state | Additive URL contract; omitted versus clear semantics; consistent Fragment/Marquee replies and retained projections; transaction-first publication and tombstones |
| diaries-client | Models/projections, IMAGE authoring controls, Marquee workflow, linked media presentation, Day reader Image ID header and regression coverage |
| diaries-web | Parsing/model/render projections, both month and source-page views, safe links, separate source selection and external navigation |
| 0028 tooling | Updated review contract/checker and synthetic fixtures for preserving links/Marquees; do not mark old drafts approved automatically |
| Deployment/docs | Compatible component versions, controlled authoring activation, rollback limits, operating docs and updated 0028/0029 handoff |

Inspect active sources, especially Fragment entities/DTOs/repositories and
`UpdateFragment`, client Fragment models and Image-reference/dayview components,
web Fragment/Marquee projections and both reader templates. Search all
`IMAGE`/`marqueeId` exclusions rather than fixing only the visible editor guard.

No file relocation, NAS writes, static-route/ACL expansion, new fragment type,
legacy production conversion or destructive 0029 schema cleanup is included.
Keep all local modes aligned. Inspect production Playbooks if deployment needs
it; modifications there require their own authorised writable scope.

## Migration and 0028 handoff

0028 is paused. Preserve its frozen inputs and latest reviewed draft unchanged.
Automatic URL extraction is feasible for the observed 30 single-link cases,
but is not equivalent to approving conversion or Page ownership.

Before resuming 0028:

1. Deploy and verify compatible responder, editor and reader capabilities.
2. Replace the old mandatory IMAGE-Marquee removal rule with explicit preserve,
   remove or absent handling. A preserved Marquee must not receive a tombstone.
3. Record the exact extracted link destination in the versioned migration
   manifest; verify source hashes, one reviewed occurrence, supported URL,
   existing Marquee/Page identity and approved text/chronology allocations.
4. Update the review portal/checker to recognise supported preservation only
   after implementation and deployment evidence exists. Do not merely switch
   off its existing link and Marquee blockers.
5. Reconcile fresh production evidence with the frozen inventory. Retain prior
   decisions where expectations still match; flag changed rows for re-review.
6. Rehearse idempotent conversion and DB-to-MQTT replay in restored isolation,
   verifying link behaviour and unchanged Marquee identities/geometry.
7. Obtain approval for the exact production migration run under 0028.

The new capability does not validate the pending Page assignments, Image
verification, caption allocations or review reasons by itself.

## Acceptance criteria

- [ ] Existing IMAGE type supports all four link/Marquee presence combinations.
- [ ] Unlinked IMAGE and ordinary MARQUEE behaviour remains compatible.
- [ ] HTTP/HTTPS destinations round-trip without semantic changes; unsafe URLs
      are rejected and missing links retain plain-image rendering.
- [ ] Link edits obey authorisation/locks/version checks; omitted updates
      preserve it and deliberate clear works across RPC, DB and retained state.
- [ ] IMAGE Marquees can be retained, added, edited and explicitly removed;
      Page consistency, uniqueness and geometry constraints hold.
- [ ] Both UIs separate external image clicks from source highlighting and
      keyboard fragment navigation; mixed/image-only days remain usable.
- [ ] Day reader shows the correct Image ID after Position, including with a
      Marquee and with catalogue metadata pending; null state is explicit.
- [ ] Deletion, reconnect and replay reconcile all Fragment/Marquee topics;
      shared Images and file bytes remain untouched.
- [ ] Existing-data schema upgrade and mixed-version deployment/rollback
      behaviour are rehearsed; no older writer can silently discard new state.
- [ ] Updated 0028 contracts/checks support preservation without auto-approval;
      0029 no longer plans to prohibit valid IMAGE Marquees.
- [ ] Relevant responder/client/web suites, builds and cross-component smoke
      tests pass, with actual commands and evidence recorded.
- [ ] Production capability is verified before 0028 resumes; temporary tooling
      is classified and removed from live/deployed paths where appropriate.

## Deployment, backup and rollback

Use the established verified backup/restore workflow before schema changes.
The schema addition should be repeatable and non-destructive; existing links
start null and existing relationships remain untouched. Audit actual schema
constraints rather than assuming that changing JPA changes production safely.

Establish a deployment/authoring gate so IMAGE-with-Marquee and linked IMAGE
writes cannot start while incompatible consumers or writers are still active.
Do not assume an old binary is a safe rollback after those states exist:
older code explicitly rejects IMAGE Marquees and cannot maintain link fields.
Rehearse rollback with preserved columns/data and document the cutoff after
which coordinated forward recovery or a verified restore is needed. Do not
drop the new column merely to roll back an application.

## Validation and Git references

At request creation, source inspection and pre-change regression baselines were recorded. On 20 November the Cygwin static source baseline passed 12/12 checks and targeted existing-code responder/web and Angular tests passed (39/39 Angular), as documented in Step 1 evidence. Step 2 subsequently passed responder regression and disposable PostgreSQL/MQTT integration. Step 3 passed the Angular production build, 240/240 Angular unit tests, targeted web-reader HTTP regression, and separate disposable public-reader and signed-in Angular editor browser acceptance. The 20 November [Step 3 acceptance review](evidence/Step%203/STEP3-ACCEPTANCE-REVIEW-20261120.md) provides the run IDs and visual evidence. **No production schema change, publication, or deployment has occurred.** New implementation commits, production image versions and production acceptance remain unrecorded. Do not commit or publish merely because this review exists.

## Dependencies and completion

Builds on 0025 persistence, 0026 web rendering, 0027 editor authoring and existing
Marquee facilities. Blocks 0028's migration resumption and informs 0029's final
invariants. Update active architecture/component docs when implementation
changes behaviour; preserve historical completion evidence.

Completion requires all acceptance evidence and an explicit capability handoff
to 0028. This record's creation does not close either feature.
