# 0051-FEAT - Extend IMAGE fragments with links and optional Marquees

## Type

Feature

## Status

**CLOSED — formal feature closure approved by the owner on 21 November 2026. Steps 1–5 accepted.** Implementation, production activation, permanent authoring-gate retirement and the 0028/0029 handoff are complete. See the [formal closure record](evidence/Step%205/0051-FORMAL-CLOSURE-20261121.md) and the [final production acceptance receipt](evidence/Step%205/STEP5-PRODUCTION-CLEANUP-ACCEPTANCE-20261121.md).

- [Step 1 evidence](evidence/Step%201/README.md): baseline and accepted cross-component contract.
- [Step 2 evidence](evidence/Step%202/README.md): responder/DB/MQTT implementation, regressions and disposable PostgreSQL/MQTT receipt `c1759df22f5f`.
- [Step 3 evidence](evidence/Step%203/README.md): accepted client and web implementation, browser/reader smoke and visual tests; the subsequent IMAGE Day Reader rendering correction passed 244 Angular tests and production build.
- [Step 4 production acceptance review](evidence/Step%204/STEP4-PRODUCTION-ACCEPTANCE-REVIEW-20261121.md) and [evidence register](evidence/Step%204/STEP4-PRODUCTION-EVIDENCE-REGISTER-20261121.md): the original rollout activated compatible authoring on client build-79, responder build-85 and web build-9, with owner-confirmed functional acceptance. This is the historical rollout state; the subsequent Step 5 deployment replaced responder build-85 with build-86 and removed both development gates. A separate post-build-79 local build was not recorded at the initial Step 4 review; the later gate-free local Docker build and five browser checks passed during Step 5.
- [Step 5 closure](evidence/Step%205/0051-FORMAL-CLOSURE-20261121.md), [production acceptance receipt](evidence/Step%205/STEP5-PRODUCTION-CLEANUP-ACCEPTANCE-20261121.md) and [0028/0029 handoff](evidence/Step%205/STEP5-0028-0029-HANDOFF-20261121.md): accepted; 0028 production migration remains separately gated.

**Post-activation rollback:** new-format IMAGE links/Marquees may now exist in production. The temporary authoring feature gates have been removed permanently from responder build-86 and its Playbooks configuration. Older binaries are **not** safe rollback targets for new-format records; use compatible forward recovery or an independently verified restore plan.

**Scope boundary:** 0028 production migration and 0029 destructive cleanup have not been authorised or executed under 0051. 0052-DEF (incorrect Whitley Park map content) remains a separate TODO defect.

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
- Of those 30, 22 also have an existing Marquee relationship. At feature
  creation, IMAGE contracts prohibited Marquees; the deployed 0051 contract
  now permits an optional same-Page source Marquee.
- Current web templates render IMAGE media separately from fragment text.
  Their image-file fallback does not preserve an external click destination.
- Before 0051, the client rejected Image-reference edits when `marqueeId` was
  non-null. The integrated model, mutation, locking and selection paths were
  changed together; the deployed fix is not reader-only.
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

`imageLinkUrl` is the implemented public field, backed by nullable PostgreSQL
`fragment.image_link_url` (`VARCHAR(4096)`). Step 1 fixed the names and
storage limit, used consistently across DB, DTOs, RPC, retained JSON and both UIs.
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

0028 remains paused pending its own formally approved resumption gates. Preserve
its frozen inputs and latest reviewed draft unchanged.
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

- [x] Existing IMAGE type supports all four link/Marquee presence combinations.
- [x] Unlinked IMAGE and ordinary MARQUEE behaviour remains compatible.
- [x] HTTP/HTTPS destinations round-trip without semantic changes; unsafe URLs
      are rejected and missing links retain plain-image rendering.
- [x] Link edits obey authorisation/locks/version checks; omitted updates
      preserve it and deliberate clear works across RPC, DB and retained state.
- [x] IMAGE Marquees can be retained, added, edited and explicitly removed;
      Page consistency, uniqueness and geometry constraints hold.
- [x] Both UIs separate external image clicks from source highlighting and
      keyboard fragment navigation; mixed/image-only days remain usable.
- [x] Day reader shows the correct Image ID after Position, including with a
      Marquee and with catalogue metadata pending; null state is explicit.
- [x] Deletion, reconnect and replay reconcile all Fragment/Marquee topics;
      shared Images and file bytes remain untouched.
- [x] Existing-data schema upgrade and mixed-version deployment/rollback
      behaviour are rehearsed; no older writer can silently discard new state.
- [x] Updated 0028 contracts/checks support preservation without auto-approval;
      0029 no longer plans to prohibit valid IMAGE Marquees.
- [x] Relevant responder/client/web suites, builds and cross-component smoke
      tests pass, with actual commands and evidence recorded.
- [x] Production capability is verified before 0028 resumes; temporary tooling
      is classified and removed from live/deployed paths where appropriate.

## Deployment, backup and rollback

Use the established verified backup/restore workflow before schema changes.
The schema addition should be repeatable and non-destructive; existing links
start null and existing relationships remain untouched. Audit actual schema
constraints rather than assuming that changing JPA changes production safely.

The original rollout used deployment/authoring gates so IMAGE-with-Marquee
and linked IMAGE writes could not start with incompatible consumers or writers.
Following accepted production functionality, those temporary gates were retired
from responder build-86 and Playbooks on 21 November 2026. No old writer is a
safe rollback target after new-format records exist; use a compatible forward
recovery or independently verified restore rather than dropping the new column.

## Validation and Git references

The Step 1–3 evidence records the 20 November baseline, responder and
PostgreSQL/MQTT integration, Angular/web regression and isolated editor/reader
acceptance. The Step 4 review records the initial production rollout (client
build-79, responder build-85, web build-9) and the original evidence limitations.
After permanent authoring-gate removal, Java regression, local Docker health,
five local GUI checks, Jenkins publication of responder build-86, coordinated
Ansible deployment, five healthy production containers, absence of the obsolete
JSON properties, Playbooks contract verification and the owner’s production
browser acceptance all passed. The final deployment and acceptance receipt was
committed in Diaries parent `bb9a1cbf1b1e7a20de67703961d598ccbf0505dc`.
Playbooks commit `417de0887109324b5f78ba0fc1bd5591625e4f12` and
controller commit `8efacfa26acaddbea2e0dd2eeab7c8947b29462a` were
pushed. Formal closure was approved on 21 November 2026; see the
[closure record](evidence/Step%205/0051-FORMAL-CLOSURE-20261121.md).

## Dependencies and completion

Builds on 0025 persistence, 0026 web rendering, 0027 editor authoring and existing
Marquee facilities. Blocks 0028's migration resumption and informs 0029's final
invariants. Update active architecture/component docs when implementation
changes behaviour; preserve historical completion evidence.

All 0051 acceptance and handoff requirements have been met. Formal 0051 closure
was approved on 21 November 2026. 0028 remains a separate, independently gated
migration; nothing in this closure approves its production application.
