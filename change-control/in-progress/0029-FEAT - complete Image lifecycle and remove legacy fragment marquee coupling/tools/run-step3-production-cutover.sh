#!/usr/bin/env bash
# 0029-FEAT: approved production cutover. Windows Cygwin Bash from Diaries parent root.
# IMPORTANT: failure leaves application writers stopped. Do not restart old responder after migration.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
EVIDENCE="$FEATURE/evidence/step-3-production-cutover"
HYBRID="$FEATURE/tools/step2-hybrid-schema-and-data.sql"
MARQUEE="$FEATURE/tools/step3-retire-marquee-page-id.sql"
mkdir -p "$EVIDENCE" || exit 1
STAMP=$(date -u +%Y%m%d-%H%M%S)
LOG="$EVIDENCE/production-cutover-$STAMP.log"
DUMP="$EVIDENCE/diaries-production-pre0029-$STAMP.dump"
(
  set -euo pipefail
  exec > >(tee "$LOG") 2>&1
  echo "0029 PRODUCTION CUTOVER START $(date -u +%FT%TZ)"
  echo "Windows backup: $DUMP"
  test -f .gitmodules && test -s "$HYBRID" && test -s "$MARQUEE" || { echo 'FAIL: run from Diaries parent checkout with 0029 SQL files'; exit 1; }
  for cmd in ssh docker sha256sum; do command -v "$cmd" >/dev/null || { echo "FAIL missing $cmd"; exit 1; }; done
  echo 'Migration inputs:'
  sha256sum "$HYBRID" "$MARQUEE"
  echo '=== STOP APPLICATION WRITERS: leave PostgreSQL and MQTT online ==='
  ssh -o BatchMode=yes pluto 'cd /home/richard/projects/diaries && docker compose --file compose.yaml --env-file .env stop diaries-responder diaries-client diaries-web'
  echo '=== RETAIN FRESH PRODUCTION DATABASE RECOVERY DUMP ==='
  ssh -o BatchMode=yes pluto 'docker exec diaries-postgres sh -c '"'"'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-acl'"'"'' > "$DUMP"
  test -s "$DUMP" || { echo 'FAIL: empty backup dump'; exit 1; }
  sha256sum "$DUMP" > "$DUMP.sha256"
  sha256sum -c "$DUMP.sha256"
  docker run --rm -i --network none postgres:18-alpine pg_restore --list < "$DUMP" > "$DUMP.toc"
  test -s "$DUMP.toc" || { echo 'FAIL: backup TOC unreadable'; exit 1; }
  echo "BACKUP PASS: $DUMP; catalogue $DUMP.toc"
  echo '=== MIGRATE 1: HYBRID FRAGMENT ==='
  ssh -o BatchMode=yes -T pluto 'docker exec -i diaries-postgres sh -c '"'"'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'"'"'' < "$HYBRID"
  echo 'MIGRATION 1 PASS'
  echo '=== MIGRATE 2: RETIRE MARQUEE PAGE_ID ==='
  ssh -o BatchMode=yes -T pluto 'docker exec -i diaries-postgres sh -c '"'"'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'"'"'' < "$MARQUEE"
  echo 'MIGRATION 2 PASS'
  echo '=== POST-MIGRATION DATABASE INTEGRITY ==='
  ssh -o BatchMode=yes -T pluto 'docker exec -i diaries-postgres sh -c '"'"'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At'"'"'' <<'SQL'
DO $verify$
BEGIN
 IF (SELECT count(*) FROM fragment) <> 2331 THEN RAISE EXCEPTION 'Fragment count mismatch'; END IF;
 IF (SELECT count(*) FROM marquee) <> 2270 THEN RAISE EXCEPTION 'Marquee count mismatch'; END IF;
 IF (SELECT count(*) FROM fragment WHERE placement='PREAMBLE') <> 9 THEN RAISE EXCEPTION 'PREAMBLE count mismatch'; END IF;
 IF (SELECT count(*) FROM fragment WHERE placement='DATED') <> 2322 THEN RAISE EXCEPTION 'DATED count mismatch'; END IF;
 IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='marquee' AND column_name='page_id') THEN RAISE EXCEPTION 'marquee.page_id still exists'; END IF;
 IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='placement') THEN RAISE EXCEPTION 'Fragment placement missing'; END IF;
 IF EXISTS (SELECT 1 FROM marquee m LEFT JOIN fragment f ON f.id=m.fragment_id WHERE f.id IS NULL OR f.placement <> 'DATED' OR f.page_id IS NULL) THEN RAISE EXCEPTION 'Bad Marquee owner'; END IF;
END $verify$;
SQL
  echo 'DATABASE INTEGRITY PASS'
  echo '=== DEPLOY PUBLISHED PLAYBOOKS TO PLUTO ==='
  ssh -o BatchMode=yes mango 'cd /home/richard/ansible-controller/playbooks && ANSIBLE_INVENTORY=/home/richard/ansible-controller/inventory/hosts ansible-playbook diaries.yaml --limit pluto --vault-password-file ~/.vault_pass.txt'
  echo 'ANSIBLE DEPLOYMENT PASS'
  echo '=== PRODUCTION CONTAINERS ==='
  ssh -o BatchMode=yes pluto 'docker ps --filter name=diaries --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"'
  echo '=== INSTALLED MQTT ANNUAL ACL ==='
  ssh -o BatchMode=yes pluto 'grep -n "diaries/years/#" /home/richard/projects/diaries/config/mosquitto/aclfile.txt'
  echo "CUTOVER COMMANDS COMPLETED $(date -u +%FT%TZ)"
  echo 'Production browser acceptance is still required before final closure.'
)
RC=$?
if test "$RC" -eq 0; then echo "PASS: cutover execution commands; log $LOG"; else
 echo "FAIL ($RC): cutover interrupted; KEEP WRITERS STOPPED if migration has begun. Do not restart old Responder. Log: $LOG"
 echo "Recovery dump (if created): $DUMP"
fi
exit "$RC"
