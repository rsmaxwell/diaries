-- 0052-DEF Step 1: READ-ONLY catalogue and Fragment reference inventory.
-- Production and development must be queried independently.
-- Output contains private diary HTML: store only in ignored evidence/*.log.
-- Verified against the 23 Nov 2026 responder source bundle.
\set ON_ERROR_STOP on
\pset pager off
\pset null '(NULL)'
\pset format aligned
\timing off
BEGIN TRANSACTION READ ONLY;

\echo ==== 0052 CONTEXT ====
SELECT current_database() AS database_name,
       current_user AS db_role,
       now() AS observed_at_utc,
       current_setting('transaction_read_only') AS transaction_read_only;

\echo ==== 0052 RELEVANT IMAGE CATALOGUE ROWS (including protected images) ====
-- No byte-size column exists in the currently documented Image schema.
-- Do not assume catalogue IDs agree between production and development.
SELECT i.id, i.version, i.relative_path, i.mime_type, i.original_filename,
       i.width, i.height, i.checksum, i.caption, i.alt_text
FROM public.image AS i
WHERE i.id IN (3, 18, 25)
   OR lower(i.relative_path) LIKE '%img2840-image-map-whitley-park%'
   OR lower(i.relative_path) LIKE '%img2900-image-hermitage%'
   OR lower(i.relative_path) LIKE '%img2903-image-st-isaac-church%'
   OR lower(i.relative_path) LIKE '%jordan-staircase%'
ORDER BY i.id;

\echo ==== 0052 REFERENCE COUNTS FOR SELECTED CATALOGUE IMAGES ====
WITH candidates AS (
  SELECT id, relative_path
  FROM public.image
  WHERE id IN (3, 18, 25)
     OR lower(relative_path) LIKE '%img2840-image-map-whitley-park%'
     OR lower(relative_path) LIKE '%img2900-image-hermitage%'
     OR lower(relative_path) LIKE '%img2903-image-st-isaac-church%'
     OR lower(relative_path) LIKE '%jordan-staircase%'
)
SELECT i.id AS image_id, i.relative_path,
       count(f.id) AS direct_fragment_count,
       coalesce(array_agg(f.id ORDER BY f.id) FILTER (WHERE f.id IS NOT NULL), ARRAY[]::bigint[]) AS direct_fragment_ids
FROM candidates AS i
LEFT JOIN public.fragment AS f ON f.image_id = i.id
GROUP BY i.id, i.relative_path
ORDER BY i.id;

\echo ==== 0052 ALL DIRECT CONSUMERS AND MATCHED LEGACY HTML REFERENCES ====
-- Includes reported Fragment IDs 84, 2332, 2333, 598 and 606, irrespective
-- of whether each still refers to the specified image.
-- Exact text hash and length document text immutability without exposing
-- every unrelated fragment's private narrative.
WITH candidate_ids AS (
  SELECT id FROM public.image
  WHERE id IN (3, 18, 25)
     OR lower(relative_path) LIKE '%img2840-image-map-whitley-park%'
     OR lower(relative_path) LIKE '%img2900-image-hermitage%'
     OR lower(relative_path) LIKE '%img2903-image-st-isaac-church%'
     OR lower(relative_path) LIKE '%jordan-staircase%'
)
SELECT f.id AS fragment_id, f.version AS fragment_version,
       f.type, f.image_id, f.page_id, f.year, f.month, f.day, f.sequence,
       f.image_link_url,
       length(f.text) AS html_text_chars,
       md5(coalesce(f.text, '')) AS html_text_md5,
       (lower(f.text) LIKE '%img2840-image-map-whitley-park%') AS mentions_old_whitley_path,
       (lower(f.text) LIKE '%img2900-image-hermitage%') AS mentions_hermitage_path,
       (lower(f.text) LIKE '%img2903-image-st-isaac-church%') AS mentions_st_isaac_path,
       m.id AS marquee_id, m.version AS marquee_version, m.page_id AS marquee_page_id,
       m.x AS marquee_x, m.y AS marquee_y, m.width AS marquee_width, m.height AS marquee_height
FROM public.fragment AS f
LEFT JOIN public.marquee AS m ON m.fragment_id = f.id
WHERE f.id IN (84, 2332, 2333, 598, 606)
   OR f.image_id IN (SELECT id FROM candidate_ids)
   OR lower(f.text) LIKE '%img2840-image-map-whitley-park%'
   OR lower(f.text) LIKE '%img2900-image-hermitage%'
   OR lower(f.text) LIKE '%img2903-image-st-isaac-church%'
ORDER BY f.id;

\echo ==== 0052 EXACT HTML FOR FIVE REPORTED FRAGMENTS (PRIVATE EVIDENCE) ====
-- Necessary to distinguish embedded image src/link from catalogue references.
SELECT id, text
FROM public.fragment
WHERE id IN (84, 2332, 2333, 598, 606)
ORDER BY id;

\echo ==== 0052 SUMMARY COUNTS ====
SELECT count(*) FILTER (WHERE image_id = 3) AS id3_direct_fragments,
       count(*) FILTER (WHERE image_id = 18) AS id18_direct_fragments,
       count(*) FILTER (WHERE lower(text) LIKE '%img2840-image-map-whitley-park%') AS whitley_legacy_html_matches,
       count(*) FILTER (WHERE lower(text) LIKE '%img2900-image-hermitage%') AS hermitage_legacy_html_matches
FROM public.fragment;

COMMIT;
\echo ==== 0052 READ-ONLY INVENTORY COMPLETED ====
