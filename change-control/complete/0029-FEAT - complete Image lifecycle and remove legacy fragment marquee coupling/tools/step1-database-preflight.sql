-- 0029 Step 1: READ-ONLY development database inventory.
-- Inspect the intended environment before running. No DDL/DML.
\set ON_ERROR_STOP on
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
\echo === Identity ===
SELECT current_database() AS database_name, current_user AS database_user, current_setting('server_version') AS pg_version, now() AS snapshot_time;
\echo === Core table presence ===
SELECT to_regclass('public.fragment') AS fragment_table, to_regclass('public.page') AS page_table,
       to_regclass('public.marquee') AS marquee_table, to_regclass('public.image') AS image_table,
       to_regclass('public.migration0028_source') AS migration_0028_source_table;
\echo === Relevant column definitions ===
SELECT table_name, column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema='public' AND table_name IN ('fragment','page','marquee','image')
  AND column_name IN ('id','page_id','fragment_id','image_id','type','relative_path','checksum','width','height','image_link_url')
ORDER BY table_name, ordinal_position;
\echo === Constraints, including validation status ===
SELECT t.relname AS table_name, c.conname, c.contype, c.convalidated,
       pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
JOIN pg_namespace n ON n.oid=t.relnamespace
WHERE n.nspname='public' AND t.relname IN ('fragment','marquee','image','page')
ORDER BY t.relname,c.conname;
\echo === Relevant indexes ===
SELECT tablename,indexname,indexdef FROM pg_indexes
WHERE schemaname='public' AND tablename IN ('fragment','marquee','image') ORDER BY tablename,indexname;
\echo === Fragment counts and nullability ===
SELECT count(*) AS fragments,
 count(*) FILTER (WHERE page_id IS NULL) AS missing_page,
 count(*) FILTER (WHERE type IS NULL) AS missing_type,
 count(*) FILTER (WHERE type IS NOT NULL AND type NOT IN ('IMAGE','MARQUEE')) AS unexpected_type,
 count(*) FILTER (WHERE type='IMAGE') AS images,
 count(*) FILTER (WHERE type='MARQUEE') AS marquees,
 count(*) FILTER (WHERE type='IMAGE' AND image_id IS NULL) AS image_without_catalogue,
 count(*) FILTER (WHERE type='MARQUEE' AND image_id IS NOT NULL) AS marquee_with_image,
 count(*) FILTER (WHERE type='MARQUEE' AND image_link_url IS NOT NULL) AS marquee_with_image_link
FROM public.fragment;
\echo === Fragment exceptions (up to 100 each) ===
SELECT f.id,f.page_id,f.type,f.image_id FROM public.fragment f
LEFT JOIN public.page p ON p.id=f.page_id
LEFT JOIN public.image i ON i.id=f.image_id
WHERE f.page_id IS NULL OR p.id IS NULL OR f.type IS NULL
 OR f.type NOT IN ('IMAGE','MARQUEE')
 OR (f.type='IMAGE' AND (f.image_id IS NULL OR i.id IS NULL))
 OR (f.type='MARQUEE' AND f.image_id IS NOT NULL)
ORDER BY f.id LIMIT 100;
\echo === Marquee integrity counts ===
SELECT count(*) AS marquee_rows,
 count(*) FILTER (WHERE m.fragment_id IS NULL) AS null_fragment,
 count(*) FILTER (WHERE f.id IS NULL) AS missing_fragment,
 count(*) FILTER (WHERE m.page_id IS NULL) AS null_marquee_page,
 count(*) FILTER (WHERE m.page_id IS DISTINCT FROM f.page_id) AS mismatched_page,
 count(*) FILTER (WHERE f.type='IMAGE') AS image_marquees,
 count(*) FILTER (WHERE f.type='MARQUEE') AS text_marquees
FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id;
\echo === Marquee duplicates and mismatch details (up to 100) ===
SELECT m.fragment_id,count(*) AS count FROM public.marquee m
GROUP BY m.fragment_id HAVING count(*)>1 ORDER BY m.fragment_id LIMIT 100;
SELECT m.id AS marquee_id,m.fragment_id,m.page_id AS marquee_page_id,
 f.page_id AS fragment_page_id,f.type AS fragment_type
FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id
WHERE f.id IS NULL OR m.fragment_id IS NULL OR m.page_id IS DISTINCT FROM f.page_id
ORDER BY m.id LIMIT 100;
\echo === Image catalogue counts and metadata exceptions ===
SELECT count(*) AS images,
 count(*) FILTER (WHERE relative_path IS NULL OR length(trim(relative_path))=0) AS missing_path,
 count(*) FILTER (WHERE checksum IS NULL OR checksum !~ '^[0-9a-f]{64}$') AS invalid_checksum,
 count(*) FILTER (WHERE width IS NULL OR width<=0 OR height IS NULL OR height<=0) AS invalid_dimensions
FROM public.image;
SELECT id,relative_path,checksum,width,height FROM public.image
WHERE relative_path IS NULL OR length(trim(relative_path))=0
 OR checksum IS NULL OR checksum !~ '^[0-9a-f]{64}$'
 OR width IS NULL OR width<=0 OR height IS NULL OR height<=0
ORDER BY id LIMIT 100;
SELECT relative_path,count(*) AS duplicate_count FROM public.image
GROUP BY relative_path HAVING count(*)>1 ORDER BY relative_path LIMIT 100;
\echo === 0028 migration journal presence (counts require separate validated query) ===
SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'migration0028_%' ORDER BY table_name;
COMMIT;
