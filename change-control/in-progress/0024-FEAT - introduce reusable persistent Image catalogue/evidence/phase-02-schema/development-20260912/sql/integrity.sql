-- Repeated before/after. JSON row hashes preserve nulls and all chronology,
-- ownership, type, text and lock fields without delimiter ambiguities.
SELECT jsonb_build_object(
 'counts',jsonb_build_object('diary',(SELECT count(*) FROM public.diary),
    'page',(SELECT count(*) FROM public.page),'fragment',(SELECT count(*) FROM public.fragment),
    'marquee',(SELECT count(*) FROM public.marquee)),
 'fragmentIntegrity', (SELECT jsonb_build_object(
    'total',count(*),'withoutPage',count(*) FILTER(WHERE f.page_id IS NULL),
    'missingPage',count(*) FILTER(WHERE f.page_id IS NOT NULL AND p.id IS NULL),
    'typedMarquee',count(*) FILTER(WHERE f.type='MARQUEE'),
    'typedImage',count(*) FILTER(WHERE f.type='IMAGE'),
    'unclassified',count(*) FILTER(WHERE f.type IS NULL),
    'invalidType',count(*) FILTER(WHERE f.type NOT IN ('MARQUEE','IMAGE')),
    'withoutMarquee',count(*) FILTER(WHERE m.n=0),
    'withOneMarquee',count(*) FILTER(WHERE m.n=1),
    'withMultipleMarquees',count(*) FILTER(WHERE m.n>1),
    'possibleEmbeddedImages',count(*) FILTER(WHERE f.text ~* '<[[:space:]]*img([[:space:]>]|/>)'))
    FROM public.fragment f LEFT JOIN public.page p ON p.id=f.page_id
    CROSS JOIN LATERAL (SELECT count(*) n FROM public.marquee m WHERE m.fragment_id=f.id) m),
 'marqueeIntegrity',(SELECT jsonb_build_object(
    'missingFragment',count(*) FILTER(WHERE f.id IS NULL),
    'withoutPage',count(*) FILTER(WHERE m.page_id IS NULL),
    'missingPage',count(*) FILTER(WHERE m.page_id IS NOT NULL AND p.id IS NULL),
    'fragmentPageMismatch',count(*) FILTER(WHERE f.id IS NOT NULL AND f.page_id IS DISTINCT FROM m.page_id))
    FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id LEFT JOIN public.page p ON p.id=m.page_id),
 'rowSha256',jsonb_build_object(
    'diary',(SELECT encode(sha256(convert_to(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'),'UTF8')),'hex') FROM public.diary t),
    'page',(SELECT encode(sha256(convert_to(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'),'UTF8')),'hex') FROM public.page t),
    'fragment',(SELECT encode(sha256(convert_to(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'),'UTF8')),'hex') FROM public.fragment t),
    'marquee',(SELECT encode(sha256(convert_to(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'),'UTF8')),'hex') FROM public.marquee t))
) AS integrity_snapshot
\gset
SELECT jsonb_pretty(:'integrity_snapshot'::jsonb) AS diary_integrity;
