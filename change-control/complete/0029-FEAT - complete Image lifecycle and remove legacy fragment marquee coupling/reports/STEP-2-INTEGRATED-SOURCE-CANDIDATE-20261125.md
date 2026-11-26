# 0029 Step 2 — Consolidated cross-component source candidate (25 November 2026)

Status: **IMPLEMENTATION CANDIDATE — NOT TESTED OR DEPLOYABLE**.

## Contents

Combines the latest responder persistence/type candidate, reader annual-projection candidate, Angular annual model candidate and hybrid database SQL candidate. Additional responder integration repairs:

- Retained-state snapshot now includes non-overlapping `diaries/years/#` so reconciliation can publish and remove annual aliases.
- `updateFragment` preserves `diaryId` and `placement` through native repository updates, and refuses implicit reassignment of annual owner/placement/year through ordinary text-edit RPC.
- The original MQTT topic identity detects `diaryId`/`pageId` changes as well as date/placement changes.
- Tests using the removed `FragmentType.MARQUEE` constant now use `TEXT`; tests cover annual topic publication/tombstones and ownership rejection.

## Important uncompleted integration

1. Responder **create/add** workflow still requires a dedicated way to create preamble and postamble Fragments without a Page or Marquee. The existing `addFragment` RPC requires Page and rectangle coordinates.
2. Editor annual-content **view, edit, reorder and creation UI**, locking integration and retained subscriptions are not wired. The Angular package only supplies model and topic helpers.
3. Reader annual rendering requires a full Java compilation and browser verification. The included reader projection remains a candidate.
4. Native date-sequence normalisation and startup normalisation must be reviewed to exclude year-level Fragments and avoid cross-diary mixing.
5. `Marquee.page_id` removal and migration journal treatment are not implemented.
6. The 49 development-only legacy HTML records have no authorised migration disposition, so the guarded SQL must not be applied there. Production migration needs backup and verified concordance.
7. Legacy retained `MARQUEE` data and old MQTT aliases require an explicit cutover/reconciliation plan, not direct use of these packages.

## Checks

- Archive entry/CRC checks are run when building the ZIP.
- Source-level assertions cover inclusion of `diaries/years/#`, DTO ownership persistence and absence of `FragmentType.MARQUEE` Java enum references.
- Full Java/Angular build and end-to-end tests **have not run** in this isolated source environment. No migrations have executed.

Do not apply or deploy the candidate to a working/production instance as a feature release. It supersedes the earlier individual Step 2 candidate ZIPs for comparison/review.
