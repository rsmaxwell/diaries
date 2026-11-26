-- 0029 rollback for the *schema/data portion only*, not an application rollback.
-- Requires the pre-change database backup plus a coordinated responder, editor,
-- reader and MQTT rollback; NEVER apply to a live newer deployment in isolation.
-- The old 11 Page-less rows and their original null types are reconstructed
-- for the reviewed production baseline; unrelated later edits are prohibited.
BEGIN;
SET LOCAL lock_timeout='10s';
DO $guard$
BEGIN
  IF NOT EXISTS(SELECT 1 FROM information_schema.columns
     WHERE table_schema='public' AND table_name='fragment' AND column_name='placement') THEN
    RAISE EXCEPTION '0029 migration not present';
  END IF;
  IF EXISTS (SELECT 1 FROM fragment WHERE placement='POSTAMBLE') THEN
    RAISE EXCEPTION 'Cannot roll back: newer POSTAMBLE data exists';
  END IF;
  -- Restrict to the original migration footprint. Prefer restoring the
  -- verified database snapshot if later application edits have occurred.
  IF (SELECT count(*) FROM fragment WHERE placement='PREAMBLE')<>9 THEN
    RAISE EXCEPTION 'Preamble count drift; use reviewed backup restore';
  END IF;
END $guard$;
-- Restore the old schema's constraints and type nullability *before*
-- restoring legacy values. The forward migration enforces TEXT/IMAGE and
-- type NOT NULL; retaining either rule makes the rollback fail.
ALTER TABLE fragment DROP CONSTRAINT fragment_owner_check;
ALTER TABLE fragment DROP CONSTRAINT fragment_type_final_check;
ALTER TABLE fragment DROP CONSTRAINT fragment_placement_check;
ALTER TABLE fragment DROP CONSTRAINT fragment_diary_fk;
DROP INDEX fragment_diary_year_placement_idx;
ALTER TABLE fragment ALTER COLUMN type DROP NOT NULL;

-- Reconstruct only the reviewed pre-migration production-shaped rows.
UPDATE fragment SET type='MARQUEE' WHERE type='TEXT';
UPDATE fragment SET page_id=NULL WHERE id IN (1738,2061);
UPDATE fragment SET type=NULL WHERE id IN (1,2,3,387,806,1177,1563,1564,1926,2061);
ALTER TABLE fragment ADD CONSTRAINT fragment_type_check CHECK
 (type IS NULL OR type IN ('MARQUEE','IMAGE'));
ALTER TABLE fragment DROP COLUMN placement;
ALTER TABLE fragment DROP COLUMN diary_id;
COMMIT;
