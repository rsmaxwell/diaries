-- 0029 Step 3 rollback of column retirement ONLY, not the hybrid migration.
-- Requires controlled deployment rollback and operator approval.
\set ON_ERROR_STOP on
BEGIN;
SET LOCAL lock_timeout='10s';
SET LOCAL statement_timeout='120s';
DO $guard$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='marquee' AND column_name='page_id')
    THEN RAISE EXCEPTION 'marquee.page_id already present'; END IF;
  IF EXISTS(SELECT 1 FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id
    WHERE f.id IS NULL OR f.page_id IS NULL)
    THEN RAISE EXCEPTION 'Cannot rebuild page_id from incomplete Fragment owners'; END IF;
END $guard$;
ALTER TABLE public.marquee ADD COLUMN page_id bigint;
UPDATE public.marquee m SET page_id=f.page_id FROM public.fragment f WHERE f.id=m.fragment_id;
ALTER TABLE public.marquee ALTER COLUMN page_id SET NOT NULL;
ALTER TABLE public.marquee ADD CONSTRAINT marquee_page_id_fkey FOREIGN KEY (page_id) REFERENCES public.page(id);
COMMIT;
