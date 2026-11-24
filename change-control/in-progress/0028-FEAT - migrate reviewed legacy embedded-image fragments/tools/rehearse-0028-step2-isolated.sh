#!/usr/bin/env bash
# 0028: isolated PostgreSQL 18 integration / failure-recovery rehearsal.
# Windows PC: run from the parent Diaries checkout in Cygwin Bash.
# Never changes the local development DB, production DB, MQTT, or Files source.
# A read-only pg_dump is taken from pluto; all SQL writes target a new Docker DB.
# This is a standalone Bash process (invoked using `bash script`). Unlike an
# outer `( ... ) && ... || ...` wrapper, its errexit setting is effective.
set -euo pipefail
on_exit() {
  local rc=$?
  trap - EXIT
  if (( rc != 0 )); then
    echo "FAIL: 0028 isolated rehearsal incomplete (exit $rc); DO NOT use production apply." >&2
    echo 'No 0028 migration apply is attempted unless media staging, DB identity and dry-run pass.' >&2
    echo 'Any existing labelled isolated Docker database and private evidence are retained.' >&2
  fi
}
trap on_exit EXIT

feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  tools="$feature/tools"
  manifest="$feature/evidence/Step 1/private/20261123T144651Z-reviewed-manifest-prepared"
  db_container='diaries-0028-rehearsal-db'
  db_volume='diaries-0028-rehearsal-pgdata'
  db_name='diaries_0028_rehearsal'
  db_port=55428
  label='uk.co.rsmaxwell.diaries.0028.isolated-rehearsal'
  resume_source=''
  if [[ "${1:-}" == '--resume-restored' && $# -eq 2 ]]; then
    resume_source="$2"
  elif (( $# != 0 )); then
    echo "FAIL: usage: bash <runner.sh> [--resume-restored <previous-private-evidence-dir>]" >&2
    exit 1
  fi

  [[ -f .gitmodules && -f "$tools/prepare-0028-rehearsal-fixtures.py" ]] || {
    echo 'FAIL: run from the Windows Diaries parent repository root with the latest ZIP applied' >&2; exit 1;
  }
  for dependency in docker ssh python3 sha256sum git cygpath tee tail grep diff tr seq sleep id; do
    command -v "$dependency" >/dev/null || { echo "FAIL: missing $dependency" >&2; exit 1; }
  done
  [[ -s "$manifest/0028-image-decisions.csv" && -s "$manifest/PREPARATION-RESULT.json" && -s "$manifest/SHA256SUMS.txt" ]] || {
    echo 'FAIL: approved Step 1 prepared manifest not found; do not regenerate without review' >&2; exit 1;
  }
  if [[ -z "$resume_source" ]]; then
    if [[ -n "$(docker ps -a -q -f "name=^/${db_container}$")" ]] || docker volume inspect "$db_volume" >/dev/null 2>&1; then
      echo "FAIL: reserved isolated container/volume already exists ($db_container / $db_volume)." >&2
      echo 'Preserve existing evidence; use --resume-restored only for a verified pre-mutation restore.' >&2
      exit 1
    fi
  fi

  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$feature/evidence/Step 2/private/${stamp}-isolated-db-rehearsal"
  mkdir -p "$out"
  out=$(cd "$out" && pwd -P)
  repo=$(pwd -P)
  manifest=$(cd "$manifest" && pwd -P)
  tool_py="$repo/$tools/prepare-0028-rehearsal-fixtures.py"
  media_py="$repo/$tools/stage-0028-rehearsal-media.py"
  if [[ -n "$resume_source" ]]; then
    [[ -d "$resume_source" ]] || { echo 'FAIL: previous evidence folder missing' >&2; exit 1; }
    resume_source=$(cd "$resume_source" && pwd -P)
    evidence_prefix="$repo/$feature/evidence/Step 2/private/"
    [[ "$resume_source" == "$evidence_prefix"* && "$resume_source" == *'-isolated-db-rehearsal' ]] || {
      echo 'FAIL: resume source is not an existing 0028 isolated rehearsal evidence folder' >&2; exit 1;
    }
    for required in production.READONLY.pgcustom production.READONLY.pgcustom.sha256 restore-counts.txt docker-identity.txt; do
      [[ -s "$resume_source/$required" ]] || { echo "FAIL: missing original restore evidence: $required" >&2; exit 1; }
    done
    # pg_restore is silent on success unless --verbose is used. Its redirected
    # log must exist, but a zero-byte log is legitimate and must not block resume.
    [[ -f "$resume_source/pg-restore.log" ]] || {
      echo 'FAIL: original restore log is missing: pg-restore.log' >&2; exit 1;
    }
    (cd "$resume_source" && sha256sum -c production.READONLY.pgcustom.sha256) | tee "$out/old-dump-sha256.log"
    printf 'Resuming restored isolated DB from evidence: %s\n' "$resume_source" | tee "$out/restore-origin.txt"
  fi
  journal_sql="$repo/diaries-responder/src/main/resources/migration0028/001-create-journal.sql"
  [[ -f "$journal_sql" ]] || { echo 'FAIL: current responder journal schema not found' >&2; exit 1; }

  {
    printf 'UTC: %s\n' "$stamp"
    echo 'Parent Git identity and changes:'
    git branch --show-current; git rev-parse HEAD; git status --short
    git submodule status
    echo 'Responder Git identity and changes:'
    git -C diaries-responder branch --show-current
    git -C diaries-responder rev-parse HEAD
    git -C diaries-responder status --short
  } > "$out/checkout.txt" 2>&1
  echo "Private evidence: $out"
  echo '=== Verify isolated rehearsal helper regression tests ==='
  python3 -m unittest discover -s "$repo/$feature/tests" -p 'test_step2_*rehearsal*.py' -v 2>&1 | tee "$out/helper-tests.log"
  echo '=== Verify prepared manifest file hashes ==='
  (cd "$manifest" && sha256sum -c SHA256SUMS.txt) | tee "$out/manifest-sha256.log"

  echo '=== Stage a checksum-verified, independent Files-root for reviewed Images ==='
  python3 "$media_py" --repo "$repo" --manifest "$manifest" --output-root "$out/files-root" \
    | tee "$out/media-copy.log"
  echo '=== Verify isolated PostgreSQL 18 identity before any migration writes ==='
  if [[ -z "$resume_source" ]]; then
    echo '=== Start a NEW, independently named and labelled PostgreSQL 18 instance ==='
    docker volume create --label "$label=true" "$db_volume" > "$out/docker-volume.txt"
    docker run -d --name "$db_container" \
      --label "$label=true" \
      --mount "source=$db_volume,target=/var/lib/postgresql" \
      -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_USER=postgres -e POSTGRES_DB="$db_name" \
      -p "127.0.0.1:${db_port}:5432" postgres:18-alpine > "$out/docker-container.txt"
  else
    [[ -n "$(docker ps -q -f "name=^/${db_container}$")" ]] || {
      echo 'FAIL: previously restored isolated Docker database is not running' >&2; exit 1;
    }
  fi
  for attempt in $(seq 1 75); do
    if docker exec "$db_container" pg_isready -U postgres -d "$db_name" >/dev/null 2>&1; then break; fi
    sleep 1
  done
  docker exec "$db_container" pg_isready -U postgres -d "$db_name" | tee "$out/db-ready.log"
  docker inspect "$db_container" > "$out/docker-inspect.PRIVATE.json"
  docker volume inspect "$db_volume" > "$out/docker-volume-inspect.PRIVATE.json"
  python3 - "$out/docker-inspect.PRIVATE.json" "$out/docker-volume-inspect.PRIVATE.json" "$label" "$db_volume" "$db_name" "$db_port" <<'PY_VERIFY_DOCKER'
import json, sys
c=json.load(open(sys.argv[1],encoding='utf-8'))[0]
v=json.load(open(sys.argv[2],encoding='utf-8'))[0]
label,volume,name,port=sys.argv[3:]
if v.get('Name')!=volume or (v.get('Labels') or {}).get(label)!='true':
    raise SystemExit('FAIL: Docker volume identity/label mismatch')
if (c['Config']['Labels'].get(label)!='true' or c['Config']['Image']!='postgres:18-alpine'
    or not c['State']['Running']):
    raise SystemExit('FAIL: Docker identity/image/running state mismatch')
if not any(m['Type']=='volume' and m['Name']==volume and m['Destination']=='/var/lib/postgresql'
           for m in c['Mounts']):
    raise SystemExit('FAIL: Docker volume mount does not match isolated rehearsal')
ports=c['NetworkSettings']['Ports'].get('5432/tcp') or []
if len(ports)!=1 or ports[0].get('HostIp')!='127.0.0.1' or ports[0].get('HostPort')!=port:
    raise SystemExit('FAIL: DB port is not exclusively bound to the approved localhost port')
env=c['Config']['Env']
for expected in ('POSTGRES_DB='+name,'POSTGRES_USER=postgres','POSTGRES_HOST_AUTH_METHOD=trust'):
    if expected not in env: raise SystemExit('FAIL: Docker DB configuration differs: '+expected)
print('PASS: isolated container label, image, volume, database and localhost-only port verified')
PY_VERIFY_DOCKER
  docker inspect -f '{{.Name}} {{.Config.Image}} {{json .HostConfig.PortBindings}}' "$db_container" > "$out/docker-identity.txt"

  psql_isolated() { docker exec -i "$db_container" psql -X -A -t -v ON_ERROR_STOP=1 -U postgres -d "$db_name" "$@"; }
  sql_scalar() { psql_isolated -c "$1" | tail -1 | tr -d '\r'; }
  if [[ -z "$resume_source" ]]; then
    # pg_dump is READ ONLY on pluto; archive stays within private 0028 evidence.
    echo '=== Read-only production pg_dump, without touching established backups ==='
    ssh pluto "docker exec diaries-postgres sh -c 'exec pg_dump -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -Fc --no-owner --no-acl'" \
      > "$out/production.READONLY.pgcustom"
    [[ -s "$out/production.READONLY.pgcustom" ]] || { echo 'FAIL: production dump is empty' >&2; exit 1; }
    (cd "$out" && sha256sum production.READONLY.pgcustom > production.READONLY.pgcustom.sha256)
    docker exec -i "$db_container" pg_restore --exit-on-error --no-owner --no-acl -U postgres -d "$db_name" \
      < "$out/production.READONLY.pgcustom" > "$out/pg-restore.log" 2>&1 || {
      echo 'FAIL: isolated pg_restore failed; last diagnostic lines:' >&2; tail -40 "$out/pg-restore.log" >&2; exit 1;
    }
    echo 'PASS: production dump restored only to the isolated container'
  else
    echo '=== Reuse already-restored isolated DB; NO new pg_dump or pg_restore ==='
    # Resume is permitted ONLY before journal installation or any conversion.
    # A touched rehearsal is preserved for investigation rather than retried blindly.
    [[ "$(sql_scalar "SELECT CASE WHEN to_regclass('public.migration0028_source') IS NULL THEN 'UNTOUCHED' ELSE 'TOUCHED' END")" == 'UNTOUCHED' ]] || {
      echo 'FAIL: migration journal already exists; this is not a pre-mutation restore' >&2; exit 1;
    }
    grep -Fq 'Restored fragment count: 2331' "$resume_source/restore-counts.txt" || {
      echo 'FAIL: recorded restore fragment count does not match expected receipt' >&2; exit 1;
    }
    echo 'PASS: restored rehearsal DB has no 0028 journal or migration activity'
  fi
  server_version=$(sql_scalar 'show server_version_num')
  [[ "$server_version" == 18* ]] || { echo "FAIL: isolated PostgreSQL is not v18 (got $server_version)" >&2; exit 1; }
  count=$(sql_scalar 'select count(*) from public.fragment')
  [[ "$count" == 2331 ]] || { echo "FAIL: restored fragment count not expected (got $count)" >&2; exit 1; }
  printf 'Restored fragment count: %s\n' "$count" | tee "$out/restore-counts.txt"

  echo '=== Generate isolated-only responder config ==='
  python3 "$tool_py" config --files-root "$out/files-root" --windows-root "$(cygpath -aw "$out")" \
      --port "$db_port" --output "$out/REHEARSAL-ONLY-config.PRIVATE.json"
  java_task() {
    local mode="$1" name="$2"; shift 2
    local -a cmd=(./gradlew --no-daemon :diaries-responder:migration0028ReviewedFragments
      "-PmigrationMode=$mode" "-PmigrationManifest=$(cygpath -aw "$manifest")"
      "-PmigrationConfig=$(cygpath -aw "$out/REHEARSAL-ONLY-config.PRIVATE.json")"
      "-PmigrationOutput=$(cygpath -aw "$out/$name")")
    cmd+=("$@")
    "${cmd[@]}" 2>&1 | tee "$out/$name.gradle.log"
  }
  echo '=== Live restored-source analysis and deterministic dry-run (NO DB WRITES) ==='
  java_task analyse analysis
  java_task dry-run dry-run
  plan="$out/dry-run/0028-reviewed-dry-run-plan.json"
  [[ -s "$plan" ]] || { echo 'FAIL: no dry-run plan produced' >&2; exit 1; }
  python3 "$tool_py" fixtures --plan "$plan" --dir "$out"
  python3 "$tool_py" approval --plan "$plan" --operator "$(id -un)" --output "$out/APPROVAL-REHEARSAL-ONLY.PRIVATE.json"
  approval="$out/APPROVAL-REHEARSAL-ONLY.PRIVATE.json"
  (cd "$out" && sha256sum dry-run/0028-reviewed-dry-run-plan.json > dry-run-plan.sha256)

  echo '=== Capture all unrelated Fragment, Page, Image and Marquee fingerprints ==='
  psql_isolated -f - < "$out/unrelated-fingerprints.sql" > "$out/before-fingerprints.txt"
  echo '=== Install 0028 schema ONLY in the isolated database ==='
  psql_isolated -f - < "$journal_sql" > "$out/schema-install.log"
  [[ "$(sql_scalar 'select count(*) from public.migration0028_source')" == 0 ]] || {
    echo 'FAIL: migration journal not initially empty' >&2; exit 1;
  }

  echo '=== Negative test: deliberately wrong approval must prevent all database writes ==='
  python3 - "$approval" "$out/INVALID-approval.PRIVATE.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
p['plan_sha256']='0'*64
with open(sys.argv[2],'w',encoding='utf-8') as f: json.dump(p,f,indent=2)
PY
  if java_task apply invalid-approval \
      "-PmigrationPlan=$(cygpath -aw "$plan")" \
      "-PmigrationApproval=$(cygpath -aw "$out/INVALID-approval.PRIVATE.json")"; then
    echo 'FAIL: invalid approval was accepted' >&2; exit 1
  fi
  [[ "$(sql_scalar 'select count(*) from public.migration0028_source')" == 0 ]] || {
    echo 'FAIL: invalid approval changed isolated database' >&2; exit 1;
  }
  echo 'PASS: wrong approval rejected, no journalled conversions'

  echo '=== Inject a failure within a multi-row date to prove transaction rollback ==='
  psql_isolated -f - < "$out/inject-failure.sql" > "$out/inject-install.log"
  if java_task apply injected-failure \
      "-PmigrationPlan=$(cygpath -aw "$plan")" \
      "-PmigrationApproval=$(cygpath -aw "$approval")"; then
    echo 'FAIL: injected database error did not stop migration' >&2; exit 1
  fi
  if ! grep -Fq '0028_REHEARSAL_INJECTED_FAILURE' "$out/injected-failure.gradle.log"; then
    echo 'FAIL: apply failed for a reason other than the deliberate injected error' >&2; exit 1
  fi
  expected_before=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["earlierCommittedExpected"])' "$out/INJECTION-PARAMETERS.json")
  actual_before=$(sql_scalar 'select count(*) from public.migration0028_source')
  [[ "$actual_before" == "$expected_before" ]] || {
    echo "FAIL: expected $expected_before earlier committed dates, got $actual_before rows" >&2; exit 1;
  }
  failed_ids=$(python3 -c 'import json,sys;print(",".join(map(str,json.load(open(sys.argv[1]))["failedDateFragments"])))' "$out/INJECTION-PARAMETERS.json")
  failed_journal=$(sql_scalar "select count(*) from public.migration0028_source where fragment_id=ANY(ARRAY[$failed_ids]::bigint[])")
  failed_original=$(sql_scalar "select count(*) from public.fragment where id=ANY(ARRAY[$failed_ids]::bigint[]) and image_id IS NULL")
  failed_count=$(python3 -c 'import json,sys;print(len(json.load(open(sys.argv[1]))["failedDateFragments"]))' "$out/INJECTION-PARAMETERS.json")
  [[ "$failed_journal" == 0 && "$failed_original" == "$failed_count" ]] || {
    echo 'FAIL: injected date transaction was not fully rolled back' >&2; exit 1;
  }
  printf 'PASS: failure rolled back entire date; %s earlier commits preserved\n' "$actual_before" | tee "$out/rollback-result.txt"

  echo '=== Remove ONLY the isolated fault fixture, then resume migration ==='
  psql_isolated -f - < "$out/remove-failure.sql" > "$out/inject-remove.log"
  java_task apply resume-apply \
      "-PmigrationPlan=$(cygpath -aw "$plan")" \
      "-PmigrationApproval=$(cygpath -aw "$approval")"
  [[ "$(sql_scalar 'select count(*) from public.migration0028_source')" == 71 ]] || {
    echo 'FAIL: resume did not commit all 71 reviewed conversions' >&2; exit 1;
  }
  echo '=== Independently verify journal and idempotence ==='
  java_task postflight postflight \
      "-PmigrationPlan=$(cygpath -aw "$plan")"
  java_task apply idempotence-apply \
      "-PmigrationPlan=$(cygpath -aw "$plan")" \
      "-PmigrationApproval=$(cygpath -aw "$approval")"
  [[ "$(sql_scalar 'select count(*) from public.migration0028_source')" == 71 ]] || { echo 'FAIL: idempotence journal count changed' >&2; exit 1; }
  [[ "$(sql_scalar 'select count(*) from public.migration0028_image_occurrence')" == 71 ]] || { echo 'FAIL: occurrence journal count differs' >&2; exit 1; }
  psql_isolated -f - < "$out/unrelated-fingerprints.sql" > "$out/after-fingerprints.txt"
  if ! diff -u "$out/before-fingerprints.txt" "$out/after-fingerprints.txt" > "$out/unrelated-diff.txt"; then
    echo 'FAIL: unrelated Fragments, Images, Pages or Marquees changed' >&2
    cat "$out/unrelated-diff.txt" >&2
    exit 1
  fi

  cat > "$out/RESULT.txt" <<RESULT
PASS: restored PostgreSQL 18 rehearsal of reviewed 71 conversions and 1 DEFER.
PASS: 71 reviewed media checksums (deduplicated to unique files), isolated Files-root.
PASS: source analyse and dry-run before writes.
PASS: invalid approval rejected without mutation.
PASS: induced date transaction rollback and persisted earlier commits.
PASS: restart-safe apply, postflight, idempotence; 71 source and 71 occurrence journals.
PASS: all unrelated Fragment, Page, Image and Marquee fingerprints unchanged.
NO production writes, MQTT publications or production deployment.
MQTT retained-topic replay and editor/reader acceptance are NOT tested here.
Isolated Docker database retained: ${db_container} / volume ${db_volume} / host port ${db_port}.
RESULT
  cat "$out/RESULT.txt"
  echo 'PASS: 0028 isolated Step 2 database integration rehearsal completed'
