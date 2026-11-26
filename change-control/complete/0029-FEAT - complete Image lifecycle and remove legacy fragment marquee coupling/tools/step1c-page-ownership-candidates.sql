\set ON_ERROR_STOP on
BEGIN TRANSACTION READ ONLY;
\echo '=== Identity and Page/Fragment counts ==='
SELECT current_database() db, current_user db_user, now() captured_at,
       (SELECT count(*) FROM page) pages,
       (SELECT count(*) FROM fragment WHERE page_id IS NULL) pageless;

\echo '=== Page candidates with existing Fragments on EXACT same diary date ==='
-- Matches are candidates only: a date does not uniquely determine a scanned page.
WITH orphan AS (
  SELECT id,year,month,day,sequence,type,length(text) text_chars
  FROM fragment WHERE page_id IS NULL
), dated_page AS (
  SELECT f.year,f.month,f.day,p.id page_id,p.name page_name,p.sequence page_sequence,
         d.id diary_id,d.name diary_name,
         count(*) existing_fragments,
         min(f.sequence) min_fragment_sequence,
         max(f.sequence) max_fragment_sequence
  FROM fragment f JOIN page p ON p.id=f.page_id
  JOIN diary d ON d.id=p.diary_id
  WHERE f.year IS NOT NULL AND f.month BETWEEN 1 AND 12 AND f.day BETWEEN 1 AND 31
  GROUP BY f.year,f.month,f.day,p.id,p.name,p.sequence,d.id,d.name
)
SELECT o.id orphan_id,make_date(o.year,o.month,o.day) orphan_date,o.sequence orphan_sequence,
       o.type orphan_type,o.text_chars,
       p.diary_id,p.diary_name,p.page_id,p.page_name,p.page_sequence,
       p.existing_fragments,p.min_fragment_sequence,p.max_fragment_sequence
FROM orphan o LEFT JOIN dated_page p
 ON (p.year,p.month,p.day)=(o.year,o.month,o.day)
ORDER BY o.id,p.diary_id,p.page_sequence,p.page_id;

\echo '=== Candidate count per Page-less Fragment (zero/multiple = needs manual association) ==='
WITH dated_page AS (
 SELECT DISTINCT f.year,f.month,f.day,p.id
 FROM fragment f JOIN page p ON p.id=f.page_id
)
SELECT o.id,o.year,o.month,o.day,o.sequence,
       count(dp.id) AS same_date_page_candidates
FROM fragment o LEFT JOIN dated_page dp
 ON (dp.year,dp.month,dp.day)=(o.year,o.month,o.day)
WHERE o.page_id IS NULL
GROUP BY o.id,o.year,o.month,o.day,o.sequence
ORDER BY o.id;

\echo '=== Nearest dated existing Page for Page-less Fragments with NO exact-date Page ==='
WITH dated_page AS (
 SELECT p.id page_id,p.name page_name,p.sequence page_sequence,d.id diary_id,d.name diary_name,
        min(make_date(f.year,f.month,f.day)) example_date
 FROM fragment f JOIN page p ON p.id=f.page_id JOIN diary d ON d.id=p.diary_id
 WHERE f.year BETWEEN 1800 AND 2100 AND f.month BETWEEN 1 AND 12 AND f.day BETWEEN 1 AND 28
 GROUP BY p.id,p.name,p.sequence,d.id,d.name
), o AS (
 SELECT id,year,month,day,sequence FROM fragment WHERE page_id IS NULL
), none AS (
 SELECT o.* FROM o WHERE NOT EXISTS (
   SELECT 1 FROM fragment f WHERE f.page_id IS NOT NULL AND
    (f.year,f.month,f.day)=(o.year,o.month,o.day))
)
SELECT n.id orphan_id,make_date(n.year,n.month,n.day) orphan_date,
       p.diary_id,p.diary_name,p.page_id,p.page_name,p.page_sequence,p.example_date,
       abs(p.example_date-make_date(n.year,n.month,n.day)) distance_days
FROM none n LEFT JOIN LATERAL (
 SELECT * FROM dated_page p WHERE extract(year from p.example_date)::int=n.year
 ORDER BY abs(p.example_date-make_date(n.year,n.month,n.day)),p.diary_id,p.page_sequence,p.page_id
 LIMIT 3
) p ON true
ORDER BY n.id,distance_days,p.diary_id,p.page_id;

\echo '=== All Page-less Fragment dates and content category ==='
SELECT id,year,month,day,sequence,type,length(text) text_chars,
 CASE WHEN text ~* '<img[[:space:]>]' THEN 'contains img tag'
      WHEN text ~* 'highlights-section|intro-|forward-section' THEN 'editorial/front matter'
      ELSE 'other HTML/text' END content_hint,
 left(regexp_replace(coalesce(text,''),'[[:space:]]+',' ','g'),120) text_preview
FROM fragment WHERE page_id IS NULL ORDER BY id;
COMMIT;
