\set ON_ERROR_STOP on

\echo '0024 targeted production Image import: begin'

BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

LOCK TABLE public.image IN SHARE ROW EXCLUSIVE MODE;

DO $guard$
DECLARE
    actual_count bigint;
    actual_min_id bigint;
    actual_max_id bigint;
    actual_digest text;
    actual_sequence bigint;
    actual_sequence_called boolean;
BEGIN
    SELECT count(*), min(id), max(id),
           md5(jsonb_agg(to_jsonb(i) ORDER BY id)::text)
      INTO actual_count, actual_min_id, actual_max_id, actual_digest
      FROM public.image AS i;

    IF actual_count <> 71
       OR actual_min_id <> 1
       OR actual_max_id <> 71
       OR actual_digest <> '230067aaca271267faba1d1692c69d79' THEN
        RAISE EXCEPTION
            'Production Image precondition mismatch: count=%, min=%, max=%, digest=%',
            actual_count, actual_min_id, actual_max_id, actual_digest;
    END IF;

    SELECT last_value, is_called
      INTO actual_sequence, actual_sequence_called
      FROM public.image_id_seq;

    IF actual_sequence <> 71 OR NOT actual_sequence_called THEN
        RAISE EXCEPTION
            'Production Image sequence precondition mismatch: last_value=%, is_called=%',
            actual_sequence, actual_sequence_called;
    END IF;
END
$guard$;

INSERT INTO public.image
    (id, version, relative_path, mime_type, original_filename,
     width, height, checksum, caption, alt_text)
VALUES
    (72, 0, 'diary-1828-and-1829-and-jan-1830/images/img2885-image-baltic-map.png', 'image/png', 'img2885-image-baltic-map.png', 1852, 1076, '20aa37569ac2b4f962ed3e74b3e51b17f01b931ae516bcb7f10816f7e56b4d01', '', ''),
    (73, 0, 'diary-1828-and-1829-and-jan-1830/images/img2885-image-copenhagen-large-map.png', 'image/png', 'img2885-image-copenhagen-large-map.png', 1832, 1084, 'b729a3bab407829192cada11efaa037014fa93825689717a254e625efd01581b', '', ''),
    (74, 0, 'diary-1828-and-1829-and-jan-1830/images/img2885-image-copenhagen-map.png', 'image/png', 'img2885-image-copenhagen-map.png', 1849, 1084, '42ef8db9a0e6a84fbb727805aa7e179c5e7a8aa89228c23d4e9358ff9d237249', '', ''),
    (75, 0, 'diary-1828-and-1829-and-jan-1830/images/img2891-image-copenhagen-east.png', 'image/png', 'img2891-image-copenhagen-east.png', 1720, 1082, 'a75e829a447b054b108bc47dd46fcd380f8aa4ab07e6342e8de15df1dacfe075', '', ''),
    (76, 0, 'diary-1828-and-1829-and-jan-1830/images/img2892-image-baltic.png', 'image/png', 'img2892-image-baltic.png', 1710, 1065, 'cd0a4a5b1d066ff8ea0fdaa959cde758f8476c037844982a61c246b6d0fdb0d3', '', ''),
    (77, 0, 'diary-1828-and-1829-and-jan-1830/images/img2900-image-st-petersburg-map-large.png', 'image/png', 'img2900-image-st-petersburg-map-large.png', 1760, 966, '25a4eaed075620efed1f33d7c7fffbccbce92a06c17def03f0ebd8df33c13e45', '', ''),
    (78, 0, 'diary-1828-and-1829-and-jan-1830/images/img2900-image-st-petersburg-map.png', 'image/png', 'img2900-image-st-petersburg-map.png', 1757, 1082, 'ddabf0f09024690f6b0a434e2bdf7437ca055ace8928e199ac7ce6c0ca3d7945', '', ''),
    (79, 0, 'diary-1828-and-1829-and-jan-1830/images/img2900-st-petersburg-map-large.png', 'image/png', 'img2900-st-petersburg-map-large.png', 1760, 966, '4c554791a010b80370e0f5b0dbbf33607c4680ed445a606a73db1e7862b48bd5', '', ''),
    (80, 0, 'diary-1828-and-1829-and-jan-1830/images/img2920-image-map-london.png', 'image/png', 'img2920-image-map-london.png', 1846, 1090, '7f9c48beec78daa43c189ccc4b91c18568521ef77c87acde12086dc547951354', '', ''),
    (81, 0, 'diary-1828-and-1829-and-jan-1830/images/img2926-burnhopeside-hall.jpg', 'image/jpeg', 'img2926-burnhopeside-hall.jpg', 1024, 768, '176b69a1e56dd694db6bc94bc499cf541dc22500084566834a175ea2c21fbd1b', '', ''),
    (82, 0, 'diary-1831/images/img2761-brandon-white-house.png', 'image/png', 'img2761-brandon-white-house.png', 1887, 1082, '6eab0c712d2c38ed9fd6ed3d9a2f4f9cc841d1b533370edb2f2fcc2a9c2be29a', '', ''),
    (83, 0, 'diary-1831/images/img2762-north-shields-walk.png', 'image/png', 'img2762-north-shields-walk.png', 1916, 907, 'b5d68a29c08d96d35a344c5ea4c420426a8f9d7ff6646119a9b9e49cc3d1d971', '', '');

DO $verify_rows$
DECLARE
    inserted_count bigint;
    inserted_digest text;
    complete_count bigint;
    complete_digest text;
BEGIN
    SELECT count(*), md5(jsonb_agg(to_jsonb(i) ORDER BY id)::text)
      INTO inserted_count, inserted_digest
      FROM public.image AS i
     WHERE id BETWEEN 72 AND 83;

    IF inserted_count <> 12
       OR inserted_digest <> 'a60fd4ef85b4c2d7c2f1fbe180a2d04b' THEN
        RAISE EXCEPTION
            'Inserted Image verification mismatch: count=%, digest=%',
            inserted_count, inserted_digest;
    END IF;

    SELECT count(*), md5(jsonb_agg(to_jsonb(i) ORDER BY id)::text)
      INTO complete_count, complete_digest
      FROM public.image AS i;

    IF complete_count <> 83
       OR complete_digest <> 'a4e88f1911437b9ed31f98f9008de723' THEN
        RAISE EXCEPTION
            'Complete Image verification mismatch: count=%, digest=%',
            complete_count, complete_digest;
    END IF;
END
$verify_rows$;

SELECT pg_catalog.setval('public.image_id_seq'::regclass, 83, true);

DO $verify_sequence$
DECLARE
    actual_sequence bigint;
    actual_sequence_called boolean;
BEGIN
    SELECT last_value, is_called
      INTO actual_sequence, actual_sequence_called
      FROM public.image_id_seq;

    IF actual_sequence <> 83 OR NOT actual_sequence_called THEN
        RAISE EXCEPTION
            'Post-import Image sequence mismatch: last_value=%, is_called=%',
            actual_sequence, actual_sequence_called;
    END IF;
END
$verify_sequence$;

COMMIT;

\echo '0024 targeted production Image import: committed 12 rows'
