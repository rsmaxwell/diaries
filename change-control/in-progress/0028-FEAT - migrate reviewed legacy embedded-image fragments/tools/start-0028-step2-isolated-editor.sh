#!/usr/bin/env bash
# Start isolated Angular Editor GUI on 127.0.0.1:58083 only.
# Reuses the successful 0028 migrated DB/MQTT/Reader/scan services unchanged.
# Run from Windows PC Cygwin, at Diaries parent repository root.
set -euo pipefail
on_exit() {
    local status=$?
    trap - EXIT
    if (( status != 0 )); then
        echo "FAIL: 0028 isolated Editor setup incomplete (exit ${status}); existing successful migration and Reader remain unchanged." >&2
        echo 'Any new labelled Editor containers and PRIVATE diagnostics are retained for inspection; do not blindly rerun start.' >&2
    fi
}
trap on_exit EXIT
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
tools="$feature/tools"
evidence="$feature/evidence/Step 2/private"
label='uk.co.rsmaxwell.diaries.0028.isolated-rehearsal'
backend='diaries-0028-replay-net'
frontend='diaries-0028-replay-http-front'
db='diaries-0028-rehearsal-db'
broker='diaries-0028-replay-broker'
responder='diaries-0028-replay-responder'
reader='diaries-0028-replay-reader'
scan='diaries-0028-replay-source-scans'
editor='diaries-0028-replay-editor'
bridge='diaries-0028-replay-editor-ws-bridge'
proxy='diaries-0028-replay-editor-proxy'
main_proxy='diaries-0028-replay-http-proxy'
fail() { echo "FAIL: $*" >&2; exit 1; }
for cmd in docker python3 git curl date; do command -v "$cmd" >/dev/null || fail "missing $cmd"; done
[[ $# -eq 0 ]] || fail 'Usage: bash <script> (no parameters)'
[[ -f .gitmodules && -f diaries-client/scripts/files/Dockerfile && -d diaries-responder ]] || fail 'Run at Diaries parent checkout root'
[[ -d "$evidence" ]] || fail 'Existing private 0028 evidence not found'
for name in "$editor" "$bridge" "$proxy"; do
  [[ -z "$(docker ps -a -q -f "name=^/${name}$")" ]] || fail "${name} exists; do not replace or duplicate. Run the verification script instead."
done
for name in "$db" "$broker" "$responder" "$reader" "$scan" "$main_proxy"; do
  [[ -n "$(docker ps -q -f "name=^/${name}$")" ]] || fail "Required isolated service not running: $name"
  [[ "$(docker inspect --format "{{index .Config.Labels \"${label}\"}}" "$name")" == true ]] || fail "Isolated service label mismatch: $name"
done
for network in "$backend" "$frontend"; do
  [[ "$(docker network inspect --format "{{index .Labels \"${label}\"}}" "$network")" == true ]] || fail "Network label mismatch: $network"
done
[[ "$(docker network inspect --format '{{.Internal}}' "$backend")" == true ]] || fail 'Backend network must remain internal'
[[ "$(docker network inspect --format '{{.Internal}}' "$frontend")" == false ]] || fail 'Frontend bridge must not be internal'
[[ "$(docker inspect --format '{{.Config.Image}}' "$db")" == 'postgres:18-alpine' ]] || fail 'Unexpected rehearsal DB image'
python3 - "$backend" "$frontend" "$db" "$broker" "$responder" "$reader" "$scan" "$main_proxy" <<'PY_GUARD'
import json,socket,subprocess,sys
backend,frontend,db,broker,responder,reader,scan,proxy=sys.argv[1:]
def inspect(name):return json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
for name in (broker,responder,reader,scan):
    info=inspect(name)
    nets=set(info['NetworkSettings']['Networks'])
    if nets!={backend}:raise SystemExit('FAIL: core isolated service network drift: %s %s'%(name,nets))
    if any(v for v in (info['NetworkSettings'].get('Ports') or {}).values()):
        raise SystemExit('FAIL: a core service unexpectedly exposes a host port: '+name)
info=inspect(db)
if backend not in info['NetworkSettings']['Networks'] or frontend in info['NetworkSettings']['Networks']:
    raise SystemExit('FAIL: isolated DB network drift')
if not any(m.get('Type')=='volume' and m.get('Name')=='diaries-0028-rehearsal-pgdata' for m in info['Mounts']):
    raise SystemExit('FAIL: isolated database volume identity drift')
ports=(info['NetworkSettings']['Ports'] or {}).get('5432/tcp') or []
if len(ports)!=1 or ports[0].get('HostIp')!='127.0.0.1' or ports[0].get('HostPort')!='55428':
    raise SystemExit('FAIL: isolated DB host port identity drift')
info=inspect(proxy)
if set(info['NetworkSettings']['Networks'])!={backend,frontend}:
    raise SystemExit('FAIL: previously verified Reader gateway network drift')
for internal,port in [('8081/tcp','58081'),('8082/tcp','58082')]:
    pb=(info['NetworkSettings'].get('Ports') or {}).get(internal) or []
    if len(pb)!=1 or pb[0].get('HostIp')!='127.0.0.1' or pb[0].get('HostPort')!=port:
        raise SystemExit('FAIL: existing Reader HTTP port changed')
s=socket.socket()
try:s.bind(('127.0.0.1',58083))
except OSError as err:raise SystemExit('FAIL: localhost Editor port 58083 already busy: %s'%err)
finally:s.close()
print('PASS: labelled backend/frontend, DB volume and ports, existing Reader gateway and Editor port verified')
PY_GUARD
psql_isolated() { docker exec "$db" psql -X -A -t -v ON_ERROR_STOP=1 -U postgres -d diaries_0028_rehearsal -c "$1" | tr -d '\r'; }
[[ "$(psql_isolated 'select count(*) from public.fragment')" == 2331 ]] || fail 'Rehearsal Fragment count differs from accepted 2331'
[[ "$(psql_isolated 'select count(*) from public.migration0028_source')" == 71 ]] || fail 'Migration source journal count differs from 71'
[[ "$(psql_isolated 'select count(*) from public.migration0028_image_occurrence')" == 71 ]] || fail 'Occurrence journal count differs from 71'
marquee_before=$(psql_isolated "select md5(coalesce(string_agg(md5(row_to_json(m)::text),'' ORDER BY m.id),'')) from public.marquee m")
[[ -n "$marquee_before" ]] || fail 'Could not fingerprint isolated Marquees'
curl --noproxy '*' --fail --silent --show-error --max-time 8 http://127.0.0.1:58082/health/ready >/dev/null || fail 'Previously accepted Reader is not healthy'
curl --noproxy '*' --fail --silent --show-error --max-time 8 -I \
  'http://127.0.0.1:58081/diaries/diary-1828-and-1829-and-jan-1830/img2840.jpg' >/dev/null || fail 'Original img2840 scan not available'
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="$evidence/${stamp}-isolated-editor-gui"
mkdir -p "$out"
out=$(cd "$out" && pwd -P)
{
  date -u
  git branch --show-current
  git rev-parse HEAD
  git status --short
  git submodule status
  git -C diaries-client status --short
  git -C diaries-responder status --short
} > "$out/checkout-and-submodule-state.txt" 2>&1
printf '%s\n' "$marquee_before" > "$out/marquee-before.md5"
{
  printf 'Fragments=2331\nMigrationSources=71\nMigrationOccurrences=71\n'
  printf 'DateUTC=%s\n' "$stamp"
} > "$out/before.txt"
# Rehearsal-only client settings. Never use shipped development/production
# broker endpoints or credentials. This file is PRIVATE evidence.
python3 - "$out/0028-editor-config.PRIVATE.json" <<'PY_CONFIG'
import json,sys
config={
 'brokerMode':'proxy','brokerProxyPath':'/mosquitto/',
 'responderBaseUrlMode':'same-origin',
 'username':'0028-isolated-client','password':'rehearsal-only',
 'diaries':'diaries','files':'files','clientId':'0028-isolated-editor',
 'keepalive':60,'reconnectPeriod':1000,'connectTimeout':30000,
 'protocolVersion':5,'clean':True,'fragmentLockTtlSeconds':900
}
with open(sys.argv[1],'w',encoding='utf-8') as f:json.dump(config,f,indent=2);f.write('\n')
PY_CONFIG
# Do not ask Docker Desktop to bind-mount a deep Windows project path: its
# long path sharing produced EIO for original page scans. Copy by stdin instead.
echo '=== Build dedicated Editor and WebSocket bridge Docker images from THIS checkout ==='
docker build --build-arg VERSION=0.0.9-0028-isolated-gui \
  -f diaries-client/scripts/files/Dockerfile -t diaries-0028-replay-editor:local diaries-client \
  > "$out/editor-build.log" 2>&1 || { tail -75 "$out/editor-build.log" >&2; fail 'Editor Docker build'; }
docker build -f "$tools/0028-editor-ws-bridge/Dockerfile" \
  -t diaries-0028-replay-editor-ws-bridge:local "$tools/0028-editor-ws-bridge" \
  > "$out/ws-bridge-build.log" 2>&1 || { tail -75 "$out/ws-bridge-build.log" >&2; fail 'WebSocket bridge Docker build'; }
echo 'PASS: locally built Angular Editor and binary MQTT WebSocket bridge; no registry publication'
# All application and broker services stay on the existing --internal bridge.
docker run -d --name "$bridge" --network "$backend" --label "${label}=true" \
  --cap-drop ALL --security-opt no-new-privileges --read-only \
  diaries-0028-replay-editor-ws-bridge:local > "$out/ws-bridge-id.txt"
docker run -d --name "$editor" --network "$backend" --label "${label}=true" \
  diaries-0028-replay-editor:local > "$out/editor-id.txt"
# Replace embedded app config inside disposable runtime container, not in Git.
docker exec -i "$editor" sh -c 'cat > /usr/share/nginx/html/diaries/assets/config.json' \
  < "$out/0028-editor-config.PRIVATE.json"
echo '=== Create Editor-only localhost HTTP proxy (leaves existing Reader gateway untouched) ==='
# Docker 29: publish on the NON-internal frontend at create time, then attach
# the backend BEFORE starting the container.
docker create --name "$proxy" --network "$frontend" --label "${label}=true" \
  -p 127.0.0.1:58083:8083 nginx:alpine > "$out/editor-proxy-id.txt"
docker network connect "$backend" "$proxy"
# docker cp works for stopped containers; no fragile Windows bind mount.
docker cp "$tools/0028-editor-isolated-gateway.conf" "$proxy:/etc/nginx/conf.d/default.conf"
docker start "$proxy" > "$out/editor-proxy-start.txt"
docker exec "$proxy" nginx -t > "$out/editor-proxy-nginx-check.log" 2>&1 || {
  cat "$out/editor-proxy-nginx-check.log" >&2; fail 'Editor gateway Nginx configuration';
}
# Nginx errors and failed bridge starts are reported with original diagnostics.
for attempt in {1..30}; do
  if curl --noproxy '*' --silent --fail --max-time 3 \
      'http://127.0.0.1:58083/diaries/assets/config.json' \
      > "$out/runtime-config-readback.PRIVATE.json"; then break; fi
  sleep 2
done
[[ -s "$out/runtime-config-readback.PRIVATE.json" ]] || {
  docker logs "$editor" >&2; docker logs "$proxy" >&2; fail 'Editor runtime configuration not available';
}
# Independent verification (and MQTT CONNECT smoke test) is read-only.
bash "$tools/verify-0028-step2-isolated-editor.sh" "$out"
cat > "$out/RESULT.txt" <<'RESULT'
PASS: 0028 isolated Angular Editor HTTP and MQTT-WebSocket infrastructure ready.
PASS: only 127.0.0.1:58083 is exposed for the new Editor gateway.
PASS: pre-existing migrated database, MQTT broker, Reader, scans and journals retained.
PENDING: manual authenticated Angular Editor visual acceptance and controlled GUI edit tests.
NO: production writes, production MQTT, deployment or image publication.
RESULT
printf '\nPASS: isolated Angular Editor preflight and network smoke completed\n'
echo 'Editor: http://127.0.0.1:58083/diaries/'
echo 'Reader: http://127.0.0.1:58082/'
echo "PRIVATE evidence: $out"
echo 'Do not close 0028 Step 2 until GUI acceptance evidence is reviewed.'
