# 0028 Step 1 — Page context / 0022 history triage plan (2026-11-18)

**Status:** TOOL PREPARED / LIVE TRIAGE NOT YET RUN / STEP 1 OPEN.

## Accepted terminal evidence, supplied by user

- Frozen current-schema inventory: `20261118T093606Z`, 2329 Fragments, 72 legacy embedded-image candidates, 72 occurrences; 81 NULL types and 60 missing Page IDs are recorded across all Fragments.
- Follow-on Page/reconciliation evidence: `20261118T100019Z-0024`, 72 matched occurrence identities/hashes; 71 uniquely matched `Image` records with `CATALOGUED_MATCH` file status; 1 `AMBIGUOUS_PATH`; all 72 0024 matches were based on `UNIQUE_LOCAL_SUFFIX` (not an approval).
- Page ownership: 22 candidates have matching direct and Marquee Page IDs, 50 have no direct Page nor Marquee.
- Human review aids: `20261118T101501Z-review`, 72 rows, 71 `MATCHED_SNAPSHOT_AND_FILE`, 1 `NOT_RESOLVED`, 72 review blockers; 16 Step 1 tests and three review evidence checksums passed.
- All of these are collected evidence only; no reviewed 0028 migration dispositions, database changes, MQTT changes, or production acceptance have occurred.

## Context investigation

The 0022 feature intentionally left potentially image-bearing legacy Fragments with nullable types, for later deliberate 0028 review. A NULL type on these records is not by itself evidence of data corruption. Fifty of the 72 candidates also lack Page and Marquee relationships, preventing safe first-class IMAGE placement without further reviewed ownership evidence.

The newer tool `tools/step1_triage_context.py` joins existing verified 0028/0024 evidence with the historical 0022 static review ledger. It provides *advisory only* Page hints from nearby Fragments on the same date, plus historical matches if a Fragment ID and/or dated HTML checksum agree. A historical source import review is not an 0028 approval and cannot substitute for checking Page/diary identity. No other page or diary tables were included in the original frozen production snapshot, so foreign-key existence must be checked separately before a mutating migration.

## Remaining acceptance work

1. Run offline triage with the command in `tools/STEP1-CONTEXT-TRIAGE-RUNBOOK.md`; keep raw output under `evidence/Step 1/private/` and record only redacted counts in the public Step 1 report.
2. Resolve the 1 ambiguous image reference manually, or make an explicit reviewed DEFER/KEEP choice as appropriate.
3. Manually determine whether each unowned row can be assigned to a validated Page, or choose an explicit non-mutating disposition. No proximity-based or source-key-based automatic Page assignment.
4. Independently verify every suffix Image mapping and its checksum; assess the original HTML and caption/text allocation. Approve one disposition per Fragment and one action per image occurrence. Feed final decisions to the Step 2 strict manifest validator; hash and sign off the exact reviewed inputs.

**Do not close Step 1, modify production, or claim an approved migration from the triage output.**
