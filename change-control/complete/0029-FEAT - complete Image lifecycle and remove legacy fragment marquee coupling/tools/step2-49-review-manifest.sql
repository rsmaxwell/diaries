\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='120s';
DO $guard$
DECLARE n int; i int; missing int;
BEGIN
 IF current_database() <> 'diaries' THEN RAISE EXCEPTION 'Expected development DB name diaries'; END IF;
 SELECT count(*) INTO n FROM public.fragment
 WHERE page_id IS NULL AND id <> ALL(ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[]);
 IF n<>49 THEN RAISE EXCEPTION 'Expected exactly 49 additional Page-less fragments, got %',n; END IF;
 SELECT count(*) INTO missing FROM public.fragment
 WHERE page_id IS NULL AND id <> ALL(ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[])
 AND (type IS NOT NULL OR image_id IS NOT NULL OR text !~* '<img');
 IF missing<>0 THEN RAISE EXCEPTION 'Source baseline drift for % rows',missing; END IF;
END $guard$;
COPY (
WITH legacy AS (
 SELECT f.id, f.year,f.month,f.day,f.sequence,f.version,f.text, md5(coalesce(f.text,'')) AS source_html_md5
 FROM public.fragment f
 WHERE f.page_id IS NULL AND f.id <> ALL(ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[])
), tags AS (
 SELECT l.*, x.arr[1] AS src, x.ordinal
 FROM legacy l LEFT JOIN LATERAL (
   SELECT t.arr,t.ordinal FROM regexp_matches(coalesce(l.text,''),
   $rx$<img[^>]*src[[:space:]]*=[[:space:]]*["']([^"']+)["']$rx$,'gi') WITH ORDINALITY AS t(arr,ordinal)
 ) x ON true
), matched AS (
 SELECT t.*, regexp_replace(split_part(split_part(coalesce(t.src,''),'?',1),'#',1),'^.*/','') AS basename,
   i.id AS catalogue_id, i.relative_path, i.checksum AS catalogue_checksum,
   count(i.id) OVER(PARTITION BY t.id,t.ordinal) AS image_candidate_count
 FROM tags t LEFT JOIN public.image i ON
   lower(i.original_filename)=lower(regexp_replace(split_part(split_part(coalesce(t.src,''),'?',1),'#',1),'^.*/',''))
   OR lower(regexp_replace(i.relative_path,'^.*/',''))=lower(regexp_replace(split_part(split_part(coalesce(t.src,''),'?',1),'#',1),'^.*/',''))
)
SELECT m.id AS source_fragment_id,m.year,m.month,m.day,m.sequence,m.version,
 m.source_html_md5,m.ordinal AS image_tag_ordinal,m.basename AS original_basename,
 m.catalogue_id,m.relative_path AS catalogue_path,m.catalogue_checksum,
 m.image_candidate_count,
 (SELECT count(*) FROM public.fragment d WHERE d.type='IMAGE' AND d.image_id=m.catalogue_id
   AND d.year=m.year AND d.month=m.month AND d.day=m.day) AS linked_on_same_day,
 (SELECT string_agg(DISTINCT d.page_id::text,';' ORDER BY d.page_id::text)
  FROM public.fragment d WHERE d.page_id IS NOT NULL AND d.year=m.year AND d.month=m.month AND d.day=m.day) AS page_candidates_same_day,
 CASE WHEN m.ordinal IS NULL THEN 'REVIEW_NO_IMG_TAG'
      WHEN m.image_candidate_count<>1 THEN 'REVIEW_AMBIGUOUS_IMAGE'
      WHEN EXISTS(SELECT 1 FROM public.fragment d WHERE d.type='IMAGE' AND d.image_id=m.catalogue_id
             AND d.year=m.year AND d.month=m.month AND d.day=m.day) THEN 'REVIEW_EXISTING_LINK'
      ELSE 'REVIEW_DESTINATION_AND_CONTENT' END AS review_status
FROM matched m ORDER BY m.year,m.month,m.day,m.id,m.ordinal,m.catalogue_id
) TO STDOUT WITH (FORMAT csv,HEADER true,FORCE_QUOTE *);
COMMIT;
