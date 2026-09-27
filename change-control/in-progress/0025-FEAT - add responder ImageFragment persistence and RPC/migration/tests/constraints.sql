\set ON_ERROR_STOP on
BEGIN;
INSERT INTO public.image(id,relative_path,mime_type,original_filename,width,height,checksum)
VALUES (-25001,'0025-fixture.png','image/png','0025-fixture.png',1,1,repeat('a',64));
INSERT INTO public.fragment SELECT (jsonb_populate_record(NULL::public.fragment,
 to_jsonb(f)||jsonb_build_object('id',-25001,'type','IMAGE','image_id',NULL))).*
FROM public.fragment f ORDER BY id LIMIT 1;
DO $$ BEGIN
 IF NOT EXISTS (SELECT FROM public.fragment WHERE id=-25001) THEN RAISE EXCEPTION 'Fixture requires one baseline Fragment'; END IF;
 UPDATE public.fragment SET type='MARQUEE',image_id=NULL WHERE id=-25001;
 UPDATE public.fragment SET type='IMAGE',image_id=NULL WHERE id=-25001;
 UPDATE public.fragment SET type='IMAGE',image_id=-25001 WHERE id=-25001;
 BEGIN
   UPDATE public.fragment SET image_id=-25002 WHERE id=-25001;
   RAISE EXCEPTION 'Missing Image reference accepted';
 EXCEPTION WHEN foreign_key_violation THEN NULL; END;
 BEGIN
   UPDATE public.fragment SET type='MARQUEE' WHERE id=-25001;
   RAISE EXCEPTION 'MARQUEE reference accepted';
 EXCEPTION WHEN check_violation THEN NULL; END;
 BEGIN
   UPDATE public.fragment SET type=NULL WHERE id=-25001;
   RAISE EXCEPTION 'NULL type reference accepted';
 EXCEPTION WHEN check_violation THEN NULL; END;
 BEGIN
   DELETE FROM public.image WHERE id=-25001;
   RAISE EXCEPTION 'Referenced Image deletion accepted';
 EXCEPTION WHEN foreign_key_violation THEN NULL; END;
 DELETE FROM public.fragment WHERE id=-25001;
 IF NOT EXISTS (SELECT FROM public.image WHERE id=-25001) THEN RAISE EXCEPTION 'Fragment deletion cascaded to Image'; END IF;
END $$;
ROLLBACK;
\echo 0025 CONSTRAINT TESTS PASS (rolled back)
