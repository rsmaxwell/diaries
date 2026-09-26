\set ON_ERROR_STOP on

BEGIN;

LOCK TABLE public.image IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE public.fragment IN SHARE ROW EXCLUSIVE MODE;

DO $migration$
DECLARE
    image65 public.image%ROWTYPE;
    image68 public.image%ROWTYPE;
    fragment1461 public.fragment%ROWTYPE;
    affected integer;
    reference_count integer;
BEGIN
    SELECT * INTO STRICT image65 FROM public.image WHERE id = 65 FOR UPDATE;
    IF image65.version <> 0
       OR image65.relative_path <> 'diary-1831/images/img2805-blue-posts-pub.jpg'
       OR image65.original_filename <> 'img2805-blue-posts-pub.jpg'
       OR image65.mime_type <> 'image/png'
       OR image65.checksum <> '96280fb86ae716f9e58a807a785cafe1f98335cef3c8fe5c7a342ca37f965fa1'
       OR image65.width <> 1912
       OR image65.height <> 1079 THEN
        RAISE EXCEPTION 'Image 65 does not match the reviewed pre-correction state';
    END IF;

    SELECT * INTO STRICT image68 FROM public.image WHERE id = 68 FOR UPDATE;
    IF image68.version <> 0
       OR image68.relative_path <> 'diary-1832/images/img3018-murder-of-nicholas-fairles.png'
       OR image68.original_filename <> 'img3018-murder-of-nicholas-fairles.png'
       OR image68.mime_type <> 'image/jpeg'
       OR image68.checksum <> 'f25f78831f9630705e8d32a1a12550473ff759ced2e0c650e3172f70ab508a6d'
       OR image68.width <> 960
       OR image68.height <> 1707 THEN
        RAISE EXCEPTION 'Image 68 does not match the reviewed pre-correction state';
    END IF;

    IF EXISTS (
        SELECT 1 FROM public.image
        WHERE lower(relative_path) = lower('diary-1831/images/img2805-blue-posts-pub.png')
    ) THEN
        RAISE EXCEPTION 'The corrected Image 65 path is already catalogued';
    END IF;

    IF EXISTS (
        SELECT 1 FROM public.image
        WHERE lower(relative_path) = lower('diary-1832/images/img3018-murder-of-nicholas-fairles.jpg')
    ) THEN
        RAISE EXCEPTION 'The corrected Image 68 path is already catalogued';
    END IF;

    SELECT * INTO STRICT fragment1461 FROM public.fragment WHERE id = 1461 FOR UPDATE;
    IF fragment1461.version <> 0
       OR strpos(fragment1461.text, 'images/img2805-blue-posts-pub.jpg') = 0
       OR strpos(fragment1461.text, 'images/img2805-blue-posts-pub.png') <> 0 THEN
        RAISE EXCEPTION 'Fragment 1461 does not match the reviewed pre-correction state';
    END IF;

    SELECT count(*) INTO reference_count
    FROM public.fragment
    WHERE strpos(text, 'img2805-blue-posts-pub.jpg') > 0;
    IF reference_count <> 1 THEN
        RAISE EXCEPTION 'Expected one old img2805 reference, found %', reference_count;
    END IF;

    SELECT count(*) INTO reference_count
    FROM public.fragment
    WHERE strpos(text, 'img3018-murder-of-nicholas-fairles.png') > 0;
    IF reference_count <> 0 THEN
        RAISE EXCEPTION 'Expected no old img3018 references, found %', reference_count;
    END IF;

    UPDATE public.image
    SET version = version + 1,
        relative_path = 'diary-1831/images/img2805-blue-posts-pub.png',
        original_filename = 'img2805-blue-posts-pub.png'
    WHERE id = 65;
    GET DIAGNOSTICS affected = ROW_COUNT;
    IF affected <> 1 THEN
        RAISE EXCEPTION 'Expected to update Image 65 once, updated % rows', affected;
    END IF;

    UPDATE public.image
    SET version = version + 1,
        relative_path = 'diary-1832/images/img3018-murder-of-nicholas-fairles.jpg',
        original_filename = 'img3018-murder-of-nicholas-fairles.jpg'
    WHERE id = 68;
    GET DIAGNOSTICS affected = ROW_COUNT;
    IF affected <> 1 THEN
        RAISE EXCEPTION 'Expected to update Image 68 once, updated % rows', affected;
    END IF;

    UPDATE public.fragment
    SET version = version + 1,
        text = replace(text, 'images/img2805-blue-posts-pub.jpg', 'images/img2805-blue-posts-pub.png')
    WHERE id = 1461;
    GET DIAGNOSTICS affected = ROW_COUNT;
    IF affected <> 1 THEN
        RAISE EXCEPTION 'Expected to update Fragment 1461 once, updated % rows', affected;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.image
        WHERE id = 65
          AND version = 1
          AND relative_path = 'diary-1831/images/img2805-blue-posts-pub.png'
          AND original_filename = 'img2805-blue-posts-pub.png'
    ) OR NOT EXISTS (
        SELECT 1 FROM public.image
        WHERE id = 68
          AND version = 1
          AND relative_path = 'diary-1832/images/img3018-murder-of-nicholas-fairles.jpg'
          AND original_filename = 'img3018-murder-of-nicholas-fairles.jpg'
    ) OR NOT EXISTS (
        SELECT 1 FROM public.fragment
        WHERE id = 1461
          AND version = 1
          AND strpos(text, 'images/img2805-blue-posts-pub.jpg') = 0
          AND strpos(text, 'images/img2805-blue-posts-pub.png') > 0
    ) THEN
        RAISE EXCEPTION 'Post-correction verification failed';
    END IF;
END
$migration$;

COMMIT;

SELECT jsonb_pretty(jsonb_build_object(
    'schemaVersion', 1,
    'status', 'COMPLETED',
    'completedAtUtc', to_char(clock_timestamp() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
    'backup', jsonb_build_object(
        'filename', 'diaries-production-20260923-193936.sql',
        'sha256', 'a4a8757d47fe08b1fef374a503c274d376d38bbb9266c494382df6317e8a34c6'
    ),
    'before', jsonb_build_object(
        'images', jsonb_build_array(
            jsonb_build_object('id', 65, 'version', 0, 'relativePath', 'diary-1831/images/img2805-blue-posts-pub.jpg', 'originalFilename', 'img2805-blue-posts-pub.jpg'),
            jsonb_build_object('id', 68, 'version', 0, 'relativePath', 'diary-1832/images/img3018-murder-of-nicholas-fairles.png', 'originalFilename', 'img3018-murder-of-nicholas-fairles.png')
        ),
        'fragment1461Version', 0
    ),
    'after', jsonb_build_object(
        'images', (
            SELECT jsonb_agg(jsonb_build_object(
                'id', id,
                'version', version,
                'relativePath', relative_path,
                'originalFilename', original_filename,
                'mimeType', mime_type,
                'checksum', checksum,
                'width', width,
                'height', height
            ) ORDER BY id)
            FROM public.image
            WHERE id IN (65, 68)
        ),
        'fragment1461', (
            SELECT jsonb_build_object(
                'id', id,
                'version', version,
                'textMd5', md5(text),
                'oldReferenceCount', (length(text) - length(replace(text, 'img2805-blue-posts-pub.jpg', ''))) / length('img2805-blue-posts-pub.jpg'),
                'newReferenceCount', (length(text) - length(replace(text, 'img2805-blue-posts-pub.png', ''))) / length('img2805-blue-posts-pub.png')
            )
            FROM public.fragment
            WHERE id = 1461
        ),
        'fragment566', (
            SELECT jsonb_build_object('id', id, 'version', version, 'textMd5', md5(text))
            FROM public.fragment
            WHERE id = 566
        )
    )
));