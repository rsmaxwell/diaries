# Step 10 — Operator acceptance gate

**Status: OPEN — no snapshot deletion approved.**

## Purpose and scope

Review specific candidate IDs from a fresh read-only plan and decide whether any ONE candidate should be permitted for a later, separately gated Step 11 pilot. Planning does not authorise deletion. Retained native paired sets, replication pins, checkpoint holds, migration-era recovery anchors and all legacy `KEEP` decisions remain protected.

## Baseline candidates (advisory only; 2026-10-19)

| Snapper config | ID | Snapshot UTC | Baseline decision |
|---|---:|---|---|
| `@data` | 19605 | 2026-09-28 00:00:38 | WOULD-DELETE |
| `@data` | 19629 | 2026-09-29 00:00:12 | WOULD-DELETE |
| `@data` | 19677 | 2026-10-01 00:00:03 | WOULD-DELETE |
| `@data` | 19701 | 2026-10-02 00:00:25 | WOULD-DELETE |
| `@data` | 19725 | 2026-10-03 00:00:31 | WOULD-DELETE |
| `@data` | 19773 | 2026-10-05 00:00:07 | WOULD-DELETE |
| `@data` | 19869 | 2026-10-09 00:00:00 | WOULD-DELETE |
| `@data` | 19885 | 2026-10-09 16:00:06 | WOULD-DELETE |

**These identifiers are not preapproved.** There are 17 KEEP entries, including historical coverage and latest legacy anchor 19886; none may be deleted under this gate.

## Gate checklist (to be completed before approval)

- [ ] Capture a **fresh** `legacy-plan --json` plus a human-readable plan from `mars`; ensure both reports agree and candidate is still `WOULD-DELETE`.
- [ ] Independently verify exact Snapper configuration, ID, creation time, read-only Btrfs subvolume identity and source path; check source consistency and candidate not unexpectedly modified.
- [ ] Review restore options, pre-existing historical coverage, checkpoint holds, native protection pins and receive-side replication/parent safety as applicable; no assumed equivalence of lone legacy `@data` and coordinated native paired sets.
- [ ] Confirm native service and timer health and check there is no concurrent native snapshot/prune/replication job for the pilot window.
- [ ] Decide **APPROVE or REJECT a named, single first pilot candidate**, with reason, operator/date/time and rollback/recovery expectations. Do not approve a batch by implication.
- [ ] Specify Step 11 stopping conditions and verification checks; do not create any approval file or run `legacy-delete --execute` as part of Step 10.

## Operator decision

**PENDING.** Candidate: ______  Config: ______  Decision: ______  Rationale: ______  Date/time: ______

Evidence from Step 9 does not itself demonstrate current `backup` replication health; do not silently regard it as verified.
