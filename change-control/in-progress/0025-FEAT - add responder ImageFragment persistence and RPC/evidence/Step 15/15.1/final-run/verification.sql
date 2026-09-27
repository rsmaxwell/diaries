\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ;
\set ON_ERROR_STOP on
\unset preflight_ok
\if :{?allow_existing_references}
\else
\set allow_existing_references false
\endif
SET search_path = pg_catalog, public;
-- Shared fail-closed checks. Only temporary objects are created by preflight.
DO $$ BEGIN
  IF to_regclass('public.fragment') IS NULL OR to_regclass('public.image') IS NULL
     OR to_regclass('public.page') IS NULL THEN RAISE EXCEPTION '0022/0024 tables required'; END IF;
  IF NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid='public.fragment'::regclass AND attname='page_id' AND atttypid='bigint'::regtype AND NOT attisdropped)
     OR NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid='public.fragment'::regclass AND attname='type' AND atttypid='varchar'::regtype AND NOT attisdropped)
     OR NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid='public.image'::regclass AND attname='id' AND atttypid='bigint'::regtype AND NOT attisdropped)
  THEN RAISE EXCEPTION 'Required page_id/type/image.id columns missing or incompatible'; END IF;
END $$;
CREATE TEMP TABLE IF NOT EXISTS _0025_expected (LIKE public.fragment);
ALTER TABLE _0025_expected ADD COLUMN IF NOT EXISTS image_id bigint;
ALTER TABLE _0025_expected DROP CONSTRAINT IF EXISTS expected_type;
ALTER TABLE _0025_expected DROP CONSTRAINT IF EXISTS expected_reference;
ALTER TABLE _0025_expected DROP CONSTRAINT IF EXISTS expected_type_varchar;
ALTER TABLE _0025_expected ADD CONSTRAINT expected_type CHECK (type IS NULL OR type IN ('MARQUEE','IMAGE'));
ALTER TABLE _0025_expected ADD CONSTRAINT expected_type_varchar CHECK (type IS NULL OR type::text = ANY(ARRAY['MARQUEE'::varchar::text,'IMAGE'::varchar::text]));
ALTER TABLE _0025_expected ADD CONSTRAINT expected_reference CHECK (image_id IS NULL OR (type IS NOT NULL AND type='IMAGE'));
DO $$
DECLARE c record; a smallint; image_key smallint;
BEGIN
  IF NOT EXISTS (SELECT FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND conname='fragment_type_check' AND contype='c' AND convalidated
    AND pg_get_expr(conbin,conrelid) IN (SELECT pg_get_expr(conbin,conrelid) FROM pg_constraint WHERE conrelid='_0025_expected'::regclass AND conname IN ('expected_type','expected_type_varchar')))
  THEN RAISE EXCEPTION 'Expected validated MARQUEE/IMAGE fragment_type_check required'; END IF;
  IF EXISTS (SELECT FROM public.fragment f LEFT JOIN public.page p ON p.id=f.page_id WHERE f.page_id IS NOT NULL AND p.id IS NULL)
  THEN RAISE EXCEPTION 'Orphan Fragment page reference'; END IF;
  SELECT attnum INTO a FROM pg_attribute WHERE attrelid='public.fragment'::regclass AND attname='image_id' AND NOT attisdropped;
  IF a IS NOT NULL THEN
    IF NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid='public.fragment'::regclass AND attnum=a AND atttypid='bigint'::regtype AND NOT attnotnull AND NOT atthasdef AND attidentity='' AND attgenerated='')
    THEN RAISE EXCEPTION 'Existing image_id must be nullable BIGINT without default/identity/generation'; END IF;
    IF EXISTS (SELECT FROM public.fragment f LEFT JOIN public.image i ON i.id=f.image_id WHERE f.image_id IS NOT NULL AND (i.id IS NULL OR f.type IS DISTINCT FROM 'IMAGE'))
    THEN RAISE EXCEPTION 'Existing image references violate ownership/type'; END IF;
  END IF;
  SELECT attnum INTO image_key FROM pg_attribute WHERE attrelid='public.image'::regclass AND attname='id';
  FOR c IN SELECT * FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND (conname='fragment_image_fk' OR (contype='f' AND a=ANY(conkey))) LOOP
    IF c.conname <> 'fragment_image_fk' OR c.contype <> 'f' OR c.conkey IS DISTINCT FROM ARRAY[a]::smallint[]
       OR c.confrelid <> 'public.image'::regclass OR c.confkey IS DISTINCT FROM ARRAY[image_key]::smallint[]
       OR c.confdeltype <> 'a' OR c.confupdtype <> 'a' OR c.confmatchtype <> 's' OR c.condeferrable
    THEN RAISE EXCEPTION 'Incompatible image foreign key: %', c.conname; END IF;
  END LOOP;
  FOR c IN SELECT * FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND conname='fragment_image_type_check' LOOP
    IF c.contype <> 'c' OR c.connoinherit OR pg_get_expr(c.conbin,c.conrelid) IS DISTINCT FROM
      (SELECT pg_get_expr(conbin,conrelid) FROM pg_constraint WHERE conrelid='_0025_expected'::regclass AND conname='expected_reference')
    THEN RAISE EXCEPTION 'Incompatible fragment_image_type_check'; END IF;
  END LOOP;
  IF to_regclass('public.fragment_image_id_idx') IS NOT NULL AND NOT EXISTS (
    SELECT FROM pg_index x JOIN pg_class ic ON ic.oid=x.indexrelid JOIN pg_am am ON am.oid=ic.relam
    WHERE x.indexrelid=to_regclass('public.fragment_image_id_idx') AND x.indrelid='public.fragment'::regclass
      AND x.indisvalid AND x.indisready AND NOT x.indisunique AND x.indnkeyatts=1 AND x.indnatts=1
      AND x.indkey[0]=a AND x.indpred IS NULL AND x.indexprs IS NULL AND am.amname='btree')
  THEN RAISE EXCEPTION 'Incompatible fragment_image_id_idx'; END IF;
END $$;

SELECT NOT EXISTS (SELECT FROM public.fragment f WHERE to_jsonb(f)->>'image_id' IS NOT NULL)
  OR :'allow_existing_references'::boolean AS references_expected \gset
\if :references_expected
\else
DO $$ BEGIN RAISE EXCEPTION 'Existing references require explicit allow_existing_references=true for repeat/recovery'; END $$;
\endif
SELECT jsonb_build_object(
 'diary',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.diary t),
 'page',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.page t),
 'fragment',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t)-'image_id' ORDER BY id)::text,'[]'))) FROM public.fragment t),
 'marquee',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.marquee t),
 'image',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.image t),
 'references',(SELECT md5(coalesce(jsonb_agg(jsonb_build_array(id,to_jsonb(t)->'image_id') ORDER BY id)::text,'[]')) FROM public.fragment t)
)::text AS integrity_snapshot \gset
\echo :integrity_snapshot

\set preflight_integrity :integrity_snapshot
SELECT current_database() AS preflight_database, current_user AS preflight_user \gset
\set preflight_ok true
\echo 0025 PREFLIGHT PASS

\set ON_ERROR_STOP on
\if :{?preflight_integrity}
\else
DO $$ BEGIN RAISE EXCEPTION 'Preflight snapshot required'; END $$;
\endif
-- Shared fail-closed checks. Only temporary objects are created by preflight.
DO $$ BEGIN
  IF to_regclass('public.fragment') IS NULL OR to_regclass('public.image') IS NULL
     OR to_regclass('public.page') IS NULL THEN RAISE EXCEPTION '0022/0024 tables required'; END IF;
  IF NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid='public.fragment'::regclass AND attname='page_id' AND atttypid='bigint'::regtype AND NOT attisdropped)
     OR NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid='public.fragment'::regclass AND attname='type' AND atttypid='varchar'::regtype AND NOT attisdropped)
     OR NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid='public.image'::regclass AND attname='id' AND atttypid='bigint'::regtype AND NOT attisdropped)
  THEN RAISE EXCEPTION 'Required page_id/type/image.id columns missing or incompatible'; END IF;
END $$;
CREATE TEMP TABLE IF NOT EXISTS _0025_expected (LIKE public.fragment);
ALTER TABLE _0025_expected ADD COLUMN IF NOT EXISTS image_id bigint;
ALTER TABLE _0025_expected DROP CONSTRAINT IF EXISTS expected_type;
ALTER TABLE _0025_expected DROP CONSTRAINT IF EXISTS expected_reference;
ALTER TABLE _0025_expected DROP CONSTRAINT IF EXISTS expected_type_varchar;
ALTER TABLE _0025_expected ADD CONSTRAINT expected_type CHECK (type IS NULL OR type IN ('MARQUEE','IMAGE'));
ALTER TABLE _0025_expected ADD CONSTRAINT expected_type_varchar CHECK (type IS NULL OR type::text = ANY(ARRAY['MARQUEE'::varchar::text,'IMAGE'::varchar::text]));
ALTER TABLE _0025_expected ADD CONSTRAINT expected_reference CHECK (image_id IS NULL OR (type IS NOT NULL AND type='IMAGE'));
DO $$
DECLARE c record; a smallint; image_key smallint;
BEGIN
  IF NOT EXISTS (SELECT FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND conname='fragment_type_check' AND contype='c' AND convalidated
    AND pg_get_expr(conbin,conrelid) IN (SELECT pg_get_expr(conbin,conrelid) FROM pg_constraint WHERE conrelid='_0025_expected'::regclass AND conname IN ('expected_type','expected_type_varchar')))
  THEN RAISE EXCEPTION 'Expected validated MARQUEE/IMAGE fragment_type_check required'; END IF;
  IF EXISTS (SELECT FROM public.fragment f LEFT JOIN public.page p ON p.id=f.page_id WHERE f.page_id IS NOT NULL AND p.id IS NULL)
  THEN RAISE EXCEPTION 'Orphan Fragment page reference'; END IF;
  SELECT attnum INTO a FROM pg_attribute WHERE attrelid='public.fragment'::regclass AND attname='image_id' AND NOT attisdropped;
  IF a IS NOT NULL THEN
    IF NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid='public.fragment'::regclass AND attnum=a AND atttypid='bigint'::regtype AND NOT attnotnull AND NOT atthasdef AND attidentity='' AND attgenerated='')
    THEN RAISE EXCEPTION 'Existing image_id must be nullable BIGINT without default/identity/generation'; END IF;
    IF EXISTS (SELECT FROM public.fragment f LEFT JOIN public.image i ON i.id=f.image_id WHERE f.image_id IS NOT NULL AND (i.id IS NULL OR f.type IS DISTINCT FROM 'IMAGE'))
    THEN RAISE EXCEPTION 'Existing image references violate ownership/type'; END IF;
  END IF;
  SELECT attnum INTO image_key FROM pg_attribute WHERE attrelid='public.image'::regclass AND attname='id';
  FOR c IN SELECT * FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND (conname='fragment_image_fk' OR (contype='f' AND a=ANY(conkey))) LOOP
    IF c.conname <> 'fragment_image_fk' OR c.contype <> 'f' OR c.conkey IS DISTINCT FROM ARRAY[a]::smallint[]
       OR c.confrelid <> 'public.image'::regclass OR c.confkey IS DISTINCT FROM ARRAY[image_key]::smallint[]
       OR c.confdeltype <> 'a' OR c.confupdtype <> 'a' OR c.confmatchtype <> 's' OR c.condeferrable
    THEN RAISE EXCEPTION 'Incompatible image foreign key: %', c.conname; END IF;
  END LOOP;
  FOR c IN SELECT * FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND conname='fragment_image_type_check' LOOP
    IF c.contype <> 'c' OR c.connoinherit OR pg_get_expr(c.conbin,c.conrelid) IS DISTINCT FROM
      (SELECT pg_get_expr(conbin,conrelid) FROM pg_constraint WHERE conrelid='_0025_expected'::regclass AND conname='expected_reference')
    THEN RAISE EXCEPTION 'Incompatible fragment_image_type_check'; END IF;
  END LOOP;
  IF to_regclass('public.fragment_image_id_idx') IS NOT NULL AND NOT EXISTS (
    SELECT FROM pg_index x JOIN pg_class ic ON ic.oid=x.indexrelid JOIN pg_am am ON am.oid=ic.relam
    WHERE x.indexrelid=to_regclass('public.fragment_image_id_idx') AND x.indrelid='public.fragment'::regclass
      AND x.indisvalid AND x.indisready AND NOT x.indisunique AND x.indnkeyatts=1 AND x.indnatts=1
      AND x.indkey[0]=a AND x.indpred IS NULL AND x.indexprs IS NULL AND am.amname='btree')
  THEN RAISE EXCEPTION 'Incompatible fragment_image_id_idx'; END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid='public.fragment'::regclass AND attname='image_id' AND NOT attisdropped)
     OR to_regclass('public.fragment_image_id_idx') IS NULL
     OR (SELECT count(*) FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND conname IN ('fragment_image_fk','fragment_image_type_check') AND convalidated) <> 2
  THEN RAISE EXCEPTION '0025 schema incomplete or unvalidated'; END IF;
END $$;
SELECT jsonb_build_object(
 'diary',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.diary t),
 'page',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.page t),
 'fragment',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t)-'image_id' ORDER BY id)::text,'[]'))) FROM public.fragment t),
 'marquee',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.marquee t),
 'image',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.image t),
 'references',(SELECT md5(coalesce(jsonb_agg(jsonb_build_array(id,to_jsonb(t)->'image_id') ORDER BY id)::text,'[]')) FROM public.fragment t)
)::text AS integrity_snapshot \gset
\echo :integrity_snapshot

SELECT :'preflight_integrity'::jsonb=:'integrity_snapshot'::jsonb AS preserved \gset
\if :preserved
\echo 0025 POSTFLIGHT PASS: all original rows and references preserved
\else
DO $$ BEGIN RAISE EXCEPTION 'Migration changed existing data'; END $$;
\endif


SELECT current_database(),current_user,version();
SELECT column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='image_id';
SELECT conname,convalidated,condeferrable,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND conname IN ('fragment_image_fk','fragment_image_type_check');
SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='fragment' AND indexname='fragment_image_id_idx';
SELECT count(*) AS image_fragments,count(image_id) AS attached_images FROM public.fragment WHERE type='IMAGE';

ROLLBACK;
