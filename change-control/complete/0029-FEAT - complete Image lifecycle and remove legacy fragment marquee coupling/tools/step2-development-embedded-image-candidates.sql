\set ON_ERROR_STOP on
-- 0029 Step 2: strictly read-only classification, never a migration or deletion gate.
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '120s';
\echo '=== Database identity and 0029 source baseline ==='
SELECT current_database() AS database_name, current_user AS database_user, now() AS observed_at;
SELECT count(*) AS development_only_pageless,
       count(*) FILTER (WHERE type IS NULL) AS null_type,
       count(*) FILTER (WHERE text ~* '<img') AS embedded_image_html
FROM public.fragment
WHERE page_id IS NULL AND id <> ALL (ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[]);
\echo '=== 0028 journal availability (absence does NOT imply migrated or unmigrated) ==='
SELECT to_regclass('public.migration0028_source') AS source_journal,
       to_regclass('public.migration0028_image_occurrence') AS occurrence_journal;
\echo '=== Per-source legacy image tags and catalogue filename/path candidates ==='
-- src is deliberately not emitted: may contain paths or tokens. Basename alone is shown.
-- Exact suffix here is a *path candidate*, not a byte/hash match.
-- URLs with percent-encoding or renames will often have no candidate.
WITH legacy AS (
 SELECT f.id, f.year, f.month, f.day, f.sequence, f.version,
        f.type, f.page_id, f.image_id, f.text
 FROM public.fragment f
 WHERE f.page_id IS NULL AND f.id <> ALL (ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[])
), sources AS (
 SELECT l.*, m.ord AS ordinal, m.match[1] AS src,
        split_part(split_part(m.match[1], '?', 1),'#',1) AS clean_src
 FROM legacy l
 LEFT JOIN LATERAL (
   SELECT x.match, x.ord FROM regexp_matches(coalesce(l.text,''),
       $rx$<img[^>]*src[[:space:]]*=[[:space:]]*["']([^"']+)["']$rx$, 'gi')
       WITH ORDINALITY AS x(match,ord)
 ) m ON true
), candidates AS (
 SELECT s.id, s.year, s.month, s.day, s.sequence, s.version, s.ordinal,
        regexp_replace(coalesce(s.clean_src,''), '^.*/', '') AS src_basename,
        s.clean_src,
        count(i.id) FILTER (WHERE i.id IS NOT NULL) AS basename_candidates,
        count(i.id) FILTER (WHERE i.id IS NOT NULL AND
           right(lower(s.clean_src), length(i.relative_path))=lower(i.relative_path)) AS path_suffix_candidates,
        coalesce(array_agg(i.id ORDER BY i.id) FILTER (WHERE i.id IS NOT NULL), ARRAY[]::bigint[]) AS catalogue_candidate_ids
 FROM sources s
 LEFT JOIN public.image i ON s.clean_src IS NOT NULL AND
      (lower(i.original_filename)=lower(regexp_replace(s.clean_src,'^.*/',''))
       OR lower(regexp_replace(i.relative_path,'^.*/',''))=lower(regexp_replace(s.clean_src,'^.*/','')))
 GROUP BY s.id,s.year,s.month,s.day,s.sequence,s.version,s.ordinal,s.clean_src
)
SELECT c.id AS legacy_fragment_id, c.year,c.month,c.day,c.sequence,c.version,
       c.ordinal AS img_ordinal, nullif(left(c.src_basename,130),'') AS src_basename,
       c.basename_candidates, c.path_suffix_candidates,
       c.catalogue_candidate_ids,
       (SELECT count(*) FROM public.fragment df
        WHERE df.type='IMAGE' AND df.image_id IS NOT NULL
          AND df.year=c.year AND df.month=c.month AND df.day=c.day) AS dated_image_fragments_on_day,
       (SELECT count(*) FROM public.fragment df
        WHERE df.type='IMAGE' AND df.image_id = ANY(c.catalogue_candidate_ids)
          AND df.year=c.year AND df.month=c.month AND df.day=c.day) AS matching_candidate_on_day,
       CASE WHEN c.ordinal IS NULL THEN 'NO_PARSEABLE_IMG_SRC'
            WHEN c.path_suffix_candidates>0 THEN 'PATH_SUFFIX_CANDIDATE_ONLY'
            WHEN c.basename_candidates>0 THEN 'FILENAME_CANDIDATE_ONLY'
            ELSE 'NO_CATALOGUE_FILENAME_CANDIDATE' END AS provisional_class
FROM candidates c
ORDER BY c.year,c.month,c.day,c.id,c.ordinal;
\echo '=== Aggregate: legacy HTML image-tag counts and catalogue counts ==='
SELECT (SELECT count(*) FROM public.image) AS catalogue_images,
       (SELECT count(*) FROM public.fragment WHERE type='IMAGE' AND image_id IS NOT NULL) AS existing_image_fragments,
       (SELECT count(*) FROM public.fragment WHERE page_id IS NULL AND id <> ALL
        (ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[])) AS legacy_sources;
\echo '=== Completeness reminder: path and date candidates do not prove source image equivalence ==='
\echo '=== Completed in READ ONLY transaction ==='
COMMIT;
