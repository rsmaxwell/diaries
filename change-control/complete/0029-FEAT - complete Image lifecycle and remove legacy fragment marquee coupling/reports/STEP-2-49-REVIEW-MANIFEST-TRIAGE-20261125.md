# 0029 Step 2 — 49-record development manifest triage (2026-11-25)

**Disposition: REVIEW ONLY, UNAPPROVED. No SQL or database modifications are included.**

## Reviewed inputs

- User-supplied `0029-49-review-manifest-20261125-174025.csv` (49 rows, each with source Fragment ID, dated sequence, source HTML MD5, Image catalogue ID/path/checksum, same-day Page candidates and candidate status).
- Existing 0029 `IMPLEMENTATION-STEPS.md`, `step2-hybrid-schema-and-data.sql` and 0028 `001-create-journal.sql` from the authoritative 2026-11-25 source bundle.

## Findings

- 49 source Fragments, 49 legacy `<img>` occurrences, 49 unique source IDs; all have exactly one basename catalogue candidate. This does **not** prove byte equality.
- 48 distinct catalogue Images (two source Fragments 547 and 565 share catalogue Image 75). This is not a conflict: multiple dated occurrences may reference one catalogue Image.
- 1 existing dated Image link candidate: source Fragment 84 / Image 3, 1828-03-20, candidate Page 692. Existing target Fragment identity and equivalence must be verified, not recreated blindly.
- 35 **unlinked** rows have a unique same-day Page candidate. Those Page IDs are preliminary and **not approved**.
- 13 unlinked rows have multiple same-day Page candidates (12 have two, one has three); source content and Page context must resolve ownership.
- Every original HTML fingerprint and every catalogue checksum is present. The CSV does **not** include full original HTML, destination Page content, physical image bytes, or source-to-target migration receipts; therefore none of the 49 can be marked migration-approved.
- Explicit checks required for legacy 598 / Image 18 (Hermitage) and 606 / Image 25 (St Isaac's Church), whose image source content has been corrected previously.

## Ambiguous Page records

| Source Fragment | Date | Candidate Page IDs | Catalogue Image |
|---:|---|---|---:|
| 114 | 1828-04-17 | 694;695 | 5 |
| 115 | 1828-04-17 | 694;695 | 6 |
| 116 | 1828-04-17 | 694;695 | 7 |
| 117 | 1828-04-17 | 694;695 | 8 |
| 118 | 1828-04-17 | 694;695 | 9 |
| 565 | 1829-06-20 | 741;742;743 | 75 |
| 575 | 1829-06-26 | 744;745 | 76 |
| 598 | 1829-07-08 | 752;753 | 18 |
| 599 | 1829-07-08 | 752;753 | 21 |
| 600 | 1829-07-08 | 752;753 | 20 |
| 611 | 1829-07-14 | 756;757 | 24 |
| 612 | 1829-07-14 | 756;757 | 23 |
| 613 | 1829-07-14 | 756;757 | 26 |

## Review and migration conditions

1. Obtain the exact source HTML and destination Page context for each of the 49 records, including captions, links, sequence collisions and all plausible Pages. Preserve these data in the feature evidence.
2. Verify actual catalogue image bytes against the embedded-image source bytes, not filename or a catalogue checksum alone. Record any deliberate correction or mismatch, especially Images 18 and 25.
3. Identify the exact existing dated IMAGE Fragment for Fragment 84 and verify same image, Page, date and occurrence semantics before deciding whether to preserve or create an additional occurrence.
4. Review the 13 ambiguous Page assignments individually, with rationale. Check the other 35 unique candidates; do not infer ownership solely from same-day existence.
5. Retain old HTML (including captions/links) and explicit source-to-target receipts. Use an isolated restored database and the 0028 journal design, with updated approved inputs and strict row-set/idempotency guards. Do not change the approved 71-conversion 0028 implementation or its receipts casually.
6. Do **not** run the production-shaped 0029 SQL on this 60-Page-less-row development database: its exact 11-row guard is intentionally designed to abort. Complete 0028 disposition first; rehearse 0029 schema, responder and MQTT updates together on a restored database.

## Decision

**No conversion or deletion approved.** All 49 remain in the review queue. This report and the companion CSV expose precise ownership exceptions without overriding evidence. 0029 Step 2 remains OPEN.
