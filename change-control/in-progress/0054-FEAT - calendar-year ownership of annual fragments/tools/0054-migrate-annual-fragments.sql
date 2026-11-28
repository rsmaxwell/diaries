-- 0054: Calendar-year ownership and EPILOGUE. Run with psql -X -v ON_ERROR_STOP=1 -1 -f.
-- Only execute after recording source inventory, database/files recovery point and application cutover plan.
-- Idempotent: already-migrated rows are unaffected; a second run validates the same constraints.
BEGIN;
SELECT pg_advisory_xact_lock(54, 20261127);
DO $$
BEGIN
 IF EXISTS (SELECT 1 FROM fragment WHERE placement NOT IN ('DATED','PREAMBLE','POSTAMBLE','EPILOGUE')) THEN
   RAISE EXCEPTION 'Unexpected fragment placement';
 END IF;
 IF EXISTS (SELECT 1 FROM fragment WHERE placement IN ('PREAMBLE','POSTAMBLE','EPILOGUE')
       AND (year IS NULL OR year NOT BETWEEN 1 AND 9999 OR page_id IS NOT NULL)) THEN
   RAISE EXCEPTION 'Invalid annual fragment ownership before migration';
 END IF;
 IF EXISTS (SELECT 1 FROM fragment WHERE placement = 'DATED'
       AND (diary_id IS NULL OR page_id IS NULL OR year IS NULL OR month IS NULL OR day IS NULL)) THEN
   RAISE EXCEPTION 'Invalid dated fragment ownership before migration';
 END IF;
END $$;
ALTER TABLE fragment DROP CONSTRAINT IF EXISTS fragment_owner_check;
ALTER TABLE fragment DROP CONSTRAINT IF EXISTS fragment_placement_check;
ALTER TABLE fragment ALTER COLUMN diary_id DROP NOT NULL;
UPDATE fragment SET placement = 'EPILOGUE' WHERE placement = 'POSTAMBLE';
UPDATE fragment SET diary_id = NULL, month = NULL, day = NULL
 WHERE placement IN ('PREAMBLE', 'EPILOGUE')
   AND (diary_id IS NOT NULL OR month IS NOT NULL OR day IS NOT NULL);
ALTER TABLE fragment ADD CONSTRAINT fragment_placement_check
 CHECK (placement IN ('DATED','PREAMBLE','EPILOGUE'));
ALTER TABLE fragment ADD CONSTRAINT fragment_owner_check
 CHECK ((placement = 'DATED' AND page_id IS NOT NULL AND diary_id IS NOT NULL
                      AND year IS NOT NULL AND month IS NOT NULL AND day IS NOT NULL)
     OR (placement IN ('PREAMBLE','EPILOGUE') AND year BETWEEN 1 AND 9999
                      AND page_id IS NULL AND diary_id IS NULL AND month IS NULL AND day IS NULL));
COMMIT;
