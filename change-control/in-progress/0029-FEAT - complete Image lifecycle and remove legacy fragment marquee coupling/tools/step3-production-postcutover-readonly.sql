-- 0029-FEAT post-cutover, production read-only integrity.  No database changes.
\set ON_ERROR_STOP on
BEGIN READ ONLY;
SET LOCAL statement_timeout = '90s';
\echo === Hybrid Fragment distribution ===
SELECT placement,type,count(*) AS fragments FROM public.fragment GROUP BY placement,type ORDER BY placement,type;
\echo === Annual PREAMBLE identities ===
SELECT id,diary_id,year,placement,type,page_id,sequence FROM public.fragment
 WHERE id IN (1,2,3,387,806,1177,1563,1564,1926,1738,2061) ORDER BY id;
\echo === Production ownership and schema assertions ===
DO $verify$
DECLARE n bigint;
BEGIN
 IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='marquee' AND column_name='page_id')
 THEN RAISE EXCEPTION 'FAIL: marquee.page_id still present'; END IF;
 IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='placement')
 THEN RAISE EXCEPTION 'FAIL: fragment.placement missing'; END IF;
 IF (SELECT count(*) FROM public.fragment) <> 2331 THEN RAISE EXCEPTION 'FAIL: unexpected Fragment count'; END IF;
 IF (SELECT count(*) FROM public.marquee) <> 2270 THEN RAISE EXCEPTION 'FAIL: unexpected Marquee count'; END IF;
 IF (SELECT count(*) FROM public.fragment WHERE placement='DATED' AND type='IMAGE') <> 73
 OR (SELECT count(*) FROM public.fragment WHERE placement='DATED' AND type='TEXT') <> 2249
 OR (SELECT count(*) FROM public.fragment WHERE placement='PREAMBLE' AND type='TEXT') <> 9
 OR (SELECT count(*) FROM public.fragment WHERE placement='POSTAMBLE') <> 0
 THEN RAISE EXCEPTION 'FAIL: Fragment type/placement distribution mismatch'; END IF;
 SELECT count(*) INTO n FROM public.fragment f
 LEFT JOIN public.page p ON p.id=f.page_id
 LEFT JOIN public.diary d ON d.id=f.diary_id
 LEFT JOIN public.image i ON i.id=f.image_id
 WHERE f.placement IS NULL OR f.placement NOT IN ('DATED','PREAMBLE','POSTAMBLE')
 OR f.type IS NULL OR f.type NOT IN ('TEXT','IMAGE')
 OR f.diary_id IS NULL OR d.id IS NULL
 OR (f.placement='DATED' AND (f.page_id IS NULL OR p.id IS NULL OR p.diary_id IS DISTINCT FROM f.diary_id))
 OR (f.placement IN ('PREAMBLE','POSTAMBLE') AND (f.page_id IS NOT NULL OR f.month IS DISTINCT FROM 1 OR f.day IS DISTINCT FROM 1))
 OR (f.type='TEXT' AND f.image_id IS NOT NULL)
 OR (f.type='IMAGE' AND (f.image_id IS NULL OR i.id IS NULL))
 OR f.sequence IS NULL OR f.sequence<=0 OR f.year IS NULL;
 IF n<>0 THEN RAISE EXCEPTION 'FAIL: % invalid Fragment ownership/type/Image records', n; END IF;
 SELECT count(*) INTO n FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id
 WHERE f.id IS NULL OR f.placement IS DISTINCT FROM 'DATED' OR f.page_id IS NULL;
 IF n<>0 THEN RAISE EXCEPTION 'FAIL: % invalid Marquee ownership rows', n; END IF;
 SELECT count(*) INTO n FROM (SELECT fragment_id FROM public.marquee WHERE fragment_id IS NOT NULL GROUP BY fragment_id HAVING count(*)>1) a;
 IF n<>0 THEN RAISE EXCEPTION 'FAIL: % duplicated Marquee owners', n; END IF;
 IF (SELECT count(*) FROM public.fragment WHERE id IN (1,2,3) AND diary_id=1 AND year=1828 AND placement='PREAMBLE' AND type='TEXT' AND page_id IS NULL)<>3
 OR NOT EXISTS(SELECT 1 FROM public.fragment WHERE id=387 AND diary_id=1 AND year=1829 AND placement='PREAMBLE' AND page_id IS NULL)
 OR NOT EXISTS(SELECT 1 FROM public.fragment WHERE id=806 AND diary_id=1 AND year=1830 AND placement='PREAMBLE' AND page_id IS NULL)
 OR NOT EXISTS(SELECT 1 FROM public.fragment WHERE id=1177 AND diary_id=3 AND year=1831 AND placement='PREAMBLE' AND page_id IS NULL)
 OR (SELECT count(*) FROM public.fragment WHERE id IN (1563,1564) AND diary_id=4 AND year=1832 AND placement='PREAMBLE' AND page_id IS NULL)<>2
 OR NOT EXISTS(SELECT 1 FROM public.fragment WHERE id=1926 AND diary_id=5 AND year=1834 AND placement='PREAMBLE' AND page_id IS NULL)
 THEN RAISE EXCEPTION 'FAIL: annual PREAMBLE assignments differ'; END IF;
 IF NOT EXISTS(SELECT 1 FROM public.fragment WHERE id=1738 AND page_id=1005 AND placement='DATED' AND type='TEXT')
 OR NOT EXISTS(SELECT 1 FROM public.fragment WHERE id=2061 AND page_id=1078 AND placement='DATED' AND type='TEXT')
 THEN RAISE EXCEPTION 'FAIL: exceptional dated Fragment placement'; END IF;
 RAISE NOTICE 'PASS: 0029 production post-cutover SQL ownership and schema integrity';
END $verify$;
COMMIT;
