\set ON_ERROR_STOP on
\if :{?before_integrity}
\else
DO $$ BEGIN RAISE EXCEPTION 'Postflight requires 001 and 002 in the same psql session'; END $$;
\endif
\if :{?migration_in_transaction}
\else
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL search_path = pg_catalog, public;
SET LOCAL TIME ZONE 'UTC';
\endif
\ir assert-image-schema.sql
\ir integrity.sql
SELECT :'before_integrity'::jsonb = :'integrity_snapshot'::jsonb AS chronology_unchanged,
 (SELECT count(*) FROM public.image) = :'expected_image_rows'::bigint AS image_rows_unchanged
\gset
\if :chronology_unchanged
\else
DO $$ BEGIN RAISE EXCEPTION '0024 altered diary chronology/integrity; transaction must roll back'; END $$;
\endif
\if :image_rows_unchanged
\else
DO $$ BEGIN RAISE EXCEPTION 'Image row count changed or new Image table was not empty'; END $$;
\endif
SELECT count(*) AS image_rows, :'expected_image_rows'::bigint AS expected_image_rows,
 count(*)=0 AS image_table_empty FROM public.image;
SELECT clock_timestamp() AS verified_at, current_database() AS database,
 current_user AS application_user, true AS exact_schema_verified, true AS chronology_unchanged;
\if :{?migration_in_transaction}
\else
ROLLBACK;
\endif
\echo 0024 POSTFLIGHT PASS
