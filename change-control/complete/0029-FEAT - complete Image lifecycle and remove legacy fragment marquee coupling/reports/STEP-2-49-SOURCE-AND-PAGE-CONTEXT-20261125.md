# 0029-FEAT Step 2 — Source HTML and candidate Page context evidence

## Basis and scope

Input: `0029-49-review-manifest-20261125-174025.csv` (49 source Fragments, exactly one catalogue filename candidate each). The prior review identified 13 sources with multiple Page candidates. The attached SQL hardcodes exact IDs, captured date, candidate Page IDs, catalogue Image ID and original HTML MD5 from this input. It deliberately does **not** choose ownership from date alone.

## Procedure

Run `bash "$FEATURE/tools/step2-49-extract-context.sh"` from the Windows Cygwin Diaries parent checkout, setting FEATURE to the current feature directory. The script runs two PostgreSQL **repeatable-read, read-only** transactions through the existing development Compose container and captures:

- `0029-49-source-context-<timestamp>.csv`: original embedded-image HTML (unaltered, including possible captions/links), live version, checksum comparison, Image catalogue details, candidate Page IDs.
- `0029-49-page-context-<timestamp>.csv`: a row per candidate Page, with Diary identity, Page title/sequence, number of Page Fragments and a truncated chronological preview of existing same-date Fragments. Candidate context is not proof of destination ownership.

The script detects source checksum drift, missing Page candidates, and unexpected source cardinality. It does not create a journal or run DML/DDL. Source HTML may contain historical/private content; keep the CSVs within the 0029 feature evidence directory and upload only as needed for review.

## Outstanding review gates

1. Manually resolve 13 ambiguous Page assignments from scanned Page context; no default selection.
2. Establish image-byte identity / correction history for catalogue 18 (Hermitage) and 25 (St Isaac's Church), plus other images. Catalogue database checksum alone does not validate legacy source bytes.
3. Preserve original HTML, meaningful captions, sequence ordering, and source-to-destination receipts. Validate Whitley Park existing link independently to avoid creating a duplicate.
4. Develop and test a separately guarded isolated migration adapted from 0028 journal model. **Do not run** `step2-hybrid-schema-and-data.sql` against current development data: it strictly requires exactly 11 Page-less Fragments.

**Status:** diagnostics prepared, not run against user database; Step 2 OPEN, production untouched.
