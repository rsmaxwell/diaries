# 0028 Step 1 — Post-0051 resumption (21 November 2026)

## Decision and baseline

0051-FEAT was formally closed, archived and pushed in Diaries parent
commit `0818179be4b207bcd9600e1e70c4870f6f9823d4`. Production client
`0.0.9-build-79`, responder `0.0.9-build-86` and web `0.0.9-build-9`
were healthy in the accepted 0051 receipts. The two obsolete authoring flags
have been removed. That dependency is now complete; 0028 resumes **ACTIVE**
with Step 1 still **OPEN**.

## Source evidence reviewed

Latest available source bundle:
`diaries-sources-20261121-111041.zip` (local Windows source snapshot;
not a claim that `mango` is synchronized). Private frozen inventory from
18 November contains 72 embedded-image occurrences. The last v1 export (15)
has nine draft rows passing checks and 63 outstanding, not approval.

The 0051-compatible v2 reviewer was run **offline** against the frozen
snapshot and original proposal CSV and prior export (15):

- Twelve synthetic v2 tests: **PASS**.
- Private v2 prepare: **PASS**, no database/Files/MQTT writes.
- 72 occurrences; 30 linked; 22 with Marquees.
- Frozen Marquee evidence lacks version/rectangle geometry for those 22.
- No v1 decisions were promoted to v2 approvals.
- The resulting private portal/JSON are unapproved and were not included
  in any portable source ZIP.

## Immediate integrated step

Run `tools/resume-step1-post0051-readonly.sh` in the authoritative Windows
Cygwin Diaries checkout. It executes a new transaction-read-only PostgreSQL
snapshot against `pluto`, prepares a new v2 private draft bound to fresh
version/geometry, checks it against that snapshot and prints only aggregate
counts/blockers. All evidence remains in ignored
`evidence/Step 1/private/`. The old frozen snapshot and all prior reviews
remain unchanged.

Do **not** run migration, write SQL, alter Files, stop services, publish a
private review, close Step 1 or infer Page ownership. Fresh 0024 file
reconciliation, exact Image identities, text/caption allocation, human
reconfirmation of link/Marquee choices and approval still remain to be done.

## Feature boundaries

0028 owns reviewed migration only. 0029 owns final lifecycle/constraint
cleanup. 0052 remains a separate map positioning defect. No deployment or
schema changes are part of this resumption increment.
