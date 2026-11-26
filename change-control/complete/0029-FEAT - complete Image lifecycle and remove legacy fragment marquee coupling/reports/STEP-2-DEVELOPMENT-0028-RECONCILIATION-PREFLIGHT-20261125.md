# Step 2 — development 0028/0029 reconciliation preflight (2026-11-25)

**State:** Revised after read-only preflight of 2026-11-25 17:33 UTC; revised version **not run**. No schema migrations, deletions, data edits, MQTT changes, restores or production operations authorised or performed.

## Why this preflight

The existing `step2-hybrid-schema-and-data.sql` deliberately matches the reviewed **11** production Page-less Fragment IDs. The development baseline contains **60** Page-less Fragments, including **49** additional records associated with ongoing 0028 embedded-image work. The guard must continue to reject that development state.

This read-only script compares the extra records with `migration0028_source` and `migration0028_image_occurrence` and prints IDs, date, type, HTML length/tag presence, journal destination, image IDs, and whether preserved original HTML is equal to current HTML. It does not print the historic HTML itself. It also examines the 11 reviewed rows and Marquee Page discrepancies.

## Procedure

Run `bash "change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/step2-development-0028-reconciliation.sh"` from the Windows Cygwin terminal **at the Diaries parent repository root**, with the normal local `development-infrastructure` Docker Compose stack running. The runner checks the Compose file and environment files, then uses `docker compose exec -T diaries-db` to execute `psql` in the development database container. It captures a timestamped log under this feature's `evidence/step-2-development-preflight/`.

Do **not** run the production-shaped migration SQL, and do not delete any records as a result of this diagnostic alone. The journal tables are optional: their DDL explicitly limits creation to a reviewed 0028 rehearsal. When absent, the script reports all 49 development-only rows and per-year distribution using base tables, while marking journal membership, preserved HTML equality and migrated Image equivalence as **unknown**, not false. It must not create the journals.

## Review / next substantive increment

1. Classify each of the 49 IDs: journalled source, unjournalled or anomalous. Confirm original HTML and corresponding migrated image **without** dropping source evidence.
2. Reuse accepted 0028 receipts/manifest and preflight evidence to determine whether records can be preserved as journalled legacy evidence or need a separate reviewed ownership disposition. Do not infer disposable solely from Journal membership.
3. Confirm reviewed 11 annual/dated IDs, destination pages 1005/1078, Marquee mismatches, and schema constraint names.
4. Design a development-specific, reversible migration rehearsal on a **restored isolated database**, with recovery artefacts and startup MQTT reconciliation covered. Keep production-shaped migration guards unchanged until compatibility has been demonstrated.

**Acceptance:** Data disposition, rollback plan and migration target are explicitly reviewed; running this preflight alone does not close Step 1/2 or authorise any migration.

## Observed first run (2026-11-25 17:33 UTC)

The first run detected PostgreSQL 18.7; the hybrid schema had not been applied; exactly 60 Page-less Fragments existed, including the 11 reviewed IDs and 49 extra NULL-type rows. It then stopped on `relation "public.migration0028_source" does not exist`, without modifying data. The replacement keeps the same read-only transaction and works when both journal tables are missing. If only one table is present, journal comparisons are deliberately skipped for investigation.

**Caution:** The 49 records cannot be declared migrated, obsolete or safe to remove based on this preflight. Review 0028 receipts and the original history separately before designing any data disposition.
