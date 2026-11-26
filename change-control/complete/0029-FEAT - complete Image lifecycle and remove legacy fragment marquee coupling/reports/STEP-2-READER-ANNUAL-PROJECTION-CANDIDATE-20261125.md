# Step 2 — Reader annual projection candidate (25 November 2026)

Status: **SOURCE CANDIDATE — NOT DEPLOYABLE; NOT ACCEPTED**.

## Grounded source findings

The original reader `ProjectionSnapshot.build` discarded Page-less Fragments before attempting resolution. Its `ResolvedFragment` and WebServer viewer require a real Page. The month template groups only Page-resolved Fragments under dated headings.

## Changes in this candidate

- Accept `TEXT` retained Fragment type while preserving `MARQUEE` as a legacy decoder until the coordinated migration.
- Add `FragmentPlacement` to the reader contract, defaulting older retained payloads to `DATED`.
- Add `diaryId` to canonical year-level Fragment payloads; reject year-level payloads that still specify a Page or Marquee.
- Independently index PREAMBLE and POSTAMBLE Fragments by `(diaryId, year, placement)` in snapshot projections; order by sequence and ID. Do not misclassify valid year-level Fragments as Page-less anomalies.
- Display a year preamble ahead of dated content in the first published month of that year, and a year postamble after dated content in the last published month; preserve sanitized TEXT, render Catalogue IMAGE and Catalogue-owned caption/alt text with safe optional links.
- Add focused retained-contract and projection tests.

## Integration blockers and limitations

- No full Java build or test run was available in this container. Changes have **not** been compiled or integration-verified.
- No editor changes are in this package; it has no annual-content create/edit/manage UI.
- The year-month placement is based on existing *dated* published months. A year with only annual content or requiring a separate annual view needs a further routing/view choice.
- Annual Fragments render as static year content, not selectable source-Page viewer items; this is intentional because they have no Page. Navigation and CSS integration need browser acceptance.
- The current reader ingests canonical `diaries/fragments/{id}`; year-topic subscription/publication and retained alias deletion are responder tasks, not implemented here.
- The responder persistence candidate, all RPC handlers, migration reconciliation, 49 development-only records, SQL schema migration and Angular editor must be integrated before any deployment.
- `fragment.year` alone is not ownership; `diaryId` is required for PREAMBLE/POSTAMBLE.

No PostgreSQL, MQTT or production state was changed. Keep this candidate in feature change control until integrated tests pass.
