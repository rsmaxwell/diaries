-- 0029 Step 2 / 0028 reconciliation: DEVELOPMENT ONLY, READ-ONLY.
-- No HTML text or credentials are printed. 0028 journal tables are optional.
\set ON_ERROR_STOP on
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '60s';
\echo === Database identity and legacy schema presence ===
SELECT current_database() database_name,current_user database_user,
       inet_server_addr() server_address,inet_server_port() server_port,
       current_setting('server_version') postgres_version,now() captured_at;
SELECT to_regclass('public.migration0028_source') journal_source,
       to_regclass('public.migration0028_image_occurrence') journal_occurrence;
-- psql conditional prevents PostgreSQL from parsing journal references when absent.
SELECT CASE WHEN to_regclass('public.migration0028_source') IS NOT NULL
                  AND to_regclass('public.migration0028_image_occurrence') IS NOT NULL
            THEN 'true' ELSE 'false' END AS has_0028_journal \gset
\if :has_0028_journal
\echo 0028 journal tables found; journal reconciliation enabled.
\else
\echo 0028 journal tables ABSENT; collecting base Fragment and ownership evidence only.
\echo No journal status, migrated Image equivalence or original-HTML equality can be established from this database.
\endif
\echo === Current 0029 schema columns (check migration not already applied) ===
SELECT table_name,column_name,is_nullable,data_type FROM information_schema.columns
WHERE table_schema='public' AND table_name IN ('fragment','marquee')
  AND column_name IN ('page_id','diary_id','placement','type','fragment_id')
ORDER BY table_name,column_name;
\echo === Page-less totals and partition against reviewed 11 IDs ===
WITH reviewed(id) AS (SELECT unnest(ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[]))
SELECT count(*) total_pageless,
       count(*) FILTER (WHERE reviewed.id IS NOT NULL) reviewed_pageless,
       count(*) FILTER (WHERE reviewed.id IS NULL) other_pageless,
       count(*) FILTER (WHERE reviewed.id IS NULL AND f.type='IMAGE') other_image_type,
       count(*) FILTER (WHERE reviewed.id IS NULL AND f.type='MARQUEE') other_marquee_type,
       count(*) FILTER (WHERE reviewed.id IS NULL AND f.type IS NULL) other_null_type
FROM public.fragment f LEFT JOIN reviewed ON reviewed.id=f.id WHERE f.page_id IS NULL;
\if :has_0028_journal
\echo === All 49 development-only Page-less rows, joined to 0028 journal ===
WITH reviewed(id) AS (SELECT unnest(ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[]))
SELECT f.id,f.year,f.month,f.day,f.sequence,f.type,
       length(coalesce(f.text,'')) html_chars,
       (coalesce(f.text,'') ~* '<img[[:space:]>]') contains_html_img,
       f.image_id current_image_id,
       s.fragment_id IS NOT NULL journalled_0028,
       s.destination_page_id journal_destination_page,
       s.image_id journal_image_id,
       CASE WHEN s.fragment_id IS NULL THEN NULL
            ELSE f.text IS NOT DISTINCT FROM s.original_html END matches_0028_original_html,
       (SELECT count(*) FROM public.migration0028_image_occurrence o
        WHERE o.source_fragment_id=f.id) journal_occurrences,
       (SELECT count(*) FROM public.marquee m WHERE m.fragment_id=f.id) marquee_count
FROM public.fragment f LEFT JOIN reviewed r ON r.id=f.id
LEFT JOIN public.migration0028_source s ON s.fragment_id=f.id
WHERE f.page_id IS NULL AND r.id IS NULL
ORDER BY f.id;
\echo === 0028 journal roll-up by source Page ownership and source/current HTML equality ===
SELECT count(*) total_journalled,
       count(*) FILTER (WHERE f.id IS NULL) journal_missing_fragment,
       count(*) FILTER (WHERE f.page_id IS NULL) journal_source_pageless,
       count(*) FILTER (WHERE f.page_id IS NOT NULL) journal_source_page_owned,
       count(*) FILTER (WHERE f.text IS DISTINCT FROM s.original_html) journal_html_changed,
       count(*) FILTER (WHERE f.image_id IS NOT NULL) journal_source_has_image_id,
       count(*) FILTER (WHERE p.id IS NULL) missing_journal_destination_page,
       count(*) FILTER (WHERE i.id IS NULL) missing_journal_image
FROM public.migration0028_source s
LEFT JOIN public.fragment f ON f.id=s.fragment_id
LEFT JOIN public.page p ON p.id=s.destination_page_id
LEFT JOIN public.image i ON i.id=s.image_id;
\echo === Per-year 49-row distribution / journalled vs unjournalled ===
WITH reviewed(id) AS (SELECT unnest(ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[]))
SELECT f.year,count(*) rows,
 count(*) FILTER (WHERE s.fragment_id IS NOT NULL) journalled,
 count(*) FILTER (WHERE s.fragment_id IS NULL) unjournalled,
 count(*) FILTER (WHERE coalesce(f.text,'') ~* '<img[[:space:]>]') img_html
FROM public.fragment f LEFT JOIN reviewed r ON r.id=f.id
LEFT JOIN public.migration0028_source s ON s.fragment_id=f.id
WHERE f.page_id IS NULL AND r.id IS NULL
GROUP BY f.year ORDER BY f.year;
\else
\echo === Development-only Page-less records (without journal; source data only) ===
WITH reviewed(id) AS (SELECT unnest(ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[]))
SELECT f.id,f.year,f.month,f.day,f.sequence,f.type,
       length(coalesce(f.text,'')) html_chars,
       (coalesce(f.text,'') ~* '<img[[:space:]>]') contains_html_img,
       f.image_id current_image_id,
       (SELECT count(*) FROM public.marquee m WHERE m.fragment_id=f.id) marquee_count
FROM public.fragment f LEFT JOIN reviewed r ON r.id=f.id
WHERE f.page_id IS NULL AND r.id IS NULL ORDER BY f.id;
\echo === Per-year 49-row distribution (journal status unavailable) ===
WITH reviewed(id) AS (SELECT unnest(ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061]::bigint[]))
SELECT f.year,count(*) rows,
       count(*) FILTER (WHERE f.type IS NULL) null_type,
       count(*) FILTER (WHERE coalesce(f.text,'') ~* '<img[[:space:]>]') img_html
FROM public.fragment f LEFT JOIN reviewed r ON r.id=f.id
WHERE f.page_id IS NULL AND r.id IS NULL
GROUP BY f.year ORDER BY f.year;
\echo Journal-dependent comparisons SKIPPED: no migration0028_source / migration0028_image_occurrence tables.
\endif
\echo === 0029 reviewed rows, check no drift in owner/date/type ===
SELECT f.id,f.page_id,f.year,f.month,f.day,f.type,f.sequence,
       length(coalesce(f.text,'')) html_chars,
       (SELECT count(*) FROM public.marquee m WHERE m.fragment_id=f.id) marquee_count
FROM public.fragment f
WHERE f.id IN (1,2,3,387,806,1177,1563,1564,1738,1926,2061)
ORDER BY f.id;
\echo === Redundant Marquee Page ownership discrepancies ===
SELECT count(*) total_marquees,
       count(*) FILTER (WHERE f.id IS NULL) missing_fragment,
       count(*) FILTER (WHERE m.page_id IS DISTINCT FROM f.page_id) page_mismatch,
       count(*) FILTER (WHERE f.page_id IS NULL) fragment_pageless
FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id;
\echo === Read-only check complete (no schema or data changes) ===
COMMIT;
