-- 0029 Step 3 — read-only production preflight for PRE-hybrid production schema.
-- Run ONLY via psql -X -v ON_ERROR_STOP=1 against the verified diaries-postgres container.
BEGIN TRANSACTION READ ONLY;
WITH expected AS (
 SELECT ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[] AS ids
), actual AS (
 SELECT COALESCE(array_agg(id ORDER BY id),ARRAY[]::bigint[]) AS ids
 FROM public.fragment WHERE page_id IS NULL
), counts AS (
 SELECT
   (SELECT count(*) FROM public.fragment) AS fragments,
   (SELECT count(*) FROM public.marquee) AS marquees,
   (SELECT count(*) FROM public.fragment WHERE type IS NOT NULL AND type NOT IN ('MARQUEE','IMAGE')) AS bad_types,
   (SELECT count(*) FROM public.marquee m JOIN public.fragment f ON f.id=m.fragment_id WHERE f.page_id IS NULL) AS annual_marquees,
   (SELECT count(*) FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id WHERE f.id IS NULL OR f.page_id IS NULL OR m.page_id IS DISTINCT FROM f.page_id) AS bad_marquee_owners,
   (SELECT count(*) FROM public.page WHERE id IN (1005,1078)) AS destination_pages,
   (SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='placement') AS placement_columns,
   (SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='marquee' AND column_name='page_id') AS marquee_page_columns
)
SELECT 'GATE='||CASE WHEN actual.ids=expected.ids AND bad_types=0 AND annual_marquees=0 AND bad_marquee_owners=0 AND destination_pages=2 AND placement_columns=0 AND marquee_page_columns=1
 THEN 'PASS' ELSE 'FAIL' END,
 'pageless_actual='||actual.ids::text,
 'fragments='||fragments,'marquees='||marquees,
 'bad_types='||bad_types,'annual_marquees='||annual_marquees,
 'bad_marquee_owners='||bad_marquee_owners,'destination_pages='||destination_pages,
 'placement_columns='||placement_columns,'marquee_page_columns='||marquee_page_columns
FROM expected CROSS JOIN actual CROSS JOIN counts;
COMMIT;
