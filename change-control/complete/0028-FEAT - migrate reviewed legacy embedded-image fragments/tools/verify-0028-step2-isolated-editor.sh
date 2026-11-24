#!/usr/bin/env bash
# Read-only HTTP/MQTT/DB checks of the 0028 isolated Angular Editor GUI.
# May be rerun without rebuilding, publishing or mutating any records.
set -euo pipefail
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
label='uk.co.rsmaxwell.diaries.0028.isolated-rehearsal'
backend='diaries-0028-replay-net'
frontend='diaries-0028-replay-http-front'
editor='diaries-0028-replay-editor'
bridge='diaries-0028-replay-editor-ws-bridge'
proxy='diaries-0028-replay-editor-proxy'
db='diaries-0028-rehearsal-db'
fail() { echo "FAIL: $*" >&2; exit 1; }
[[ -f .gitmodules && -d diaries-client ]] || fail 'Run from Diaries parent checkout'
for tool in docker python3 curl; do command -v "$tool" >/dev/null || fail "missing $tool"; done
if [[ $# -eq 0 ]]; then
  # Independent subsequent verification uses the latest completed private start.
  mapfile -t candidates < <(find "$feature/evidence/Step 2/private" -maxdepth 1 -type d -name '*-isolated-editor-gui' | sort)
  (( ${#candidates[@]} > 0 )) || fail 'No isolated Editor evidence. Run start script first.'
  out="${candidates[${#candidates[@]}-1]}"
elif [[ $# -eq 1 && -d "$1" ]]; then out="$1"
else fail 'Usage: bash <verification> [existing-editor-private-evidence-dir]'; fi
out=$(cd "$out" && pwd -P)
repo=$(pwd -P)
case "$out" in "$repo/$feature/evidence/Step 2/private/"*-isolated-editor-gui) ;; *) fail 'Evidence must be within the 0028 private editor rehearsal directory';; esac
for name in "$editor" "$bridge" "$proxy"; do
  [[ -n "$(docker ps -q -f "name=^/${name}$")" ]] || fail "Isolated Editor service missing: $name"
  [[ "$(docker inspect --format "{{index .Config.Labels \"${label}\"}}" "$name")" == true ]] || fail "Unexpected service label: $name"
done
python3 - "$backend" "$frontend" "$editor" "$bridge" "$proxy" <<'PY_NET'
import json,subprocess,sys
backend,frontend,editor,bridge,proxy=sys.argv[1:]
for name in (editor,bridge,proxy):
 d=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
 nets=set(d['NetworkSettings']['Networks'])
 expected={backend,frontend} if name==proxy else {backend}
 if nets!=expected:raise SystemExit('FAIL: Editor service network drift: %s = %s' % (name,nets))
 published={k:v for k,v in (d['NetworkSettings'].get('Ports') or {}).items() if v}
 if name!=proxy and published:raise SystemExit('FAIL: a backend-only Editor service exposes ports: '+name)
 if name==proxy:
  if published!={'8083/tcp':[{'HostIp':'127.0.0.1','HostPort':'58083'}]}:
   raise SystemExit('FAIL: Editor HTTP gateway host ports changed: %s' % published)
print('PASS: Editor and MQTT-WebSocket bridge internal-only; only labelled gateway exposes localhost:58083')
PY_NET
[[ "$(docker network inspect --format '{{.Internal}}' "$backend")" == true ]] || fail 'Internal backend was changed'
[[ "$(docker network inspect --format '{{.Internal}}' "$frontend")" == false ]] || fail 'Frontend bridge changed'
# Isolated application assets, runtime configuration and same-origin scan media.
curl --noproxy '*' --fail --silent --show-error --max-time 10 \
  'http://127.0.0.1:58083/diaries/' > "$out/editor-index.PRIVATE.html"
curl --noproxy '*' --fail --silent --show-error --max-time 10 \
  'http://127.0.0.1:58083/diaries/assets/config.json' > "$out/runtime-config-readback.PRIVATE.json"
python3 - "$out/runtime-config-readback.PRIVATE.json" "$out/editor-index.PRIVATE.html" <<'PY_CONFIG'
import json,sys
cfg=json.load(open(sys.argv[1],encoding='utf-8'))
expected={'brokerMode':'proxy','brokerProxyPath':'/mosquitto/',
          'responderBaseUrlMode':'same-origin','clientId':'0028-isolated-editor',
          'protocolVersion':5}
for key,val in expected.items():
 if cfg.get(key)!=val:raise SystemExit('FAIL: Editor runtime config %s is not rehearsal-only'%key)
if cfg.get('brokerDirectUrl') or cfg.get('brokerProxyUrl') or cfg.get('responderBaseUrl'):
 raise SystemExit('FAIL: explicit external connection present in runtime config')
if 'rsmaxwell.co.uk' in json.dumps(cfg).lower() or 'localhost:9001' in json.dumps(cfg):
 raise SystemExit('FAIL: development/production endpoint leakage in runtime config')
html=open(sys.argv[2],encoding='utf-8').read().lower()
if '<base href="/diaries/">' not in html and "<base href='/diaries/'>" not in html:
 raise SystemExit('FAIL: Angular Editor application base path differs from /diaries/')
print('PASS: Angular Editor assets and exact same-origin isolated runtime configuration served')
PY_CONFIG
code=$(curl --noproxy '*' --silent --show-error --max-time 10 -o /dev/null -w '%{http_code}' \
 'http://127.0.0.1:58083/diaries-responder/diaries/diary-1828-and-1829-and-jan-1830/img2840.jpg')
[[ "$code" == 200 ]] || fail "Source scan via Editor same-origin gateway: HTTP $code"
echo 'PASS: original manuscript img2840 accessible via Editor same-origin responder path'
python3 "$feature/tools/0028-editor-websocket-probe.py" | tee "$out/mqtt-ws-connect.txt"
curl --noproxy '*' --fail --silent --show-error --max-time 10 \
 'http://127.0.0.1:58082/health/ready' > "$out/reader-health.json"
psql_isolated() { docker exec "$db" psql -X -A -t -v ON_ERROR_STOP=1 -U postgres -d diaries_0028_rehearsal -c "$1" | tr -d '\r'; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_source')" == 71 ]] || fail 'Migration source journal changed'
[[ "$(psql_isolated 'select count(*) from public.migration0028_image_occurrence')" == 71 ]] || fail 'Migration occurrence journal changed'
[[ "$(psql_isolated 'select count(*) from public.fragment')" == 2331 ]] || fail 'Isolated Fragment row count changed'
marquee_after=$(psql_isolated "select md5(coalesce(string_agg(md5(row_to_json(m)::text),'' ORDER BY m.id),'')) from public.marquee m")
[[ -s "$out/marquee-before.md5" && "$(cat "$out/marquee-before.md5")" == "$marquee_after" ]] || fail 'Isolated Marquee records changed during Editor startup'
echo 'PASS: Reader still ready; all 71+71 migration journals and pre-existing Marquee records unchanged'
echo 'PASS: isolated Editor automatic acceptance checks completed (no database writes)'
echo "PRIVATE evidence: $out"
