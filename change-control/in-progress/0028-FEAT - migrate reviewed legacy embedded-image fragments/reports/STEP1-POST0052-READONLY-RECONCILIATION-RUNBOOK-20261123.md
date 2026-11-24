# 0028 — Step 1 post-0052 read-only reconciliation (runbook)

**Prepared:** 2026-11-23. **Step 1 remains OPEN.** This report describes a
verification workflow; it does not claim a live production check was run.

The recovered `0028-0051-review-v2.RECOVERED-598-CONFIRMED.PRIVATE.json` has
71 V2-confirmed `CONVERT_TO_IMAGE` occurrences and one explicit `DEFER`
(Fragment 1564). The existing V2 checker returned zero blockers against the
preserved **21 November** read-only snapshot. Its review gate intentionally
never grants production apply authorisation.

## Purpose and policy

- Obtain **one new** read-only production PostgreSQL snapshot using the existing
  `step1_inventory.py`; neither database nor Files-root is modified.
- Validate every recovered decision against the original 18 November frozen
  evidence **and** the new snapshot with the existing 0051-compatible checker.
- Match all 71 reviewed conversion occurrences to current Image IDs, exact
  catalogue relative paths and current checksums, using the already-reviewed
  0024 proposals. Preserve occurrence-specific caption overrides (notably 575).
- Compare catalogue identity with 21 November: permit metadata corrections
  **only** for Images **3** (Whitley Park) and **18** (Hermitage). Require new
  checksums for both and reject any metadata change to 20, 21, 25 or other
  images. Flag candidate source, chronology, Page, Marquee, and coverage drift.
- Retain private JSON/CSV/snapshot/identity evidence under ignored
  `evidence/Step 1/private/`. The new mapping CSV is a **review aid**, not
  an approved mutation manifest.

## Prerequisites

- Run from the **Windows PC Cygwin terminal**, in the authoritative Diaries
  parent working copy, branch `main`.
- Apply `0028-step1-review-draft-recovery-20261123.zip` first if the recovered
  private JSON is not already in the 0028 Step 1 private evidence directory.
- Preserve all existing uncommitted 0028 work and existing private files.
- Have working `ssh pluto`, Docker Compose and database container as used by
  the existing read-only inventory (no privilege changes or deploy).

## Execute — Windows PC, Cygwin

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'

bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/verify-0028-step1-post0052-readonly.sh'
```

By default this checks the *recovered* private JSON. A differently named
fresh exported JSON can be passed as a single quoted argument. The wrapper
records Git parent/submodule revisions and runs focused offline tests before
any SSH call. It writes a unique timestamped private directory containing
`current/`, `checked/`, `mapped/` and `git-and-input-identity.txt`.

Expected successful outcome: V2 checker 0 blockers, 71 reviewed conversion
mappings, one explicit DEFER, catalogue changes confined to Image IDs 3 and
18, and no unexpected source/candidate drift. A mismatch is **FAIL**, not
permission to patch the data; inspect the local private evidence without
uploading raw diary HTML or private URLs. The earlier accepted 0052 file hash
verification remains available; this new workflow checks database metadata
and does **not** independently rehash every Files-root file.

## Acceptance still required

The reviewer must accept the post-0052 reconciliation, verify updated current
checksums in the final exact migration manifest and sign off its hash. The
separate Step 2 migration CLI, restored-production rehearsal and explicit
production application approval are **not** provided or authorised here.

Legacy Fragments 84/598/599/600 must render correctly in both applications
**after** their separate 0028 migration. 0052's acceptance of their present
absence from the public Reader is not evidence that 0028 has completed.
