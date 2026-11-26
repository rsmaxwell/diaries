# 0029-FEAT — Step 1A: correct 22 legacy Fragment types

## Evidence and intent

The development database preflight (2026-11-25) identified 22 `fragment` rows with a non-null `page_id`, a matching `marquee.page_id` and a non-null associated Marquee, but null `fragment.type`. The exact Fragment IDs are embedded in the SQL.

This script changes **only those 22 rows** to `MARQUEE` and increments their optimistic-lock `version`. It uses a transaction, checks the initial conditions, and checks the result before committing. It neither deletes records nor changes the schema.

**Use only against `diaries-development-db`, not production.** Capture its stdout/stderr in `evidence/step-1/`. The production data should be separately inspected and a production-specific plan approved before any equivalent change.

A direct SQL correction does **not** itself republish MQTT retained topics. After a successful update, inspect how the running responder refreshes Fragment state and verify the retained publications; do not assume that restarting it necessarily corrects the retained tree.

**Acceptance:** SQL exits zero; post-update query lists exactly 22 rows with type `MARQUEE`; the remaining count of null-type Fragments associated with a Marquee is zero. Step 1 as a whole remains open for the other 60 Page-less Fragments and broader reconciliation.
