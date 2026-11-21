#!/usr/bin/env bash
# 0051 Step 1 read-only baseline executed on pluto via:
#   ssh pluto 'bash -s' < path/to/this/script > private/live-production-baseline.log 2>&1
# No remote files written, services restarted, migrations performed or secrets dumped.
# This runs under a separate non-interactive Bash process, not an interactive shell.
set -euo pipefail

echo "0051 STEP 1 READ-ONLY LIVE PRODUCTION BASELINE"
date -u '+captured_utc=%Y-%m-%dT%H:%M:%SZ'
hostname

echo '== Running component names, configured image tags, image IDs and health =='
docker inspect --format '{{.Name}} image={{.Config.Image}} image_id={{.Image}} status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' diaries-responder diaries-client diaries-web diaries-postgres diaries-mosquitto

echo '== Responder current authoring gate (boolean line only) =='
# Do not emit any adjacent JSON secrets.
if ! docker exec diaries-responder sh -c 'grep -E "^[[:space:]]*\"imageFragmentWritesEnabled\"[[:space:]]*:" /config/responder.json' ; then
  echo 'WARN: imageFragmentWritesEnabled not found at /config/responder.json'
fi

echo '== PostgreSQL fragment and marquee schema (read-only transaction) =='
docker exec -i diaries-postgres sh -c 'export PGPASSWORD="${POSTGRES_PASSWORD:-}"; exec psql -X -v ON_ERROR_STOP=1 -P pager=off -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<'SQL'
BEGIN READ ONLY;
SELECT table_name, ordinal_position, column_name, data_type,
       character_maximum_length, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name IN ('fragment', 'marquee')
ORDER BY table_name, ordinal_position;
SELECT c.relname AS table_name, con.conname AS constraint_name,
       con.contype AS constraint_type, pg_get_constraintdef(con.oid) AS definition
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relname IN ('fragment', 'marquee')
ORDER BY c.relname, con.conname;
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public' AND tablename IN ('fragment', 'marquee')
ORDER BY tablename, indexname;
ROLLBACK;
SQL

echo '0051 STEP 1 READ-ONLY BASELINE COMPLETE'
