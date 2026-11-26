# 0029-FEAT — Step 2 development integrity verification handoff (2026-11-26)

**Scope:** Read-only PostgreSQL postflight. Run against development container `diaries-development-db`, not production. This check does not operate on MQTT or change data. Save evidence beneath `evidence/step-2-final-development-integrity/`.

The checks follow the 0029 hybrid ownership and migration scripts in the 2026-11-26 source bundle. They include type/placement/diary/page ownership, catalogue-image references, Marquee ownership, chronology sequence uniqueness, annual historical PREAMBLE cardinality, recovery of Fragments 1–3, removal of temporary Fragments 2340/2341/2347/2348/2349, 49 migration archives and receipts, 48 converted IMAGE rows, original Fragment 2338/Image 3, and DATED exceptions 1738 and 2061.

**Evidence already accepted:** Responder restart at 11:43 UTC republished `diaries/fragments/{1,2,3}` and `diaries/years/1/1828/preamble/{1,2,3}`, removed temporary 2348/2349 retained aliases, and ended `synchronise: ok`. Both Editor and Reader screenshot checks passed. Do not repeat expensive migration/recovery tests.

**Commands (Windows Cygwin Bash, Diaries parent root):**

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
bash 'change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/run-step2-final-development-integrity.sh'
```

**Acceptance status:** Pending operator-run log. Do not mark Step 2 CLOSED or the feature complete merely because this package was prepared. Review any failed constraint against actual database state, rather than altering historical data to satisfy a query.

**Known limits:** This check validates referential/invariant consistency and anchored content lengths, not byte-for-byte HTML hashes for all 9 annual Fragments nor live MQTT retained payload equality. Previous targeted migration evidence and responder reconciliation logs cover those separately. The image filesystem checks were performed earlier and are not repeated here.
