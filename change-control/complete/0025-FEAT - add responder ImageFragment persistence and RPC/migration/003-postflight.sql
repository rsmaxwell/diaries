\set ON_ERROR_STOP on
\if :{?preflight_integrity}
\else
DO $$ BEGIN RAISE EXCEPTION 'Preflight snapshot required'; END $$;
\endif
\ir assert-schema.sql
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_attribute WHERE attrelid='public.fragment'::regclass AND attname='image_id' AND NOT attisdropped)
     OR to_regclass('public.fragment_image_id_idx') IS NULL
     OR (SELECT count(*) FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND conname IN ('fragment_image_fk','fragment_image_type_check') AND convalidated) <> 2
  THEN RAISE EXCEPTION '0025 schema incomplete or unvalidated'; END IF;
END $$;
\ir snapshot.sql
SELECT :'preflight_integrity'::jsonb=:'integrity_snapshot'::jsonb AS preserved \gset
\if :preserved
\echo 0025 POSTFLIGHT PASS: all original rows and references preserved
\else
DO $$ BEGIN RAISE EXCEPTION 'Migration changed existing data'; END $$;
\endif
