# 0051 Step 2 — additive schema migration (not yet applied)

`001-add-image-link-url.sql` adds nullable `public.fragment.image_link_url VARCHAR(4096)` after the approved read-only production schema audit. Running it twice is intended to be harmless; it does not change existing rows, constraints, indexes or snapshot data. `002-assert-image-link-schema.sql` validates the column and existing one-Marquee-per-Fragment uniqueness.

**Do not apply to production at Step 2.** The 0051 rollout gate requires an independently verified recovery point, coordinated responder/client/web deployment, the new extension gate disabled by default and separately authorised schema deployment. Existing `imageFragmentWritesEnabled=true` stays unchanged. Older binaries are unsafe rollback targets after the first extension write.

For isolated local PostgreSQL fixtures, run the first SQL with `psql -X -v ON_ERROR_STOP=1 -f ...`, then re-run it and run the read-only assertion. Capture exact outputs and row counts before/after under `evidence/Step 2/private/`. Do not use the live pluto database for isolated tests.
