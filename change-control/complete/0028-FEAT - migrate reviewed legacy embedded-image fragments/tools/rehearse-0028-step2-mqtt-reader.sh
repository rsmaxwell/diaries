#!/usr/bin/env bash
# Disposable broker + responder retained replay + read-only Reader HTTP smoke.
# Run from Windows PC/Cygwin, from the Diaries parent checkout.
# The isolated already-migrated DB is the ONLY database contacted.
set -euo pipefail
on_exit() {
  local rc=$?
  trap - EXIT
  if (( rc != 0 )); then
    echo "FAIL: 0028 isolated MQTT/Reader rehearsal incomplete (exit $rc)" >&2
    echo 'Disposable containers/network and PRIVATE logs are retained for diagnosis.' >&2
    echo 'NO production migration, publication or deployment was attempted.' >&2
  fi
}
trap on_exit EXIT
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
manifest="$feature/evidence/Step 1/private/20261123T144651Z-reviewed-manifest-prepared"
rehearsal="$feature/evidence/Step 2/private/20261123T185712Z-isolated-db-rehearsal"
tools="$feature/tools"
label='uk.co.rsmaxwell.diaries.0028.isolated-rehearsal'
network='diaries-0028-replay-net'
broker='diaries-0028-replay-broker'
responder='diaries-0028-replay-responder'
reader='diaries-0028-replay-reader'
db='diaries-0028-rehearsal-db'
require() { "$@" || { echo "FAIL: $*" >&2; exit 1; }; }
# Resume only the HTTP acceptance checks after an already successful MQTT replay.
# No broker, responder, Reader, database or journal is rebuilt or reset.
if [[ "${1:-}" == '--resume-http' ]]; then
  [[ $# -eq 2 ]] || { echo 'Usage: <runner> --resume-http <previous-mqtt-reader-evidence>' >&2; exit 1; }
  exec bash "$tools/verify-0028-step2-reader-http.sh" "$2"
fi
[[ $# -eq 0 ]] || { echo 'Usage: <runner> [--resume-http <previous-evidence>]' >&2; exit 1; }
[[ -f .gitmodules && -d diaries-responder && -d diaries-web ]] || { echo 'FAIL: run from Diaries parent checkout' >&2; exit 1; }
for command in docker python3 git cygpath curl sha256sum date grep seq tail tr sleep; do
  command -v "$command" >/dev/null || { echo "FAIL: missing $command" >&2; exit 1; }
done
[[ -s "$manifest/0028-dispositions.csv" && -s "$rehearsal/RESULT.txt" && -d "$rehearsal/files-root" ]] || {
  echo 'FAIL: successful isolated database rehearsal inputs not found; do not restore or recreate database' >&2; exit 1;
}
grep -Fq 'PASS: restored PostgreSQL 18 rehearsal' "$rehearsal/RESULT.txt" || { echo 'FAIL: isolated database rehearsal not accepted' >&2; exit 1; }
if [[ -n "$(docker ps -a -q -f "name=^/${broker}$")" ||
      -n "$(docker ps -a -q -f "name=^/${responder}$")" ||
      -n "$(docker ps -a -q -f "name=^/${reader}$")" ]] || docker network inspect "$network" >/dev/null 2>&1; then
  echo 'FAIL: dedicated MQTT rehearsal containers/network already exist. Inspect evidence; do not overwrite.' >&2
  exit 1
fi
[[ -n "$(docker ps -q -f "name=^/${db}$")" ]] || { echo 'FAIL: isolated restored DB is not running' >&2; exit 1; }
actual_label=$(docker inspect --format "{{index .Config.Labels \"${label}\"}}" "$db")
[[ "$actual_label" == true ]] || { echo 'FAIL: DB label does not identify the 0028 isolated rehearsal' >&2; exit 1; }
[[ "$(docker inspect --format '{{.Config.Image}}' "$db")" == 'postgres:18-alpine' ]] || {
  echo 'FAIL: DB image does not match isolated PostgreSQL 18' >&2; exit 1;
}
docker inspect "$db" > /dev/null
# Confirm the restored DB is the expected local, independently labelled volume.
python3 - "$db" "$label" <<'PY_DB_ID'
import json, subprocess, sys
name,label=sys.argv[1:]
info=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
expected={'POSTGRES_DB=diaries_0028_rehearsal','POSTGRES_USER=postgres','POSTGRES_HOST_AUTH_METHOD=trust'}
if not expected.issubset(set(info['Config']['Env'])):raise SystemExit('FAIL: isolated DB environment identity mismatch')
if not any(m.get('Type')=='volume' and m.get('Name')=='diaries-0028-rehearsal-pgdata' for m in info['Mounts']):
    raise SystemExit('FAIL: isolated DB volume mismatch')
ports=(info['NetworkSettings']['Ports'] or {}).get('5432/tcp') or []
if len(ports)!=1 or ports[0].get('HostIp')!='127.0.0.1' or ports[0].get('HostPort')!='55428':
    raise SystemExit('FAIL: isolated DB port must remain localhost:55428')
print('PASS: isolated DB labels, volume, environment and localhost port verified')
PY_DB_ID
# Do not conflict with any already running development HTTP endpoints.
python3 - <<'PY_PORTS'
import socket
for port in (58081,58082):
    s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    try:s.bind(('127.0.0.1',port))
    except OSError as e:raise SystemExit(f'FAIL: localhost port {port} is busy: {e}')
    finally:s.close()
print('PASS: HTTP ports 58081/58082 are available on Windows')
PY_PORTS
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="$feature/evidence/Step 2/private/${stamp}-mqtt-reader-replay"
mkdir -p "$out"
out=$(cd "$out" && pwd -P)
manifest=$(cd "$manifest" && pwd -P)
rehearsal=$(cd "$rehearsal" && pwd -P)
repo=$(pwd -P)
echo "PRIVATE evidence: $out"
{
  date -u
  git branch --show-current;git rev-parse HEAD;git status --short
  git submodule status
  git -C diaries-responder status --short
  git -C diaries-web status --short
} > "$out/checkout.txt" 2>&1

# Verify the pre-existing converted DB and stable geometry; never take a new dump.
psql_isolated() { docker exec "$db" psql -X -A -t -v ON_ERROR_STOP=1 -U postgres -d diaries_0028_rehearsal -c "$1" | tr -d '\r'; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_source')" == 71 ]] || { echo 'FAIL: 71 source journal rows missing' >&2; exit 1; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_image_occurrence')" == 71 ]] || { echo 'FAIL: 71 occurrence journal rows missing' >&2; exit 1; }
[[ "$(psql_isolated 'select count(*) from public.fragment')" == 2331 ]] || { echo 'FAIL: isolated source fragment count changed' >&2; exit 1; }
marquee_before=$(psql_isolated "select md5(coalesce(string_agg(md5(row_to_json(m)::text),'' ORDER BY m.id),'')) from public.marquee m")
printf '%s\n' "$marquee_before" > "$out/marquee-before.md5"
media_win=$(cygpath -aw "$rehearsal/files-root")
[[ -d "$rehearsal/files-root" ]] || { echo 'FAIL: staged Files-root missing' >&2; exit 1; }
(cd "$manifest" && sha256sum -c SHA256SUMS.txt) | tee "$out/manifest-sha256.txt"
mkdir "$out/fixtures"
python3 "$repo/$tools/0028-replay-verify.py" generate --manifest "$manifest" --output "$out/fixtures" | tee "$out/fixtures.log"
mosquitto_conf_win=$(cygpath -aw "$out/fixtures/mosquitto.ISOLATED.conf")
responder_conf_win=$(cygpath -aw "$out/fixtures/responder.ISOLATED.PRIVATE.json")
reader_conf_win=$(cygpath -aw "$out/fixtures/reader.ISOLATED.PRIVATE.json")

# The private broker has *no published host MQTT port*. Do not connect production.
echo '=== Build runtime images from the current checkout (no publication) ==='
docker build -f diaries-responder/Dockerfile -t diaries-0028-replay-responder:local . > "$out/responder-build.log" 2>&1 || {
  tail -70 "$out/responder-build.log" >&2; exit 1;
}
docker build -f diaries-web/Dockerfile -t diaries-0028-replay-reader:local . > "$out/reader-build.log" 2>&1 || {
  tail -70 "$out/reader-build.log" >&2; exit 1;
}
echo 'PASS: locally built responder and Reader images; no registry push'

echo '=== Create disposable Docker bridge and isolated MQTT broker ==='
docker network create --label "${label}=true" --internal "$network" > "$out/network-id.txt"
# Network --internal blocks outbound routing; DB is only added to this new bridge.
docker network connect "$network" "$db"
docker run -d --name "$broker" --network "$network" --label "${label}=true" \
  --mount "type=bind,source=$mosquitto_conf_win,target=/mosquitto/config/mosquitto.conf,readonly" \
  eclipse-mosquitto:2 > "$out/broker-id.txt"
# Isolated bridge blocks outbound routing; only the two dedicated HTTP ports
# are published, on loopback only. No MQTT port is published.
for _ in $(seq 1 40); do
  if docker exec "$broker" mosquitto_pub -h 127.0.0.1 -t 0028/probe -m ready >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec "$broker" mosquitto_pub -h 127.0.0.1 -t 0028/probe -m ready

echo '=== Replay actual converted records through isolated responder ==='
docker run -d --name "$responder" --network "$network" --label "${label}=true" \
  -p 127.0.0.1:58081:8081 \
  --mount "type=bind,source=$responder_conf_win,target=/config/responder.json,readonly" \
  --mount "type=bind,source=$media_win,target=/data/files-root,readonly" \
  diaries-0028-replay-responder:local > "$out/responder-id.txt"
# MQTT retained publications are the startup sync. Wait for the image topics,
# without touching the existing development broker.
python3 - "$out/fixtures/EXPECTED.PRIVATE.json" "$out/retained-topic-args.txt" <<'PY_TOPICS'
import json,sys
items=json.load(open(sys.argv[1],encoding='utf-8'))
with open(sys.argv[2],'w',encoding='utf-8') as f:
    for x in items:f.write(f'diaries/fragments/{x["fragment_id"]}\n')
PY_TOPICS
mapfile -t topics < "$out/retained-topic-args.txt"
subargs=()
for topic in "${topics[@]}"; do subargs+=( -t "$topic" ); done
# Wait for responder sync to settle. Incomplete capture is a FAILED test.
for attempt in $(seq 1 36); do
  if ! docker ps -q -f "name=^/${responder}$" | grep -q .; then
    docker logs "$responder" > "$out/responder.log" 2>&1
    echo 'FAIL: isolated responder exited during MQTT startup' >&2; tail -60 "$out/responder.log" >&2;exit 1
  fi
  if docker exec "$broker" mosquitto_sub -h 127.0.0.1 -p 1883 -C 71 -W 4 \
      -F '%t|||%p' "${subargs[@]}" > "$out/retained-fragments.PRIVATE.txt" 2> "$out/mqtt-subscribe.log"; then
    if python3 "$repo/$tools/0028-replay-verify.py" validate-retained \
         --expected "$out/fixtures/EXPECTED.PRIVATE.json" --input "$out/retained-fragments.PRIVATE.txt" \
         > "$out/retained-validation.txt" 2>&1; then
      cat "$out/retained-validation.txt"
      break
    fi
  fi
  if (( attempt == 36 )); then
    docker logs "$responder" > "$out/responder.log" 2>&1
    echo 'FAIL: 71 retained MQTT fragments not valid after replay' >&2
    tail -60 "$out/responder.log" >&2
    cat "$out/retained-validation.txt" 2>/dev/null || true
    exit 1
  fi
  sleep 2
done


echo '=== Verify all 22 separately retained Marquee identities ==='
python3 - "$out/fixtures/EXPECTED-MARQUEES.PRIVATE.json" "$out/retained-marquee-args.txt" <<'PY_MARQUEES'
import json,sys
rows=json.load(open(sys.argv[1],encoding='utf-8'))
with open(sys.argv[2],'w',encoding='utf-8') as f:
    for x in rows:f.write(f'diaries/marquees/{x["marquee_id"]}\n')
PY_MARQUEES
mapfile -t mtops < "$out/retained-marquee-args.txt"
marquee_args=()
for topic in "${mtops[@]}"; do marquee_args+=( -t "$topic" ); done
for attempt in $(seq 1 12); do
  if docker exec "$broker" mosquitto_sub -h 127.0.0.1 -p 1883 -C 22 -W 4 \
       -F '%t|||%p' "${marquee_args[@]}" > "$out/retained-marquees.PRIVATE.txt" 2> "$out/marquee-subscribe.log"; then
    if python3 "$repo/$tools/0028-replay-verify.py" validate-marquees \
       --expected "$out/fixtures/EXPECTED-MARQUEES.PRIVATE.json" \
       --input "$out/retained-marquees.PRIVATE.txt" > "$out/marquee-validation.txt" 2>&1; then
      cat "$out/marquee-validation.txt"
      break
    fi
  fi
  if (( attempt == 12 )); then
    echo 'FAIL: reviewed Marquee MQTT topics missing or reassigned' >&2
    cat "$out/marquee-validation.txt" 2>/dev/null || true
    exit 1
  fi
  sleep 2
done

echo '=== Start real read-only Reader on the isolated broker ==='
docker run -d --name "$reader" --network "$network" --label "${label}=true" \
  -p 127.0.0.1:58082:8082 \
  -e DIARIES_WEB_MQTT_USERNAME='rehearsal-reader' \
  -e DIARIES_WEB_MQTT_PASSWORD='rehearsal-only-password' \
  --mount "type=bind,source=$reader_conf_win,target=/config/diaries-web.json,readonly" \
  diaries-0028-replay-reader:local > "$out/reader-id.txt"
# A Docker --internal-only bridge has no external default gateway: Docker 29
# does not activate -p host bindings. The HTTP proxy attaches to the internal
# bridge AND a small separate frontend bridge. The application containers stay
# internal-only, retaining network isolation from production and development.
bash "$repo/$tools/verify-0028-step2-reader-http.sh" "$out"
