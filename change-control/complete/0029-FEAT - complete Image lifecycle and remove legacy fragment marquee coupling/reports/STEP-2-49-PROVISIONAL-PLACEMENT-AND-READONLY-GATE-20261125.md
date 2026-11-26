# 0029 Step 2 — 49 legacy embedded-image Fragment placement and rehearsal preflight (2026-11-25)

## Evidence used

- `0029-49-review-manifest-20261125-174025.csv`: 49 source HTML fingerprints / unique catalogue filename candidate records.
- `0029-49-source-context-20261125-193610.csv`: complete original HTML, zero detected source drift.
- `0029-49-page-context-20261125-193610.csv`: 63 candidate-page rows, candidate Page identity and nearby dated chronology.
- `0029-49-page-placement-review-20261125.csv`: reviewed 46 candidate placements and three unresolved Alexander Nevsky entries.

## Additional inference for Fragments 611, 612, 613

On 1829-07-14, original embedded images are in sequence 1, 2, 3. The dated text Fragment **614** (sequence **4**) belongs to Page **756** (`img2904`). The next dated text Fragment **615** (sequence **5**) belongs to Page **757** (`img2905`). Thus assigning the three images to Page 756 preserves their before-text sequence in the page chronology. This is a **provisional inference**; inspect the scanned source and obtain editorial acceptance before approving it. The image filenames `img2903` alone cannot settle Page 756 versus 757.

The accompanying mapping contains: 1 pre-existing IMAGE link (84), 35 single-Page candidates, 10 filename/context candidates and 3 sequence/context candidates. **Every mapping row remains PENDING approval**. Image bytes and the post-correction catalogue content for Hermitage Image 18 / Fragment 598 and St Isaac Image 25 / Fragment 606 are NOT verified; do not assume the stored checksum proves the original file is identical.

## Procedure

Run the packaged read-only preflight from the **Windows 11 Cygwin Bash** terminal in the Diaries parent checkout. It uses the two existing generated CSVs and the provisional mapping and compares the 49 source records against a fresh PostgreSQL READ ONLY snapshot. It rejects source HTML drift, missing catalogue/page references, Page/Diary mismatches and unexpected source conversions. It does not create a journal, convert Fragment records, update the schema, change MQTT topics or delete images. Evidence remains under the 0029 feature's evidence directory.

**This is not an isolated restored-database migration execution.** That still requires documented restorable database/media snapshot, specific original-file versus catalogue-file equivalence checks, formal disposition of existing Fragment 84's link, and editorial acceptance of destination Pages. The production-shaped `step2-hybrid-schema-and-data.sql` guard must not be weakened and must not run on this 60-Page-less development baseline.
