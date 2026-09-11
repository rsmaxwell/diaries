\set ON_ERROR_STOP on

BEGIN;
SET LOCAL lock_timeout = '10s';

ALTER TABLE fragment ADD COLUMN IF NOT EXISTS page_id BIGINT;
ALTER TABLE fragment ADD COLUMN IF NOT EXISTS type VARCHAR(16);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'fragment'::regclass
          AND conname = 'fragment_type_check'
    ) THEN
        ALTER TABLE fragment
            ADD CONSTRAINT fragment_type_check
            CHECK (type IS NULL OR type IN ('MARQUEE', 'IMAGE'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'fragment'::regclass
          AND conname = 'fragment_page_fk'
    ) THEN
        ALTER TABLE fragment
            ADD CONSTRAINT fragment_page_fk
            FOREIGN KEY (page_id) REFERENCES page(id)
            NOT VALID;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS fragment_page_id_idx ON fragment(page_id);

COMMIT;
