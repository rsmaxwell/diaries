\set ON_ERROR_STOP on
\if :{?preflight_ok}
\else
DO $$ BEGIN RAISE EXCEPTION 'Run 001-preflight.sql first in the same psql session'; END $$;
\endif
BEGIN;
SET LOCAL search_path = pg_catalog, public;
SET LOCAL TIME ZONE 'UTC';
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';
SELECT pg_advisory_xact_lock(24,2);
-- Prevent concurrent chronology writes while capturing and checking evidence.
LOCK TABLE public.diary, public.page, public.fragment, public.marquee IN SHARE MODE;
\ir prerequisites.sql
\ir integrity.sql
SELECT :'preflight_integrity'::jsonb = :'integrity_snapshot'::jsonb
 AND :'preflight_database' = current_database()
 AND :'preflight_user' = current_user AS preflight_still_valid
\gset
\if :preflight_still_valid
\else
DO $$ BEGIN RAISE EXCEPTION 'Database/user/chronology changed since preflight; rerun preflight'; END $$;
\endif
\set before_integrity :integrity_snapshot
\if :image_exists
LOCK TABLE public.image IN SHARE MODE;
SELECT count(*) AS expected_image_rows FROM public.image
\gset
\echo 0024 existing Image schema accepted; preserving rows
\else
\set expected_image_rows 0
\ir schema.sql
\echo 0024 Image schema created
\endif
\set migration_in_transaction true
\ir 003-postflight.sql
COMMIT;
\unset migration_in_transaction
\echo 0024 APPLY PASS (committed)
