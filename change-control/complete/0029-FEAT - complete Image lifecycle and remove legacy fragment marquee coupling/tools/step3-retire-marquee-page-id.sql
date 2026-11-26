-- 0029 Step 3: run ONLY after Step 2 hybrid conversion has committed.
-- Development rehearsal first; production requires separate approval and backup.
\set ON_ERROR_STOP on
BEGIN;
SET LOCAL lock_timeout = '10s';
SET LOCAL statement_timeout = '120s';
DO $guard$
DECLARE mismatch_count bigint; orphan_count bigint;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='marquee' AND column_name='page_id')
    THEN RAISE EXCEPTION 'marquee.page_id already absent; refusing second application'; END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='placement')
    THEN RAISE EXCEPTION '0029 Step 2 hybrid ownership not installed'; END IF;
  SELECT count(*) INTO orphan_count FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id
    WHERE f.id IS NULL OR f.page_id IS NULL OR f.placement IS DISTINCT FROM 'DATED';
  IF orphan_count<>0 THEN RAISE EXCEPTION 'Marquee/Fragment ownership invalid: %',orphan_count; END IF;
  SELECT count(*) INTO mismatch_count FROM public.marquee m JOIN public.fragment f ON f.id=m.fragment_id
    WHERE m.page_id IS DISTINCT FROM f.page_id;
  IF mismatch_count<>0 THEN RAISE EXCEPTION 'Marquee redundant Page mismatch: %',mismatch_count; END IF;
END $guard$;
ALTER TABLE public.marquee DROP COLUMN page_id;
DO $verify$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='marquee' AND column_name='page_id')
    THEN RAISE EXCEPTION 'marquee.page_id still present'; END IF;
END $verify$;
COMMIT;
