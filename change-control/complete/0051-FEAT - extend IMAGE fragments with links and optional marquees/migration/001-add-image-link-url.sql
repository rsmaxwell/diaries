\set ON_ERROR_STOP on
-- 0051 Step 2: apply only on a verified compatible schema, with a backup available.
BEGIN;
SET LOCAL lock_timeout = '10s';
ALTER TABLE public.fragment ADD COLUMN IF NOT EXISTS image_link_url VARCHAR(4096);
DO $$
DECLARE column_type text; max_chars integer;
BEGIN
    SELECT data_type, character_maximum_length INTO column_type, max_chars
      FROM information_schema.columns
     WHERE table_schema='public' AND table_name='fragment' AND column_name='image_link_url';
    IF column_type IS DISTINCT FROM 'character varying' OR max_chars IS DISTINCT FROM 4096 THEN
        RAISE EXCEPTION '0051: incompatible fragment.image_link_url definition';
    END IF;
END $$;
COMMIT;
