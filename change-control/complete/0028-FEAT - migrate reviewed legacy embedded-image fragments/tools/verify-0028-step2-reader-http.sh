#!/usr/bin/env bash
# 0028-FEAT: resume ONLY the isolated Reader HTTP checks after successful MQTT replay.
# Existing Reader/responder/broker/DB containers must stay on internal bridge only.
# The sole dual-homed service is a labelled nginx reverse proxy with localhost-only ports.
# Windows PC / Cygwin; run from Diaries parent checkout.
set -euo pipefail
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
label='uk.co.rsmaxwell.diaries.0028.isolated-rehearsal'
backend='diaries-0028-replay-net'
frontend='diaries-0028-replay-http-front'
proxy='diaries-0028-replay-http-proxy'
broker='diaries-0028-replay-broker'
responder='diaries-0028-replay-responder'
reader='diaries-0028-replay-reader'
db='diaries-0028-rehearsal-db'
for command in docker python3 cygpath curl sha256sum grep date; do
    command -v "$command" >/dev/null || { echo "FAIL: missing $command" >&2; exit 1; }
done
[[ $# -eq 1 && -d "$1" ]] || { echo 'Usage: <http-script> <previous-mqtt-reader-evidence>' >&2; exit 1; }
[[ -f .gitmodules && -d diaries-responder && -d diaries-web ]] || { echo 'FAIL: must run from Diaries parent root' >&2; exit 1; }
repo=$(pwd -P)
out=$(cd "$1" && pwd -P)
case "$out" in
    "$repo/$feature/evidence/Step 2/private/"*-mqtt-reader-replay) ;;
    *) echo 'FAIL: evidence must be an existing, private 0028 MQTT rehearsal directory' >&2; exit 1 ;;
esac
[[ -s "$out/fixtures/EXPECTED.PRIVATE.json" && -s "$out/fixtures/EXPECTED-MARQUEES.PRIVATE.json" && -s "$out/retained-fragments.PRIVATE.txt" && -s "$out/retained-marquees.PRIVATE.txt" ]] || {
    echo 'FAIL: cannot resume without complete original MQTT replay receipts' >&2; exit 1;
}
if [[ -f "$out/RESULT.txt" ]] && grep -Fq 'PASS: isolated responder replay' "$out/RESULT.txt"; then
    echo 'PASS: this 0028 MQTT/Reader HTTP rehearsal has already completed'; cat "$out/RESULT.txt"; exit 0
fi
# Reverify captured payloads against the same reviewed manifest, without new MQTT publications.
python3 "$repo/$feature/tools/0028-replay-verify.py" validate-retained \
    --expected "$out/fixtures/EXPECTED.PRIVATE.json" --input "$out/retained-fragments.PRIVATE.txt" \
    | tee "$out/retained-http-resume-validation.txt"
python3 "$repo/$feature/tools/0028-replay-verify.py" validate-marquees \
    --expected "$out/fixtures/EXPECTED-MARQUEES.PRIVATE.json" --input "$out/retained-marquees.PRIVATE.txt" \
    | tee "$out/marquee-http-resume-validation.txt"
# Guard every existing container and the internal bridge before adding any resources.
[[ "$(docker network inspect --format '{{.Internal}}' "$backend")" == true ]] || { echo 'FAIL: internal backend changed' >&2; exit 1; }
[[ "$(docker network inspect --format "{{index .Labels \"${label}\"}}" "$backend")" == true ]] || { echo 'FAIL: backend label mismatch' >&2; exit 1; }
for name in "$db" "$broker" "$responder" "$reader"; do
    [[ -n "$(docker ps -q -f "name=^/${name}$")" ]] || { echo "FAIL: ${name} not running; refusing to rebuild" >&2; exit 1; }
    [[ "$(docker inspect --format "{{index .Config.Labels \"${label}\"}}" "$name")" == true ]] || { echo "FAIL: unlabeled existing container: $name" >&2; exit 1; }
done
[[ "$(docker inspect --format '{{.Config.Image}}' "$db")" == 'postgres:18-alpine' ]] || { echo 'FAIL: isolated DB image mismatch' >&2; exit 1; }
# Inspect all network memberships and isolated database journal without connecting to production.
python3 - "$backend" "$frontend" "$db" "$broker" "$responder" "$reader" <<'PY_INSPECT'
import json,subprocess,sys
backend,frontend,db,broker,responder,reader=sys.argv[1:]
for name in (db,broker,responder,reader):
    d=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
    nets=set(d['NetworkSettings']['Networks'])
    if backend not in nets or frontend in nets:
        raise SystemExit(f'FAIL: unexpected network membership for {name}: {nets}')
    if name in (broker,responder,reader) and nets!={backend}:
        raise SystemExit(f'FAIL: replay service {name} must have internal network only')
d=json.loads(subprocess.check_output(['docker','inspect',db],text=True))[0]
if not any(m.get('Type')=='volume' and m.get('Name')=='diaries-0028-rehearsal-pgdata' for m in d['Mounts']):
    raise SystemExit('FAIL: database volume identity mismatch')
ports=(d['NetworkSettings']['Ports'] or {}).get('5432/tcp') or []
if len(ports)!=1 or ports[0].get('HostIp')!='127.0.0.1' or ports[0].get('HostPort')!='55428':
    raise SystemExit('FAIL: restored database is not localhost 55428')
print('PASS: database/broker/responder/Reader remain on the isolated backend')
PY_INSPECT
psql_isolated() { docker exec "$db" psql -X -A -t -v ON_ERROR_STOP=1 -U postgres -d diaries_0028_rehearsal -c "$1" | tr -d '\r'; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_source')" == 71 ]] || { echo 'FAIL: source journal changed' >&2; exit 1; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_image_occurrence')" == 71 ]] || { echo 'FAIL: occurrence journal changed' >&2; exit 1; }
[[ "$(psql_isolated 'select count(*) from public.fragment')" == 2331 ]] || { echo 'FAIL: fragment row count changed' >&2; exit 1; }
marquee_before=$(psql_isolated "select md5(coalesce(string_agg(md5(row_to_json(m)::text),'' ORDER BY m.id),'')) from public.marquee m")
if [[ -f "$out/marquee-before.md5" ]]; then
    [[ "$(cat "$out/marquee-before.md5")" == "$marquee_before" ]] || { echo 'FAIL: Marquee records changed since before MQTT replay' >&2; exit 1; }
fi
printf '%s\n' "$marquee_before" > "$out/marquee-before-http.md5"

# Only the proxy may join the standard bridge. Core services remain internal-only.
if docker network inspect "$frontend" >/dev/null 2>&1; then
    [[ "$(docker network inspect --format "{{index .Labels \"${label}\"}}" "$frontend")" == true ]] || { echo 'FAIL: frontend network exists without 0028 label' >&2; exit 1; }
    [[ "$(docker network inspect --format '{{.Internal}}' "$frontend")" == false ]] || { echo 'FAIL: frontend cannot be an internal-only bridge' >&2; exit 1; }
else
    docker network create --driver bridge --label "${label}=true" "$frontend" > "$out/http-frontend-network-id.txt"
fi
proxy_conf_win=$(cygpath -aw "$repo/$feature/tools/0028-mqtt-http-proxy.conf")
proxy_action=create
if [[ -n "$(docker ps -a -q -f "name=^/${proxy}$")" ]]; then
    # Existing previous-run gateway is disposable, but replacement is allowed
    # ONLY when it is exactly our labelled nginx proxy with the expected
    # read-only configuration, loopback-only requested bindings and no
    # unexpected networks. Never remove a caller's unrelated container.
    proxy_action=$(python3 - "$proxy" "$backend" "$frontend" "$label" <<'PY_PROXY'
import json, subprocess, sys
name,backend,frontend,label=sys.argv[1:]
p=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
if p['Config'].get('Labels',{}).get(label)!='true':
    raise SystemExit('FAIL: existing HTTP proxy has incorrect label; refusing replacement')
if p['Config'].get('Image')!='nginx:alpine':
    raise SystemExit('FAIL: existing HTTP proxy image differs; refusing replacement')
nets=set(p['NetworkSettings']['Networks'])
if not nets or not nets.issubset({backend,frontend}):
    raise SystemExit(f'FAIL: unexpected HTTP proxy networks {nets}; refusing replacement')
mounts=p['Mounts']
if len(mounts)!=1 or mounts[0].get('Destination')!='/etc/nginx/conf.d/default.conf' or mounts[0].get('RW') is not False:
    raise SystemExit('FAIL: existing proxy does not have the expected read-only nginx configuration; refusing replacement')
expected={'8081/tcp':[{'HostIp':'127.0.0.1','HostPort':'58081'}],
          '8082/tcp':[{'HostIp':'127.0.0.1','HostPort':'58082'}]}
requested=p['HostConfig'].get('PortBindings') or {}
if requested not in ({}, expected):
    raise SystemExit('FAIL: existing proxy requested unexpected bindings; refusing replacement')
actual=p['NetworkSettings'].get('Ports') or {}
if nets=={backend,frontend} and all(actual.get(k)==v for k,v in expected.items()):
    print('keep')
else:
    print('replace')
PY_PROXY
    )
fi
if [[ "$proxy_action" == replace ]]; then
    echo 'Repairing ONLY the labelled 0028 disposable HTTP proxy; database, MQTT and Reader remain untouched'
    docker logs "$proxy" > "$out/http-proxy-before-repair.log" 2>&1 || true
    docker inspect "$proxy" > "$out/http-proxy-before-repair.PRIVATE.json"
    docker rm -f "$proxy" > "$out/http-proxy-removed-id.txt"
fi
if [[ "$proxy_action" != keep ]]; then
    # Create on the NON-internal frontend first. When created on the internal
    # bridge first, Docker 29 discards the -p host bindings and connecting an
    # additional bridge later does not reliably activate them.
    # Configure BOTH networks before starting nginx, so upstream DNS names
    # resolve on the first attempt and ports are active from startup.
    docker create --name "$proxy" --network "$frontend" --label "${label}=true" \
        -p 127.0.0.1:58081:8081 -p 127.0.0.1:58082:8082 \
        --mount "type=bind,source=$proxy_conf_win,target=/etc/nginx/conf.d/default.conf,readonly" \
        nginx:alpine > "$out/http-proxy-id.txt"
    docker network connect "$backend" "$proxy"
    docker start "$proxy" > "$out/http-proxy-start.txt"
fi
# Verify effective published ports and exact network ownership, not requested -p flags.
python3 - "$proxy" "$backend" "$frontend" "$db" "$broker" "$responder" "$reader" <<'PY_PORTS'
import json,subprocess,sys
proxy,backend,frontend,db,broker,responder,reader=sys.argv[1:]
def inspect(name):return json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
p=inspect(proxy)
if set(p['NetworkSettings']['Networks'])!={backend,frontend}:
    raise SystemExit('FAIL: proxy is not the only intended dual-homed HTTP gateway')
ports=p['NetworkSettings']['Ports'] or {}
for internal,external in [('8081/tcp','58081'),('8082/tcp','58082')]:
    bindings=ports.get(internal) or []
    if len(bindings)!=1 or bindings[0].get('HostIp')!='127.0.0.1' or bindings[0].get('HostPort')!=external:
        raise SystemExit(f'FAIL: proxy port {internal} is not published at localhost:{external}: {bindings}')
for k,v in ports.items():
    if k not in ('8081/tcp','8082/tcp') and v:
        raise SystemExit('FAIL: unexpected additional HTTP proxy port')
for name in (db,broker,responder,reader):
    if frontend in inspect(name)['NetworkSettings']['Networks']:
        raise SystemExit(f'FAIL: isolated service unexpectedly on frontend: {name}')
print('PASS: only the HTTP proxy publishes localhost:58081 and localhost:58082')
PY_PORTS

echo '=== Reader HTTP readiness through isolated localhost proxy ==='
ready=no
for attempt in $(seq 1 45); do
    code=$(curl --noproxy '*' --silent --show-error --max-time 4 \
        -o "$out/reader-health.json" -w '%{http_code}' \
        http://127.0.0.1:58082/health/ready 2>> "$out/http-curl-errors.log") || code=000
    if [[ "$code" == 200 ]]; then ready=yes;break; fi
    sleep 2
done
if [[ "$ready" != yes ]]; then
    docker logs "$reader" > "$out/reader.log" 2>&1 || true
    docker logs "$proxy" > "$out/http-proxy.log" 2>&1 || true
    echo "FAIL: Reader HTTP readiness via proxy; last status=${code}" >&2
    cat "$out/reader-health.json" >&2 2>/dev/null || true
    tail -40 "$out/http-proxy.log" >&2 || true
    exit 1
fi
printf '%s\n' 'PASS: Reader reached HTTP 200 readiness via dedicated localhost proxy'
curl --noproxy '*' --fail --silent --show-error --location --max-time 20 \
    http://127.0.0.1:58082/ -o "$out/reader-home.PRIVATE.html"
[[ -s "$out/reader-home.PRIVATE.html" ]] || { echo 'FAIL: Reader home page is empty' >&2; exit 1; }

python3 - "$out/fixtures/EXPECTED.PRIVATE.json" "$out/representative-urls.txt" <<'PY_URLS'
import json,sys
from urllib.parse import quote
rows=json.load(open(sys.argv[1],encoding='utf-8'))
link=next((x for x in rows if x['link']),rows[0])
marquee=next((x for x in rows if x['marquee_id']),rows[1])
plain=next((x for x in rows if not x['link'] and not x['marquee_id']),rows[2])
with open(sys.argv[2],'w',encoding='utf-8') as f:
    for x in {a['fragment_id']:a for a in (link,marquee,plain)}.values():
        f.write(f'{x["fragment_id"]}\t{quote(x["image_path"],safe="/")}\n')
PY_URLS
while IFS=$'\t' read -r fid path; do
    [[ -n "$fid" && -n "$path" ]] || { echo 'FAIL: representative image URL missing' >&2; exit 1; }
    curl --noproxy '*' --fail --silent --show-error --location --max-time 20 \
        "http://127.0.0.1:58082/fragments/$fid" -o "$out/reader-fragment-${fid}.PRIVATE.html"
    [[ -s "$out/reader-fragment-${fid}.PRIVATE.html" ]] || { echo "FAIL: Reader returned empty Fragment $fid" >&2; exit 1; }
    curl --noproxy '*' --fail --silent --show-error --head --max-time 20 \
        "http://127.0.0.1:58081/files/$path" > "$out/media-${fid}.headers.txt"
    echo "PASS: Reader route and staged catalogue HTTP media for Fragment $fid"
done < "$out/representative-urls.txt"
marquee_after=$(psql_isolated "select md5(coalesce(string_agg(md5(row_to_json(m)::text),'' ORDER BY m.id),'')) from public.marquee m")
[[ "$marquee_before" == "$marquee_after" ]] || { echo 'FAIL: Marquee changed during HTTP verification' >&2; exit 1; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_source')" == 71 ]] || { echo 'FAIL: migration journal changed during HTTP verification' >&2; exit 1; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_image_occurrence')" == 71 ]] || { echo 'FAIL: occurrence journal changed during HTTP verification' >&2; exit 1; }
docker logs "$responder" > "$out/responder.log" 2>&1
docker logs "$reader" > "$out/reader.log" 2>&1
docker logs "$proxy" > "$out/http-proxy.log" 2>&1
cat > "$out/RESULT.txt" <<'RESULT'
PASS: retained MQTT replay matches all 71 reviewed IMAGE Fragment identities, references, links, Marquees and captions.
PASS: all 22 preserved Marquee retained topics match correct identity, Fragment and Page.
PASS: Reader projection is ready via localhost-only nginx gateway and representative Reader/Images HTTP checks.
PASS: isolated DB journal counts and current Marquee row fingerprint unchanged during HTTP verification.
NO production, existing development MQTT, or production PostgreSQL access attempted.
NOT TESTED: original diary page scan images, Angular Editor GUI and full visual browser acceptance.
Isolated DB, broker, responder and Reader retained; only labelled HTTP proxy joins external-facing frontend bridge.
RESULT
cat "$out/RESULT.txt"
echo 'Reader URL: http://127.0.0.1:58082/'
echo "PRIVATE evidence: $out"
echo 'PASS: 0028 Step 2 isolated MQTT/Reader HTTP rehearsal completed'
