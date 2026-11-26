-- 0029-FEAT / Step 1A: classify the 22 verified legacy Marquee fragments.
-- Development DB only. No deletion and no constraint changes.
-- Fails and rolls back unless the precise 22-record set is still eligible.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE TEMP TABLE expected_0029_fragment_ids (id bigint PRIMARY KEY) ON COMMIT DROP;
INSERT INTO expected_0029_fragment_ids(id)
SELECT unnest(ARRAY[1251, 1253, 1262, 1269, 1276, 1279, 1288, 1296, 1315, 1321, 1373, 1375, 1392, 1397, 1398, 1416, 1419, 1420, 1438, 1443, 1460, 1461]::bigint[]);

-- Lock the target rows, so their checked state cannot change mid-transaction.
SELECT f.id, f.page_id, f.type, m.id AS marquee_id, m.page_id AS marquee_page_id, f.version
FROM fragment f
JOIN expected_0029_fragment_ids e ON e.id=f.id
LEFT JOIN marquee m ON m.fragment_id=f.id
ORDER BY f.id FOR UPDATE OF f;

DO $guard$
DECLARE eligible_count integer;
DECLARE actual_null_with_marquee integer;
BEGIN
  SELECT count(*) INTO eligible_count
  FROM expected_0029_fragment_ids e
  JOIN fragment f ON f.id=e.id
  JOIN marquee m ON m.fragment_id=f.id
  WHERE f.type IS NULL AND f.page_id IS NOT NULL
    AND m.page_id=f.page_id AND f.image_id IS NULL;

  SELECT count(*) INTO actual_null_with_marquee
  FROM fragment f JOIN marquee m ON m.fragment_id=f.id
  WHERE f.type IS NULL;

  IF eligible_count <> 22 OR actual_null_with_marquee <> 22 THEN
    RAISE EXCEPTION '0029 precondition failed: eligible expected=%, total untyped with marquee=% (both must equal 22)', eligible_count, actual_null_with_marquee;
  END IF;
END $guard$;

-- Bump optimistic-lock version to avoid silently overwriting stale state.
UPDATE fragment f
SET type='MARQUEE', version=f.version+1
FROM expected_0029_fragment_ids e
WHERE f.id=e.id AND f.type IS NULL
RETURNING f.id, f.page_id, f.type, f.version;

DO $check$
DECLARE fixed integer;
DECLARE remaining integer;
BEGIN
  SELECT count(*) INTO fixed FROM fragment f JOIN expected_0029_fragment_ids e ON e.id=f.id WHERE f.type='MARQUEE';
  SELECT count(*) INTO remaining FROM fragment f JOIN marquee m ON m.fragment_id=f.id WHERE f.type IS NULL;
  IF fixed <> 22 OR remaining <> 0 THEN
    RAISE EXCEPTION '0029 postcondition failed: fixed=%, remaining untyped with marquee=%', fixed, remaining;
  END IF;
END $check$;
COMMIT;

SELECT f.id, f.type, f.page_id, m.id AS marquee_id, m.page_id AS marquee_page_id, f.version
FROM fragment f JOIN marquee m ON m.fragment_id=f.id
WHERE f.id IN (1251, 1253, 1262, 1269, 1276, 1279, 1288, 1296, 1315, 1321, 1373, 1375, 1392, 1397, 1398, 1416, 1419, 1420, 1438, 1443, 1460, 1461)
ORDER BY f.id;
