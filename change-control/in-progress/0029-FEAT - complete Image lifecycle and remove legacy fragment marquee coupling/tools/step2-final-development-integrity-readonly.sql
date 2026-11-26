-- 0029-FEAT Step 2 final read-only development integrity verification.
-- Execution target: diaries-development-db only. No data or schema writes.
\set ON_ERROR_STOP on
BEGIN READ ONLY;
SET LOCAL statement_timeout = '60s';

\echo === Fragment ownership and type summary ===
SELECT placement, type, count(*) AS fragments
FROM public.fragment GROUP BY placement,type ORDER BY placement,type;

\echo === Annual PREAMBLE distribution ===
SELECT diary_id, year, placement, count(*) AS fragments,
       string_agg(id::text, ', ' ORDER BY sequence,id) AS fragment_ids
FROM public.fragment
WHERE placement IN ('PREAMBLE','POSTAMBLE')
GROUP BY diary_id,year,placement ORDER BY diary_id,year,placement;

\echo === Historical 1828 PREAMBLE identity and content ===
SELECT id,version,diary_id,placement,type,year,month,day,sequence,
       page_id,marquee_id_placeholder,html_length
FROM (
  SELECT f.id,f.version,f.diary_id,f.placement,f.type,f.year,f.month,f.day,
         f.sequence,f.page_id,
         CASE WHEN EXISTS(SELECT 1 FROM public.marquee m WHERE m.fragment_id=f.id)
              THEN 'UNEXPECTED MARQUEE' ELSE 'none' END AS marquee_id_placeholder,
         length(f.text) AS html_length
  FROM public.fragment f WHERE f.id IN (1,2,3)
) s ORDER BY id;

\echo === Reviewed 49-source conversion and catalogue Image 3 ===
SELECT (SELECT count(*) FROM public.migration0029_rehearsal_receipt) AS reviewed_receipts,
       (SELECT count(*) FROM public.migration0029_legacy_image_archive) AS archived_sources,
       (SELECT count(*) FROM public.migration0029_rehearsal_receipt r
        JOIN public.fragment f ON f.id=r.source_id
        WHERE r.source_id<>84 AND f.type='IMAGE'
        AND f.image_id=r.image_id AND f.page_id=r.destination_page_id
        AND f.year=r.year AND f.month=r.month AND f.day=r.day) AS converted_fragments,
       (SELECT count(*) FROM public.fragment WHERE id=2338 AND type='IMAGE'
        AND placement='DATED' AND image_id=3 AND page_id=692) AS original_whitley_fragment,
       (SELECT count(*) FROM public.image WHERE id=3) AS catalogue_image_3;

\echo === Temporary Fragment absence ===
SELECT id FROM public.fragment WHERE id IN (2340,2341,2347,2348,2349) ORDER BY id;

\echo === Integrity assertion gates (raises error if any fail) ===
DO $checks$
DECLARE
  n bigint;
  issue text;
BEGIN
  SELECT count(*) INTO n FROM public.fragment f
  LEFT JOIN public.page p ON p.id=f.page_id
  LEFT JOIN public.diary d ON d.id=f.diary_id
  LEFT JOIN public.image i ON i.id=f.image_id
  WHERE f.placement NOT IN ('DATED','PREAMBLE','POSTAMBLE') OR f.placement IS NULL
     OR f.type NOT IN ('TEXT','IMAGE') OR f.type IS NULL
     OR f.diary_id IS NULL OR d.id IS NULL
     OR (f.placement='DATED' AND (f.page_id IS NULL OR p.id IS NULL
         OR p.diary_id IS DISTINCT FROM f.diary_id))
     OR (f.placement IN ('PREAMBLE','POSTAMBLE') AND
         (f.page_id IS NOT NULL OR f.month<>1 OR f.day<>1))
     OR (f.type='TEXT' AND f.image_id IS NOT NULL)
     OR (f.type='IMAGE' AND (f.image_id IS NULL OR i.id IS NULL))
     OR f.sequence IS NULL OR f.sequence<=0
     OR f.year IS NULL OR f.month NOT BETWEEN 1 AND 12
     OR f.day NOT BETWEEN 1 AND 31;
  IF n<>0 THEN RAISE EXCEPTION 'FAIL: % invalid Fragment ownership/type/Image/date rows',n; END IF;
  RAISE NOTICE 'PASS: ownership, type, Image references and basic dates';

  SELECT count(*) INTO n FROM public.marquee m
  LEFT JOIN public.fragment f ON f.id=m.fragment_id
  WHERE f.id IS NULL OR f.placement IS DISTINCT FROM 'DATED'
    OR f.page_id IS NULL;
  IF n<>0 THEN RAISE EXCEPTION 'FAIL: % orphaned or annual Marquees',n; END IF;
  SELECT count(*) INTO n FROM (SELECT fragment_id FROM public.marquee
     WHERE fragment_id IS NOT NULL GROUP BY fragment_id HAVING count(*)>1) duplicates;
  IF n<>0 THEN RAISE EXCEPTION 'FAIL: % Fragments have multiple Marquees',n; END IF;
  RAISE NOTICE 'PASS: Marquee ownership';

  SELECT count(*) INTO n FROM (
    SELECT diary_id,year,month,day,sequence FROM public.fragment
      WHERE placement='DATED'
      GROUP BY diary_id,year,month,day,sequence HAVING count(*)>1
    UNION ALL
    SELECT diary_id,year,0,0,sequence FROM public.fragment
      WHERE placement='PREAMBLE'
      GROUP BY diary_id,year,sequence HAVING count(*)>1
    UNION ALL
    SELECT diary_id,year,0,0,sequence FROM public.fragment
      WHERE placement='POSTAMBLE'
      GROUP BY diary_id,year,sequence HAVING count(*)>1
  ) duplicated;
  IF n<>0 THEN RAISE EXCEPTION 'FAIL: % duplicate chronological positions',n; END IF;
  RAISE NOTICE 'PASS: chronological sequence uniqueness';

  SELECT count(*) INTO n FROM public.fragment WHERE placement='PREAMBLE';
  IF n<>9 THEN RAISE EXCEPTION 'FAIL: expected 9 historical PREAMBLEs, found %',n; END IF;
  IF EXISTS(SELECT 1 FROM public.fragment WHERE placement='POSTAMBLE') THEN
    RAISE NOTICE 'INFO: POSTAMBLE rows exist; they were not in the original migrated baseline';
  END IF;
  IF (SELECT count(*) FROM public.fragment WHERE id IN (1,2,3)
     AND version=13 AND diary_id=1 AND placement='PREAMBLE' AND type='TEXT'
     AND year=1828 AND month=1 AND day=1 AND page_id IS NULL
     AND ((id=1 AND sequence=3 AND length(text)=436)
       OR (id=2 AND sequence=4 AND length(text)=182)
       OR (id=3 AND sequence=5 AND length(text)=79)))<>3 THEN
      RAISE EXCEPTION 'FAIL: historical 1828 PREAMBLE identities/content lengths differ';
  END IF;
  IF EXISTS(SELECT 1 FROM public.fragment WHERE id IN (2340,2341,2347,2348,2349)) THEN
    RAISE EXCEPTION 'FAIL: temporary test Fragments remain';
  END IF;
  RAISE NOTICE 'PASS: nine annual PREAMBLEs; restored 1828 IDs; temporary Fragments absent';

  SELECT count(*) INTO n FROM public.migration0029_rehearsal_receipt;
  IF n<>49 THEN RAISE EXCEPTION 'FAIL: expected 49 receipts, found %',n; END IF;
  SELECT count(*) INTO n FROM public.migration0029_legacy_image_archive;
  IF n<>49 THEN RAISE EXCEPTION 'FAIL: expected 49 archived sources, found %',n; END IF;
  SELECT count(*) INTO n FROM public.migration0029_rehearsal_receipt r
  JOIN public.fragment f ON f.id=r.source_id
  WHERE r.source_id<>84 AND f.type='IMAGE'
    AND f.placement='DATED' AND f.image_id=r.image_id
    AND f.page_id=r.destination_page_id
    AND f.diary_id=r.diary_id AND f.year=r.year
    AND f.month=r.month AND f.day=r.day;
  IF n<>48 THEN RAISE EXCEPTION 'FAIL: expected 48 converted IMAGE Fragments, found %',n; END IF;
  IF EXISTS(SELECT 1 FROM public.fragment WHERE id=84) THEN
    RAISE EXCEPTION 'FAIL: redundant legacy HTML Fragment 84 still exists';
  END IF;
  IF NOT EXISTS(SELECT 1 FROM public.fragment WHERE id=2338
     AND placement='DATED' AND type='IMAGE' AND page_id=692 AND image_id=3)
    OR NOT EXISTS(SELECT 1 FROM public.image WHERE id=3) THEN
      RAISE EXCEPTION 'FAIL: original Whitley Park Fragment or catalogue Image 3 missing';
  END IF;
  RAISE NOTICE 'PASS: 49 receipts/archives, 48 conversions, Whitley Park preserved';

  IF NOT EXISTS(SELECT 1 FROM public.fragment WHERE id=1738
      AND placement='DATED' AND page_id=1005)
    OR NOT EXISTS(SELECT 1 FROM public.fragment WHERE id=2061
      AND placement='DATED' AND page_id=1078) THEN
    RAISE EXCEPTION 'FAIL: exceptional DATED Fragment ownership changed';
  END IF;
  RAISE NOTICE 'PASS: exceptional dated Fragments 1738 and 2061';
  RAISE NOTICE 'PASS: ALL 0029 STEP 2 DEVELOPMENT DATABASE INTEGRITY GATES';
END $checks$;
COMMIT;
