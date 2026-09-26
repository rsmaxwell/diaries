\set ON_ERROR_STOP on

\echo 'Fragment 566 development-version correction: begin'

BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

LOCK TABLE public.fragment IN SHARE ROW EXCLUSIVE MODE;

DO $guard$
DECLARE
    fragment_count bigint;
    fragment_digest text;
    unaffected_count bigint;
    unaffected_digest text;
    current_version bigint;
    current_text_digest text;
    current_non_text_digest text;
BEGIN
    SELECT count(*),
           md5(coalesce(string_agg(to_jsonb(f)::text, E'\n'
                                   ORDER BY to_jsonb(f)::text), ''))
      INTO fragment_count, fragment_digest
      FROM public.fragment AS f;

    SELECT count(*),
           md5(coalesce(string_agg(to_jsonb(f)::text, E'\n'
                                   ORDER BY to_jsonb(f)::text), ''))
      INTO unaffected_count, unaffected_digest
      FROM public.fragment AS f
     WHERE id <> 566;

    SELECT version, md5(text), md5((to_jsonb(f) - 'version' - 'text')::text)
      INTO current_version, current_text_digest, current_non_text_digest
      FROM public.fragment AS f
     WHERE id = 566;

    IF fragment_count <> 2329
       OR fragment_digest <> '057dc426efd74ed3180aac2eb70b1d95'
       OR unaffected_count <> 2328
       OR unaffected_digest <> 'e6e36119bb148be76db105085166d78f'
       OR current_version <> 3
       OR current_text_digest <> '88028219b08dd39f500e7ede406e3949'
       OR current_non_text_digest <> '750ba4e3a7b2b6ce753593aa14ec5c0b' THEN
        RAISE EXCEPTION
            'Production Fragment precondition mismatch: count=%, digest=%, unaffected_count=%, unaffected_digest=%, version=%, text_digest=%, non_text_digest=%',
            fragment_count, fragment_digest, unaffected_count,
            unaffected_digest, current_version, current_text_digest,
            current_non_text_digest;
    END IF;
END
$guard$;

UPDATE public.fragment
   SET version = 2,
       text = convert_from(
           decode(
               'aW5wdXQvanNvbg0KPHA+QmV0d2VlbiAzICZhbXA7IDQgbydjbG9jayBmZWVsaW5nIG15IDxzcGFuIGNsYXNzPWhpZ2hsaWdodF95ZWxsb3c+Y29wcGVyczwvc3Bhbj4gdmVyeSBob3QgJmFtcDsgYSBtaWdodCBncmVhdCB0aGlyc3QgdXBvbiBtZSwgSSBnb3QgdXAgZm9yIGEgZHJpbmsgb2Ygd2F0ZXIuIEkgd2FzIG11Y2ggc3VycHJpc2VkIHRvIGZpbmQgdGhlIHNoaXAgdW5kZXIgd2F5ICZhbXA7IHJ1bm5pbmcgd2l0aCBhIGxpZ2h0IGJyZWV6ZSBhbmQgc3R1ZGRpbmcgLi4uPC9wPg0KDQpkYXRhYmFzZQ0KIjxwPkJldHdlZW4mbmJzcDszJm5ic3A7JmFtcDsmbmJzcDs0Jm5ic3A7byYjMzk7Y2xvY2smbmJzcDtmZWVsaW5nJm5ic3A7bXkmbmJzcDtjb3VnaCZuYnNwO3ZlcnkmbmJzcDtiYWQmbmJzcDsmYW1wOyZuYnNwO2EmbmJzcDttaWdodHkmbmJzcDtncmVhdCZuYnNwO3RoaXJzdCZuYnNwO3Vwb24mbmJzcDttZSwmbmJzcDtJJm5ic3A7Z290Jm5ic3A7dXAmbmJzcDtmb3ImbmJzcDthJm5ic3A7ZHJpbmsmbmJzcDtvZiZuYnNwO3dhdGVyJm5ic3A7JmFtcDsmbmJzcDt3YXMmbmJzcDttdWNoJm5ic3A7c3VycHJpc2VkJm5ic3A7dG8mbmJzcDtmaW5kJm5ic3A7dGhlJm5ic3A7c2hpcCZuYnNwO3VuZGVyJm5ic3A7d2F5Jm5ic3A7JmFtcDsmbmJzcDtydW5uaW5nJm5ic3A7d2l0aCZuYnNwO2EmbmJzcDtsaWdodCZuYnNwO2JyZWV6ZSZuYnNwO2FuZCZuYnNwO3Nsb3cmbmJzcDtnb2luZy48L3A+Ig==',
               'base64'),
           'UTF8')
 WHERE id = 566
   AND version = 3
   AND md5(text) = '88028219b08dd39f500e7ede406e3949';

DO $verify$
DECLARE
    fragment_count bigint;
    fragment_digest text;
    unaffected_count bigint;
    unaffected_digest text;
    selected_version bigint;
    selected_text_digest text;
    selected_non_text_digest text;
BEGIN
    SELECT count(*),
           md5(coalesce(string_agg(to_jsonb(f)::text, E'\n'
                                   ORDER BY to_jsonb(f)::text), ''))
      INTO fragment_count, fragment_digest
      FROM public.fragment AS f;

    SELECT count(*),
           md5(coalesce(string_agg(to_jsonb(f)::text, E'\n'
                                   ORDER BY to_jsonb(f)::text), ''))
      INTO unaffected_count, unaffected_digest
      FROM public.fragment AS f
     WHERE id <> 566;

    SELECT version, md5(text), md5((to_jsonb(f) - 'version' - 'text')::text)
      INTO selected_version, selected_text_digest, selected_non_text_digest
      FROM public.fragment AS f
     WHERE id = 566;

    IF fragment_count <> 2329
       OR fragment_digest <> '7469f2a48b59105ff619d695873632aa'
       OR unaffected_count <> 2328
       OR unaffected_digest <> 'e6e36119bb148be76db105085166d78f'
       OR selected_version <> 2
       OR selected_text_digest <> 'cb2269f86054079dbc29cf3eebb0d115'
       OR selected_non_text_digest <> '750ba4e3a7b2b6ce753593aa14ec5c0b' THEN
        RAISE EXCEPTION
            'Post-update Fragment verification mismatch: count=%, digest=%, unaffected_count=%, unaffected_digest=%, version=%, text_digest=%, non_text_digest=%',
            fragment_count, fragment_digest, unaffected_count,
            unaffected_digest, selected_version, selected_text_digest,
            selected_non_text_digest;
    END IF;
END
$verify$;

COMMIT;

\echo 'Fragment 566 development-version correction: committed one row'
