\set ON_ERROR_STOP on
BEGIN TRANSACTION READ ONLY;
\echo '=== Database identity ==='
SELECT current_database() AS db, current_user AS db_user, now() AS captured_at;
\echo '=== Fragment columns (for future cleanup review) ==='
SELECT column_name, data_type, is_nullable FROM information_schema.columns
WHERE table_schema='public' AND table_name='fragment' ORDER BY ordinal_position;
\echo '=== Summary of Page-less Fragments ==='
SELECT count(*) AS missing_page,
       count(*) FILTER (WHERE type IS NULL) AS missing_page_and_type,
       count(*) FILTER (WHERE type IS NOT NULL) AS missing_page_with_type,
       count(*) FILTER (WHERE image_id IS NOT NULL) AS with_image,
       count(*) FILTER (WHERE NULLIF(btrim(text),'') IS NOT NULL) AS with_nonempty_text,
       count(*) FILTER (WHERE m.id IS NOT NULL) AS with_marquee
FROM fragment f LEFT JOIN marquee m ON m.fragment_id=f.id WHERE f.page_id IS NULL;
\echo '=== Page-less Fragments with metadata and short text previews ==='
SELECT f.id, f.type, f.year, f.month, f.day, f.sequence, f.version,
       f.image_id, m.id AS marquee_id, m.page_id AS marquee_page_id,
       length(f.text) AS text_chars,
       left(regexp_replace(coalesce(f.text,''), '[[:space:]]+', ' ', 'g'), 160) AS text_preview
FROM fragment f LEFT JOIN marquee m ON m.fragment_id=f.id
WHERE f.page_id IS NULL ORDER BY f.id;
\echo '=== Count of Marquee fragments missing a Marquee ==='
SELECT f.id, f.type, f.year, f.month, f.day,
       length(f.text) AS text_chars
FROM fragment f LEFT JOIN marquee m ON m.fragment_id=f.id
WHERE f.page_id IS NULL AND f.type='MARQUEE' AND m.id IS NULL ORDER BY f.id;
\echo '=== Foreign keys from other tables to Fragment ==='
SELECT c.conrelid::regclass AS referencing_table, c.conname,
       pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c WHERE c.contype='f' AND c.confrelid='public.fragment'::regclass
ORDER BY 1,2;
\echo '=== Page-less Fragment IDs (compare production and development) ==='
SELECT id FROM fragment WHERE page_id IS NULL ORDER BY id;
COMMIT;
