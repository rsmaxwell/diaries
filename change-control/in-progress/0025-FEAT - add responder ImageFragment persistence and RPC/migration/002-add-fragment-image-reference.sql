\set ON_ERROR_STOP on
\if :{?preflight_ok}
\else
DO $$ BEGIN RAISE EXCEPTION 'Run 001-preflight.sql in the same session first'; END $$;
\endif
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';
SELECT pg_advisory_xact_lock(25,2);
-- Short maintenance window: block chronology writes and schema drift for evidence checks.
LOCK TABLE public.diary, public.page, public.marquee, public.image IN SHARE MODE;
LOCK TABLE public.fragment IN ACCESS EXCLUSIVE MODE;
\ir assert-schema.sql
\ir snapshot.sql
SELECT :'preflight_integrity'::jsonb=:'integrity_snapshot'::jsonb
 AND :'preflight_database'=current_database() AND :'preflight_user'=current_user AS unchanged \gset
\if :unchanged
\else
DO $$ BEGIN RAISE EXCEPTION 'Preflight state changed; rerun preflight'; END $$;
\endif
ALTER TABLE public.fragment ADD COLUMN IF NOT EXISTS image_id bigint;
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND conname='fragment_image_fk') THEN
    ALTER TABLE public.fragment ADD CONSTRAINT fragment_image_fk FOREIGN KEY (image_id) REFERENCES public.image(id) ON DELETE NO ACTION NOT VALID;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND conname='fragment_image_type_check') THEN
    ALTER TABLE public.fragment ADD CONSTRAINT fragment_image_type_check CHECK (image_id IS NULL OR (type IS NOT NULL AND type='IMAGE')) NOT VALID;
  END IF;
END $$;
CREATE INDEX IF NOT EXISTS fragment_image_id_idx ON public.fragment(image_id);
ALTER TABLE public.fragment VALIDATE CONSTRAINT fragment_image_fk;
ALTER TABLE public.fragment VALIDATE CONSTRAINT fragment_image_type_check;
\ir 003-postflight.sql
COMMIT;
\echo 0025 APPLY PASS
