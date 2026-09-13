\set ON_ERROR_STOP on
BEGIN;
INSERT INTO public.image(relative_path,mime_type,original_filename,width,height,checksum)
 VALUES ('Test/Photo.JPG','image/jpeg','Photo.JPG',1,2,repeat('a',64)),
        ('Other/Photo.JPG','image/jpeg','Photo.JPG',1,2,repeat('a',64)),
        ('Unicode/CAFÉ.PNG','image/png','CAFÉ.PNG',1,2,repeat('b',64));
DO $$
DECLARE r record; actual_state text; command text;
BEGIN
 IF (SELECT count(*) FROM public.image WHERE version=0 AND caption='' AND alt_text='' AND id>0) <> 3 THEN
    RAISE EXCEPTION 'Identity/defaults or duplicate-checksum support failed';
 END IF;
 FOR r IN SELECT * FROM (VALUES
    ('case alias', 'test/photo.jpg', 'image/jpeg', '1', '2', '0', repeat('a',64), '23505'),
    ('Unicode case alias', 'unicode/café.png', 'image/png', '1', '2', '0', repeat('a',64), '23505'),
    ('MIME', 'invalid-mime', 'text/plain', '1', '2', '0', repeat('a',64), '23514'),
    ('width', 'invalid-width', 'image/png', '0', '2', '0', repeat('a',64), '23514'),
    ('height', 'invalid-height', 'image/png', '1', '-1', '0', repeat('a',64), '23514'),
    ('version', 'invalid-version', 'image/png', '1', '2', '-1', repeat('a',64), '23514'),
    ('uppercase checksum', 'invalid-hash-upper', 'image/png', '1', '2', '0', repeat('A',64), '23514'),
    ('nonhex checksum', 'invalid-hash-hex', 'image/png', '1', '2', '0', repeat('g',64), '23514'),
    ('short checksum', 'invalid-hash-short', 'image/png', '1', '2', '0', 'abc', '23514'),
    ('null checksum', 'invalid-hash-null', 'image/png', '1', '2', '0', NULL, '23502'),
    ('null MIME', 'invalid-mime-null', NULL, '1', '2', '0', repeat('a',64), '23502'),
    ('null path', NULL, 'image/png', '1', '2', '0', repeat('a',64), '23502')
 ) v(label,path,mime,width,height,version,checksum,expected_state)
 LOOP
    actual_state := NULL;
    command := format('INSERT INTO public.image(relative_path,mime_type,original_filename,width,height,version,checksum) VALUES (%L,%L,%L,%s,%s,%s,%L)',
       r.path,r.mime,'fixture',r.width,r.height,r.version,r.checksum);
    BEGIN EXECUTE command;
    EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE;
    END;
    IF actual_state IS DISTINCT FROM r.expected_state THEN
       RAISE EXCEPTION 'Test %: expected %, got %',r.label,r.expected_state,actual_state;
    END IF;
 END LOOP;
 IF (SELECT relative_path FROM public.image WHERE relative_path='Test/Photo.JPG') IS DISTINCT FROM 'Test/Photo.JPG' THEN
    RAISE EXCEPTION 'Stored path case was not preserved';
 END IF;
END $$;
ROLLBACK;
\echo PASS identity/defaults, duplicate checksum, ASCII/Unicode uniqueness and 12 invalid-row cases
