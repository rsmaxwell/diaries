\set ON_ERROR_STOP on
\unset preflight_ok
\if :{?allow_existing_references}
\else
\set allow_existing_references false
\endif
SET search_path = pg_catalog, public;
\ir assert-schema.sql
SELECT NOT EXISTS (SELECT FROM public.fragment f WHERE to_jsonb(f)->>'image_id' IS NOT NULL)
  OR :'allow_existing_references'::boolean AS references_expected \gset
\if :references_expected
\else
DO $$ BEGIN RAISE EXCEPTION 'Existing references require explicit allow_existing_references=true for repeat/recovery'; END $$;
\endif
\ir snapshot.sql
\set preflight_integrity :integrity_snapshot
SELECT current_database() AS preflight_database, current_user AS preflight_user \gset
\set preflight_ok true
\echo 0025 PREFLIGHT PASS
