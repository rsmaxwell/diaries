-- Read-only checks shared by preflight and the locked apply transaction.
DO $$
BEGIN
 IF current_setting('server_version_num')::integer < 180000 THEN
    RAISE EXCEPTION '0024 requires PostgreSQL 18+ and pg_unicode_fast; no schema changes made';
 END IF;
 IF current_setting('server_encoding') <> 'UTF8' THEN RAISE EXCEPTION '0024 requires UTF8'; END IF;
 IF NOT has_database_privilege(current_database(),'CONNECT')
    OR NOT has_schema_privilege('public','USAGE')
    OR NOT has_schema_privilege('public','CREATE') THEN
    RAISE EXCEPTION '0024 requires CONNECT and public USAGE/CREATE as the application owner';
 END IF;
 IF EXISTS(SELECT 1 FROM (VALUES ('diary'),('page'),('fragment'),('marquee')) t(n)
    WHERE to_regclass('public.'||n) IS NULL) THEN RAISE EXCEPTION '0022 base tables are missing'; END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_collation WHERE oid='pg_catalog.pg_unicode_fast'::regcollation AND collisdeterministic) THEN
    RAISE EXCEPTION 'Deterministic pg_unicode_fast collation is required';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relname ~* '^image($|_)'
    AND c.relname NOT IN ('image','image_id_seq','image_pkey','image_relative_path_ci_uq','image_checksum_idx')) THEN
    RAISE EXCEPTION 'Unexpected Image-like relation in public; inspect preflight objects';
 END IF;
 IF to_regclass('public.image') IS NULL AND (
    EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
       WHERE n.nspname='public' AND c.relname ~* '^image($|_)')
    OR to_regtype('public.image') IS NOT NULL OR to_regtype('public._image') IS NOT NULL) THEN
    RAISE EXCEPTION 'Partial Image schema found without public.image';
 END IF;
 IF to_regclass('public.image') IS NOT NULL AND NOT EXISTS(
    SELECT 1 FROM pg_class WHERE oid=to_regclass('public.image') AND relkind='r') THEN
    RAISE EXCEPTION 'public.image exists but is not an ordinary table';
 END IF;
END $$;
SELECT to_regclass('public.image') IS NOT NULL AS image_exists
\gset
\if :image_exists
\ir assert-image-schema.sql
SELECT (SELECT bool_and(has_table_privilege('public.image',p)) FROM (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(p))
   AND (SELECT bool_and(has_sequence_privilege('public.image_id_seq',p)) FROM (VALUES ('USAGE'),('SELECT')) v(p)) AS image_privileges_ok
\gset
\if :image_privileges_ok
\else
DO $$ BEGIN RAISE EXCEPTION 'Application role lacks Image table/sequence privileges'; END $$;
\endif
\endif
