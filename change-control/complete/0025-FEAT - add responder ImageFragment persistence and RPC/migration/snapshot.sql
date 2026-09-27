SELECT jsonb_build_object(
 'diary',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.diary t),
 'page',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.page t),
 'fragment',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t)-'image_id' ORDER BY id)::text,'[]'))) FROM public.fragment t),
 'marquee',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.marquee t),
 'image',(SELECT jsonb_build_array(count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM public.image t),
 'references',(SELECT md5(coalesce(jsonb_agg(jsonb_build_array(id,to_jsonb(t)->'image_id') ORDER BY id)::text,'[]')) FROM public.fragment t)
)::text AS integrity_snapshot \gset
\echo :integrity_snapshot
