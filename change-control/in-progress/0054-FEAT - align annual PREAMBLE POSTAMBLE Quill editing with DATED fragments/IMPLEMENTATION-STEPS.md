# 0054-FEAT — Implementation steps

**Status:** IN PROGRESS — 26 November 2026

## Step 1 — Confirm current editor behaviour and choose parity contract (CLOSED — accepted by continuing to implementation)

- In the Windows Diaries working tree check parent branch/revision/status, `.gitmodules`, submodule status, and Client branch/revision/status before editing. Compare with the November 26 source snapshot.
- Inspect annual editor and normal DATED `TextPanelComponent` Quill setup, stylesheet, HTML content handling, max-length validation, lock/save logic and relevant tests.
- Establish which DATED toolbar capabilities should also apply to annual TEXT content, especially image insertion and HTML compatibility; retain current annual IMAGE catalogue workflow.
- Record the final parity decisions in a concise report in `reports/`.

**Gate:** Identified behavioural gap and agreed functional contract; do not claim Quill is absent without verifying.

## Step 2 — Implement annual Quill parity (IMPLEMENTED — validation pending)

- Implement the agreed shared Quill configuration and annual editor improvements in one coherent Angular change.
- Cover both new and existing PREAMBLE/POSTAMBLE TEXT content; preserve annual DTOs, RPCs, retained MQTT topic subscriptions, sequencing and locks.
- Add/update focused tests for formatting round-trip, unchanged text, cancellation, errors and editor transitions. Keep DATED editor behaviour intact.

**Gate:** Client build and targeted tests pass.

## Step 3 — Consolidated verification and release (OPEN)

- Exercise create/edit/save/reload of PREAMBLE and POSTAMBLE TEXT, HTML format preservation, locking and Reader rendering; regression-check DATED TEXT and annual IMAGE features.
- Record build/test/browser results, relevant Git revisions and rollback mechanism inside this feature.
- Release through the existing standard Diaries pipeline when approved, with a production browser smoke check.

**Gate:** Functional acceptance, evidence and owner approval. Only then mark CLOSED and move the full feature directory to `change-control/complete/`.

## Implementation note — 26 November 2026

Step 1 contract was accepted by the owner's instruction to continue. Step 2 changes are
packaged for review; the client build and targeted test gate remains **OPEN** because
this analysis container could not restore npm or Gradle dependencies. See
`reports/0054-STEP2-IMPLEMENTATION-AND-VERIFICATION.md`. Step 3 has not started.

## Step 3 follow-up — owner-approved toolbar parity (27 November 2026)

- DATED and PREAMBLE/POSTAMBLE TEXT editors must expose **exactly the same** Quill toolbar controls.
- Keep hyperlink insertion; remove inline image insertion from both toolbars.
- Keep annual IMAGE fragments and catalogue image management unchanged.
- Prevent paste/drop insertion of new inline images while preserving already-stored legacy HTML.
- Include focused toolbar and paste/drop regression tests in Step 3 acceptance.
- Verify in the development browser before release. No release/closure is authorised by this package.
