# 0051 Step 4 — source compatibility implementation review

**Status:** IMPLEMENTED OFFLINE; production rollout rehearsal and acceptance OPEN.
**Source:** `diaries-sources-20261120-152822.zip` (20 November 2026).
**Historical authority:** the existing 0028 private frozen snapshot and approved 0051 Steps 1–3.

The 0028 read-only inventory now includes Marquee version and x/y/width/height
for **new** snapshots. The old `IMAGE_HAS_MARQUEE` anomaly has been removed,
while cross-Page, duplicate and missing Page anomalies remain. Existing frozen
source files and reviewer exports were not changed.

The added offline v2 reviewer parses original HTML anchors per IMG ordinal,
verifies exact decoded destinations with SHA-256, requires explicit link
set/clear and Marquee preserve/remove choices, and checks version/Page/HTML
and geometry when supplied with a matching fresh read-only snapshot. It
rejects ambiguous shared anchors, unsafe URLs, cross-Page/stale relationships,
duplicate/conflicting per-Fragment decisions, missing text allocation and
missing reviewer confirmations. It displays legacy v1 choices as hints only.
No writes, replay, conversions or production activation are present.

Read-only source rehearsal against the original private inputs identified
**72 occurrences**, **30 linked**, and **22 with Marquees**. All 22
historical Marquees lack version/geometry in that snapshot. These are
**historic observations**, not a fresh production inventory or approvals.
The v2 output remains `PRIVATE_UNAPPROVED_V2`; existing source SHA-256 inputs
were verified, previous decisions were not promoted.

**Not demonstrated:** the full 0028 Java migration engine, fresh production
preflight, deployed binary compatibility, actual mixed-version rollout,
local-published-smoke image checks or approved production deployment. These
require separate later evidence; Step 4 remains OPEN.
