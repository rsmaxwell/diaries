-- Read-only structural fingerprint; no application data or sequence values.
SELECT jsonb_build_object(
 'table', (SELECT jsonb_build_object('kind',relkind,'persistence',relpersistence,
    'rowSecurity',relrowsecurity,'forceRowSecurity',relforcerowsecurity,
    'partition',relispartition,'options',reloptions,'tablespace',reltablespace)
    FROM pg_class WHERE oid='public.image'::regclass),
 'columns', (SELECT jsonb_agg(jsonb_build_object(
    'position',a.attnum,'name',a.attname,'type',format_type(a.atttypid,a.atttypmod),
    'notNull',a.attnotnull,'identity',a.attidentity,'generated',a.attgenerated,
    'default',pg_get_expr(d.adbin,d.adrelid),'collation',a.attcollation::regcollation::text)
    ORDER BY a.attnum)
    FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
    WHERE a.attrelid='public.image'::regclass AND a.attnum>0 AND NOT a.attisdropped),
 'droppedColumns', (SELECT count(*) FROM pg_attribute WHERE attrelid='public.image'::regclass AND attnum>0 AND attisdropped),
 'constraints', (SELECT jsonb_agg(jsonb_build_object(
    'name',conname,'type',contype,'definition',pg_get_constraintdef(oid),
    'validated',convalidated,'enforced',conenforced,'deferrable',condeferrable,'deferred',condeferred,
    'noInherit',connoinherit) ORDER BY conname)
    FROM pg_constraint WHERE conrelid='public.image'::regclass AND contype<>'n'),
 'invalidNotNullConstraints', (SELECT count(*) FROM pg_constraint WHERE conrelid='public.image'::regclass AND contype='n' AND (NOT convalidated OR NOT conenforced)),
 'indexes', (SELECT jsonb_agg(jsonb_build_object(
    'name',c.relname,'definition',pg_get_indexdef(i.indexrelid),
    'valid',i.indisvalid,'ready',i.indisready,'live',i.indislive,
    'unique',i.indisunique,'primary',i.indisprimary,'nullsNotDistinct',i.indnullsnotdistinct,
    'options',c.reloptions,'tablespace',c.reltablespace) ORDER BY c.relname)
    FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE i.indrelid='public.image'::regclass),
 'sequence', (SELECT jsonb_build_object('name',c.relname,'schema',c.relnamespace::regnamespace::text,'type',format_type(s.seqtypid,NULL),
    'start',s.seqstart,'increment',s.seqincrement,'min',s.seqmin,'max',s.seqmax,
    'cache',s.seqcache,'cycle',s.seqcycle,'persistence',c.relpersistence,
    'ownerMatchesTable',c.relowner=(SELECT relowner FROM pg_class WHERE oid='public.image'::regclass),
    'identityDependency',EXISTS(SELECT 1 FROM pg_depend d WHERE d.objid=c.oid
       AND d.refobjid='public.image'::regclass AND d.refobjsubid=1 AND d.deptype='i'))
    FROM pg_sequence s JOIN pg_class c ON c.oid=s.seqrelid
    WHERE s.seqrelid=to_regclass(pg_get_serial_sequence('public.image','id'))),
 'userTriggers', (SELECT count(*) FROM pg_trigger WHERE tgrelid='public.image'::regclass AND NOT tgisinternal),
 'policies', (SELECT count(*) FROM pg_policy WHERE polrelid='public.image'::regclass),
 'rules', (SELECT count(*) FROM pg_rewrite WHERE ev_class='public.image'::regclass),
 'inheritance', (SELECT count(*) FROM pg_inherits WHERE inhrelid='public.image'::regclass OR inhparent='public.image'::regclass)
) AS image_catalog_shape
\gset
