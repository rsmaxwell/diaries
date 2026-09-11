\set ON_ERROR_STOP on

BEGIN;
SET LOCAL lock_timeout = '10s';

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM marquee
        GROUP BY fragment_id
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION '0022 cannot backfill: a Fragment has multiple Marquees';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM marquee m
        LEFT JOIN page p ON p.id = m.page_id
        WHERE m.page_id IS NULL OR p.id IS NULL
    ) THEN
        RAISE EXCEPTION '0022 cannot backfill: a Marquee has an invalid Page';
    END IF;
END $$;

UPDATE fragment f
SET page_id = m.page_id
FROM marquee m
WHERE m.fragment_id = f.id
  AND f.page_id IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM fragment f
        JOIN marquee m ON m.fragment_id = f.id
        WHERE f.page_id IS DISTINCT FROM m.page_id
    ) THEN
        RAISE EXCEPTION '0022 page backfill does not agree with Marquee.page_id';
    END IF;
END $$;

ALTER TABLE fragment VALIDATE CONSTRAINT fragment_page_fk;

COMMIT;

SELECT
    count(*) AS total_fragments,
    count(*) FILTER (WHERE page_id IS NOT NULL) AS fragments_with_page,
    count(*) FILTER (WHERE page_id IS NULL) AS fragments_without_page
FROM fragment;
