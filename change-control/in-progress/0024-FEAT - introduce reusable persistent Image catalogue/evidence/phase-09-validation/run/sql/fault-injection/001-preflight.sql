\set ON_ERROR_STOP on
\pset pager off
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL search_path = pg_catalog, public;
SET LOCAL TIME ZONE 'UTC';
SELECT current_database() AS database, inet_server_addr() AS server_address,
 inet_server_port() AS server_port, version() AS server_version,
 current_schema() AS current_schema, 'public' AS target_schema, clock_timestamp() AS executed_at,
 current_user AS application_user, session_user, current_setting('transaction_isolation') AS isolation,
 current_setting('transaction_read_only') AS read_only,
 current_setting('search_path') AS search_path;
SELECT datcollate,datctype,datlocprovider FROM pg_database WHERE datname=current_database();
SELECT collname,collprovider,collisdeterministic,collversion,
 pg_collation_actual_version(oid) AS actual_version
 FROM pg_collation WHERE oid='pg_catalog.pg_unicode_fast'::regcollation;
SELECT has_database_privilege(current_database(),'CONNECT') AS can_connect,
 has_schema_privilege('public','USAGE') AS schema_usage,
 has_schema_privilege('public','CREATE') AS can_create_table_sequence_indexes_constraints;
SELECT n.nspname,c.relname,c.relkind,pg_get_userbyid(c.relowner) AS owner
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE c.relname ILIKE '%image%' ORDER BY n.nspname,c.relname;
SELECT n.nspname,t.typname,t.typtype FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace
 WHERE t.typname ILIKE '%image%' ORDER BY n.nspname,t.typname;
\ir prerequisites.sql
\ir integrity.sql
\set preflight_integrity :integrity_snapshot
\set preflight_database :DBNAME
\set preflight_user :USER
ROLLBACK;
\set preflight_ok true
\echo 0024 PREFLIGHT PASS (read-only)
