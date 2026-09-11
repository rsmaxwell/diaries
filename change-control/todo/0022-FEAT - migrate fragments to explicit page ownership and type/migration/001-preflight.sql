\set ON_ERROR_STOP on

BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;

SELECT 'fragment' AS entity, count(*) AS row_count FROM fragment
UNION ALL SELECT 'marquee', count(*) FROM marquee
UNION ALL SELECT 'page', count(*) FROM page
ORDER BY entity;

SELECT
    count(*) AS total_fragments,
    count(*) FILTER (WHERE relationships.marquee_count = 0) AS without_marquee,
    count(*) FILTER (WHERE relationships.marquee_count = 1) AS with_one_marquee,
    count(*) FILTER (WHERE relationships.marquee_count > 1) AS with_multiple_marquees
FROM (
    SELECT f.id, count(m.id) AS marquee_count
    FROM fragment f
    LEFT JOIN marquee m ON m.fragment_id = f.id
    GROUP BY f.id
) relationships;

SELECT f.id AS fragment_id, count(m.id) AS marquee_count
FROM fragment f
JOIN marquee m ON m.fragment_id = f.id
GROUP BY f.id
HAVING count(m.id) > 1
ORDER BY f.id;

SELECT
    m.id AS marquee_id,
    m.fragment_id,
    m.page_id,
    CASE
        WHEN f.id IS NULL THEN 'missing fragment'
        WHEN m.page_id IS NULL THEN 'null page_id'
        WHEN p.id IS NULL THEN 'missing page'
    END AS problem
FROM marquee m
LEFT JOIN fragment f ON f.id = m.fragment_id
LEFT JOIN page p ON p.id = m.page_id
WHERE f.id IS NULL OR m.page_id IS NULL OR p.id IS NULL
ORDER BY m.id;

SELECT
    id AS fragment_id,
    lock_user_id,
    lock_username,
    lock_timestamp,
    lock_session_id
FROM fragment
WHERE lock_user_id IS NOT NULL
   OR lock_session_id IS NOT NULL
   OR lock_timestamp IS NOT NULL
ORDER BY id;

-- Indicative only. The Java inventory utility performs the authoritative
-- tolerant HTML parse and records each img src value.
SELECT count(*) AS possible_embedded_image_fragments
FROM fragment
WHERE text ~* '<[[:space:]]*img([[:space:]>]|/>)';

SELECT
    count(*) AS fragment_count,
    md5(string_agg(
        concat_ws('|', id, version, year, month, day, sequence, md5(text),
                  lock_user_id, lock_username, lock_known_as,
                  lock_timestamp, lock_session_id),
        E'\n' ORDER BY id)) AS legacy_fragment_digest
FROM fragment;

SELECT
    count(*) AS marquee_count,
    md5(string_agg(
        concat_ws('|', id, version, page_id, fragment_id, x, y, width, height),
        E'\n' ORDER BY id)) AS legacy_marquee_digest
FROM marquee;

ROLLBACK;
