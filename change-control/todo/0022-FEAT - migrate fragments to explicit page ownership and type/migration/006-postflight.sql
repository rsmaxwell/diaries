\set ON_ERROR_STOP on

BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;

SELECT
    count(*) AS total_fragments,
    count(*) FILTER (WHERE page_id IS NOT NULL) AS with_page,
    count(*) FILTER (WHERE page_id IS NULL) AS without_page,
    count(*) FILTER (WHERE type = 'MARQUEE') AS typed_marquee,
    count(*) FILTER (WHERE type = 'IMAGE') AS typed_image,
    count(*) FILTER (WHERE type IS NULL) AS unclassified
FROM fragment;

SELECT f.id AS fragment_id, f.page_id AS fragment_page_id, m.id AS marquee_id,
       m.page_id AS marquee_page_id
FROM fragment f
JOIN marquee m ON m.fragment_id = f.id
WHERE f.page_id IS DISTINCT FROM m.page_id
ORDER BY f.id;

SELECT f.id AS fragment_id, f.page_id, f.type,
       CASE
           WHEN f.page_id IS NULL THEN 'page_id unresolved'
           WHEN f.type IS NULL THEN 'type awaiting review'
           WHEN f.type NOT IN ('MARQUEE', 'IMAGE') THEN 'invalid type'
       END AS problem
FROM fragment f
WHERE f.page_id IS NULL
   OR f.type IS NULL
   OR f.type NOT IN ('MARQUEE', 'IMAGE')
ORDER BY f.id;

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

SELECT conname, convalidated
FROM pg_constraint
WHERE conrelid = 'fragment'::regclass
  AND conname IN ('fragment_page_fk', 'fragment_type_check')
ORDER BY conname;

ROLLBACK;
