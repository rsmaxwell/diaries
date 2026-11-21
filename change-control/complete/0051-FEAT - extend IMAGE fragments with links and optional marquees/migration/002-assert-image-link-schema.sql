\set ON_ERROR_STOP on
-- Read-only 0051 assertion; rerunnable after 001 or on an isolated fixture.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='fragment'
          AND column_name='image_link_url' AND data_type='character varying'
          AND character_maximum_length=4096 AND is_nullable='YES') THEN
        RAISE EXCEPTION '0051: fragment.image_link_url missing/incompatible';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
        WHERE conrelid='public.marquee'::regclass
          AND contype='u' AND pg_get_constraintdef(oid) LIKE '%(fragment_id)%') THEN
        RAISE EXCEPTION '0051: unique Marquee/Fragment association absent';
    END IF;
END $$;
SELECT '0051 SCHEMA ASSERT PASS' AS result;
