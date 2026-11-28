-- Read-only inventory to capture with psql before migration (save stdout in evidence/step-2).
BEGIN READ ONLY;
SELECT id, version, year, month, day, diary_id, page_id, placement,
       type, sequence, image_id, image_link_url, lock_user_id,
       lock_username, lock_known_as, lock_timestamp, lock_session_id
FROM fragment WHERE placement IN ('PREAMBLE','POSTAMBLE','EPILOGUE')
ORDER BY year, placement, sequence, id;
SELECT placement, count(*) FROM fragment GROUP BY placement ORDER BY placement;
COMMIT;
