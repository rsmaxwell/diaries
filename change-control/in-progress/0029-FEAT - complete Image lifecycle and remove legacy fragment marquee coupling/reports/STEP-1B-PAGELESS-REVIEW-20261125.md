# Step 1B — Read-only Page-less Fragment classification

Status: **Diagnostic prepared; not yet executed** (25 November 2026).

## Baseline from Step 1

- Development: 60 Fragments lacking `page_id`, including 59 with no type and Fragment 1738 with type `MARQUEE` but no Marquee.
- Production: 11 Fragments lacking `page_id`, including 10 lacking type. No production Fragment with null type has an associated Marquee.
- Development Step 1A corrected 22 missing `MARQUEE` types; production had none eligible.

## Step 1B

Run `tools/step1b-pageless-fragment-review.sql` as a read-only transaction on **each** database. Record IDs, date, text presence/preview, type, Image and Marquee links, and any declared inbound foreign-key constraints. Compare IDs between environments and review source/migration history before suggesting deletion or reassignment. Do **not** infer a record is disposable simply because `page_id` is null. The SQL provides declared FK introspection, not a complete audit of application/MQTT references.

Save both command outputs under `evidence/step-1/`. Outputs may include short excerpts from historic transcriptions; keep within the Diaries parent repository evidence and review sensitivity before sharing outside it.

No correction or deletion is authorised or performed in Step 1B diagnostics. Do not close Step 1B until outputs and any operational dependencies have been reviewed.
