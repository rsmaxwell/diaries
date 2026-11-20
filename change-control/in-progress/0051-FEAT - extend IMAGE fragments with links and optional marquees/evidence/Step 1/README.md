# 0051 Step 1 — Preparation and baseline register

**20 November 2026: Step 1 CLOSED after owner approval.** Read-only production baseline, Cygwin static baseline and selected local runtime tests PASS.

The owner requested moving 0051 into `in-progress` and preparing Step 1.
This preparation records the Windows checkout, identifies known exclusions
and defines the next checks. It does not implement the feature or resume 0028.

## Captured evidence

- [Local source baseline](local-source-baseline.json): parent/submodule branch,
  HEAD and working-tree status, recorded after the feature directory move.
  Parent changes include the previously requested 0028 pause/0029 dependency
  edits and uncommitted 0051 documentation; do not discard them.
- [Source audit entry points](source-audit-entry-points.json): selected active
  source file hashes and concrete IMAGE/Marquee assumptions. This is an initial
  map, not an exhaustive audit or a record of passing runtime tests.
- [Evidence hashes](SHA256SUMS.txt): hashes of the two baseline JSON files.
- An ignored private production-container baseline is present in the uploaded
  bundle (file mtime 20 Nov 2026 09:27 UTC). Captured service versions: responder
  `0.0.9-build-84`, client `0.0.9-build-77`, web `0.0.9-build-8`; all three
  recorded as running/healthy. The raw private file is **not** in the change ZIP.
  A new live read-only inspection at 10:47 UTC confirmed running component images
  and PostgreSQL schema; see the [live baseline review](STEP1-LIVE-BASELINE-REVIEW-20261120.md).
- [Step 1 cross-component contract](STEP1-CROSS-COMPONENT-CONTRACT.md),
  [source audit](STEP1-SOURCE-AUDIT.md), and
  [test matrix](STEP1-TEST-MATRIX.md) contain the reviewable decisions.
- [Read-only production inspection procedure](STEP1-NEXT-READONLY-VALIDATION.md)
  records the pluto command and private evidence location; it completed on
  20 November 2026 and need not be repeated for the Python test fix.
- [Static baseline report](step1-static-baseline-results.txt) records the
  read-only source checks in `tests/step1-static-baseline.py`. Those checks
  are **not** application runtime tests. The first Cygwin invocation failed
  on Python annotation compatibility; the corrected script subsequently passed
  **12/12 source checks under Python 3.7.12**. Raw output remains in `private/`.
- The live baseline was inspected read-only from the owner’s Cygwin terminal;
  it did not restart containers, change schema or mutate Image/Marquee rows.
  Selected synthetic existing-code application tests were subsequently run on Windows;
  see the [runtime baseline review](STEP1-RUNTIME-BASELINE-REVIEW-20261120.md).

- [Runtime regression baseline review](STEP1-RUNTIME-BASELINE-REVIEW-20261120.md):
  selected responder and web reader Gradle test builds PASS; Angular Chrome Headless
  **39/39 tests PASS**. Raw logs retained in the ignored `private/` directory.

## Step 1 work queue

| Work | Current state | Next action |
|---|---|---|
| Local revisions and dirty state | Captured | Recheck before implementation; preserve existing edits |
| Deployed responder/client/web versions and authoring gate | Confirmed live 20 Nov; existing IMAGE authoring enabled | Preserve raw output privately; feature-specific rollout gate remains to be tested |
| Local runtime baseline | Targeted existing-code Java and Angular tests PASS on Windows | Run DB/MQTT integration and new-feature scenarios in Steps 2–4 |
| IMAGE/Marquee invariant audit | Source audit + live DB constraints inspected | Confirm same-Page enforcement and mutation behaviour via application tests |
| Client/web contract audit | Source paths and exclusions mapped | Check real retained streams and browser runtime |
| Synthetic baseline | Cygwin Python 3.7: 12/12 source checks PASS; responder/web Gradle tests PASS; Angular 39/39 PASS | Preserve raw logs; do not count new-feature acceptance cases as passed |
| URL and Marquee contract | Proposed detailed contract documented; live schema supports additive URL migration | Review and accept it before Step 2 |
| Mixed-version deployment and rollback | Proposed sequence and cutoff documented | Confirm actual gate capabilities/config and verify in isolated rehearsal |
| Step 1 acceptance | CLOSED — 20 Nov 2026 | Owner approved cross-component contract and coverage boundary; new DB/MQTT integration remains in Steps 2–4 |

## Contract decisions accepted

Owner accepted all seven areas on 20 November 2026; implementation and integration evidence remain Step 2–4 work.


1. Confirm `imageLinkUrl` / `image_link_url`, maximum length and supported
   absolute HTTP/HTTPS forms without corrupting encoded paths or query strings.
2. Specify deliberate clear representation across the RPC library's current
   null-handling behaviour, and preservation on ordinary updates.
3. Define same-Page IMAGE Marquee create/edit/remove operations and lock/version
   ownership; reject duplicate or cross-Page associations. Preserve geometry
   and identity when a later migration retains an existing Marquee.
4. Verify Image replacement/clear and Fragment/Marquee deletion rules, including
   retained topic values/tombstones and restart replay.
5. Keep image-click navigation separate from source highlighting and editor
   selection. Specify accessible controls and missing-media behaviour.
6. Confirm Day reader `Image ID: N` immediately after Position, null-reference
   text, and metadata-pending behaviour. The active source already shows
   `Image N`; this work must preserve and clarify that capability.
7. Define a safe compatibility gate across the three deployed components.
   Additive JSON/schema fields alone do not make IMAGE-with-Marquee compatible
   with old consumers that explicitly reject the relationship.

## Minimum synthetic acceptance matrix to prepare

- IMAGE: neither link nor Marquee; link only; Marquee only; both.
- Existing MARQUEE and legacy HTML compatibility, mixed/image-only days.
- Set/preserve/clear link; HTTP, HTTPS, encoded map query, invalid scheme and
  malformed input; two Fragments sharing an Image with different destinations.
- IMAGE with null/unresolved Image reference and a retained link/Marquee.
- Marquee add/edit/remove, Page mismatch, duplicate association, stale version,
  concurrent locks, transaction failure and Fragment deletion.
- Retained messages arriving in different orders; reconnect, full replay and
  exact tombstone behaviour.
- Day reader Image ID ordering, catalogue metadata pending, replacement/clear,
  keyboard navigation, responsive layout and click/drag event separation.

Use synthetic content. Read production state only for baseline evidence and
retain sensitive output in ignored private storage. No legacy conversion or
destructive cleanup is authorised by starting this step.

## 0028 remains paused

The existing frozen inventory, review export (15) and all intermediate drafts
remain unchanged. Finishing preparation or moving 0051 does not clear the
review blockers or authorise migration. Its resumed workflow requires the
implemented/deployed capability, updated migration contracts and a fresh drift
check against the preserved evidence.
