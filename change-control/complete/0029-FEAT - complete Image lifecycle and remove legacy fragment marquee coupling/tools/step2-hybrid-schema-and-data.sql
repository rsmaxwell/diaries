-- 0029-FEAT Step 2 — production-shaped HYBRID ownership conversion.
-- NOT FOR EXECUTION until responder, client, reader and MQTT publication are ready
-- and a current restorable production backup is documented.
-- Intended for production-shaped data with exactly the approved 11 Page-less rows.
-- Deliberately ABORTS on the additional 49 Page-less development records.
-- All changes are transactional. psql must use -X -v ON_ERROR_STOP=1.
BEGIN;
SET LOCAL lock_timeout = '10s';
SET LOCAL statement_timeout = '120s';

-- Refuse to proceed if this is not the reviewed 11-row production baseline.
DO $guard$
DECLARE
    expected bigint[] := ARRAY[1,2,3,387,806,1177,1563,1564,1738,1926,2061];
    actual bigint[];
    invalid_count bigint;
BEGIN
    SELECT COALESCE(array_agg(id ORDER BY id), ARRAY[]::bigint[]) INTO actual
    FROM fragment WHERE page_id IS NULL;
    IF actual IS DISTINCT FROM expected THEN
        RAISE EXCEPTION '0029 production row-set mismatch: expected %, actual %', expected, actual;
    END IF;
    SELECT count(*) INTO invalid_count FROM fragment
    WHERE type IS NOT NULL AND type NOT IN ('MARQUEE','IMAGE');
    IF invalid_count <> 0 THEN
        RAISE EXCEPTION '0029 unexpected existing Fragment types: %',invalid_count;
    END IF;
    IF NOT EXISTS(SELECT 1 FROM page WHERE id=1005)
       OR NOT EXISTS(SELECT 1 FROM page WHERE id=1078) THEN
        RAISE EXCEPTION '0029 dated destination Page missing';
    END IF;
    IF EXISTS(SELECT 1 FROM marquee m JOIN fragment f ON f.id=m.fragment_id
              WHERE f.page_id IS NULL) THEN
        RAISE EXCEPTION '0029 Page-less Fragment owns a Marquee';
    END IF;
END $guard$;

ALTER TABLE fragment ADD COLUMN placement varchar(16);
ALTER TABLE fragment ADD COLUMN diary_id bigint;
-- Retire the old enum check before introducing TEXT, still within the transaction.
ALTER TABLE fragment DROP CONSTRAINT fragment_type_check;

-- Page-owned Fragments remain DATED; Diary identity is derived from their Page.
UPDATE fragment f SET placement='DATED', diary_id=p.diary_id
FROM page p WHERE p.id=f.page_id;

-- Explicitly approved nine annual editorial Fragments. Diary 1 spans
-- 1828, 1829 and January 1830; the other diaries are separate books.
WITH approved(fragment_id, diary_id, fragment_year) AS (
 VALUES (1::bigint,1::bigint,1828), (2,1,1828), (3,1,1828),
        (387,1,1829), (806,1,1830), (1177,3,1831),
        (1563,4,1832), (1564,4,1832), (1926,5,1834)
)
UPDATE fragment f SET placement='PREAMBLE', diary_id=a.diary_id
FROM approved a WHERE f.id=a.fragment_id AND f.year=a.fragment_year
  AND f.page_id IS NULL AND f.type IS NULL;

-- The two reviewed dated commentaries keep their complete HTML text.
UPDATE fragment SET page_id=1005, placement='DATED', diary_id=4
WHERE id=1738 AND year=1832 AND month=6 AND day=27 AND page_id IS NULL
  AND type='MARQUEE';
UPDATE fragment SET page_id=1078, placement='DATED', diary_id=5
WHERE id=2061 AND year=1834 AND month=5 AND day=14 AND page_id IS NULL
  AND type IS NULL;

-- Only after all ownerships are assigned convert the content type.
UPDATE fragment SET type='TEXT' WHERE type='MARQUEE' OR type IS NULL;

-- Protect against stale IDs, dates, relationships and incomplete backfill.
DO $validate$
DECLARE
    invalid_count bigint;
    preambles bigint;
BEGIN
    SELECT count(*) INTO invalid_count FROM fragment f
    LEFT JOIN page p ON p.id=f.page_id
    WHERE f.placement IS NULL OR f.type IS NULL OR f.diary_id IS NULL
       OR f.type NOT IN ('TEXT','IMAGE')
       OR f.placement NOT IN ('PREAMBLE','DATED','POSTAMBLE')
       OR (f.placement='DATED' AND
           (f.page_id IS NULL OR p.diary_id IS DISTINCT FROM f.diary_id))
       OR (f.placement IN ('PREAMBLE','POSTAMBLE') AND f.page_id IS NOT NULL)
       OR (f.placement IN ('PREAMBLE','POSTAMBLE') AND
            (f.month IS DISTINCT FROM 1 OR f.day IS DISTINCT FROM 1))
       OR (f.type='TEXT' AND f.image_id IS NOT NULL);
    IF invalid_count<>0 THEN
        RAISE EXCEPTION '0029 hybrid backfill validation failed for % rows',invalid_count;
    END IF;
    SELECT count(*) INTO preambles FROM fragment WHERE placement='PREAMBLE';
    IF preambles<>9 THEN
        RAISE EXCEPTION '0029 expected nine preambles, found %',preambles;
    END IF;
    IF EXISTS(SELECT 1 FROM fragment f JOIN marquee m ON m.fragment_id=f.id
              WHERE f.placement<>'DATED') THEN
        RAISE EXCEPTION '0029 annual Fragment has a Marquee';
    END IF;
END $validate$;

ALTER TABLE fragment
  ADD CONSTRAINT fragment_diary_fk FOREIGN KEY(diary_id) REFERENCES diary(id),
  ADD CONSTRAINT fragment_placement_check CHECK
    (placement IN ('PREAMBLE','DATED','POSTAMBLE')),
  ADD CONSTRAINT fragment_type_final_check CHECK(type IN ('TEXT','IMAGE')),
  ADD CONSTRAINT fragment_owner_check CHECK
    ((placement='DATED' AND page_id IS NOT NULL) OR
     (placement IN ('PREAMBLE','POSTAMBLE') AND page_id IS NULL));
ALTER TABLE fragment ALTER COLUMN type SET NOT NULL;
ALTER TABLE fragment ALTER COLUMN placement SET NOT NULL;
ALTER TABLE fragment ALTER COLUMN diary_id SET NOT NULL;
CREATE INDEX fragment_diary_year_placement_idx
 ON fragment(diary_id,year,placement,sequence,id);

-- Existing fragment_image_type_check only allows image_id when type=IMAGE.

SELECT placement, type, count(*) AS fragments FROM fragment
GROUP BY placement,type ORDER BY placement,type;
COMMIT;
