#!/usr/bin/env bash
# Windows PC/Cygwin. Repair the one locally generated JWT secret in the 0028
# isolated responder. No production systems are addressed; no user DB changes.
# Must run from the Diaries parent checkout. Dedicated process uses fail-fast.
set -euo pipefail
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
fixtures="$feature/evidence/Step 2/private/20261123T195519Z-mqtt-reader-replay/fixtures"
config="$fixtures/responder.ISOLATED.PRIVATE.json"
helper="$feature/tools/0028-isolated-auth-secret.py"
label='uk.co.rsmaxwell.diaries.0028.isolated-rehearsal'
responder='diaries-0028-replay-responder'
db='diaries-0028-rehearsal-db'
reader='diaries-0028-replay-reader'
fail() { echo "FAIL: $*" >&2; exit 1; }
[[ -f .gitmodules && -d diaries-responder && -d "$feature" ]] || fail 'Run from Windows Diaries parent checkout'
for cmd in docker python3 curl date grep tr seq sleep; do command -v "$cmd" >/dev/null || fail "Missing command: $cmd"; done
[[ -f "$config" && -f "$helper" ]] || fail 'Expected existing rehearsal config and helper absent; do not regenerate fixtures'
[[ ! -L "$config" ]] || fail 'Rehearsal config must not be a symlink'
[[ "$(docker inspect --format "{{index .Config.Labels \"${label}\"}}" "$responder")" == true ]] || fail 'Responder is not labelled as the isolated 0028 rehearsal'
[[ "$(docker inspect --format "{{index .Config.Labels \"${label}\"}}" "$db")" == true ]] || fail 'Database is not labelled as the isolated 0028 rehearsal'
[[ -n "$(docker ps -q -f "name=^/${responder}$")" ]] || fail 'Isolated responder not running'
[[ -n "$(docker ps -q -f "name=^/${reader}$")" ]] || fail 'Isolated Reader not running'
python3 - "$responder" "$config" <<'PY_ID'
import json, subprocess, sys
name, config = sys.argv[1:]
d=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
if d['Config']['Image'] != 'diaries-0028-replay-responder:local':
    raise SystemExit('FAIL: unexpected responder image')
if set(d['NetworkSettings']['Networks']) != {'diaries-0028-replay-net'}:
    raise SystemExit('FAIL: responder connected to unexpected Docker network')
mounts=[m for m in d['Mounts'] if m.get('Destination')=='/config/responder.json']
if len(mounts)!=1 or mounts[0].get('Type')!='bind' or mounts[0].get('RW'):
    raise SystemExit('FAIL: responder config is not a single read-only bind mount')
src=mounts[0]['Source'].replace('\\','/').casefold()
suffix='/20261123t195519z-mqtt-reader-replay/fixtures/responder.isolated.private.json'
if not src.endswith(suffix):
    raise SystemExit('FAIL: mounted config is not the expected private 0028 fixture')
print('PASS: exact isolated responder image, network, identity and config mount verified')
PY_ID
# Verify clone identity and baseline acceptance before modifying the isolated config.
psql_rehearsal() {
    docker exec "$db" psql -X -A -t -v ON_ERROR_STOP=1 -U postgres -d diaries_0028_rehearsal -c "$1" | tr -d '\r'
}
[[ "$(psql_rehearsal 'select count(*) from public.migration0028_source')" == 71 ]] || fail 'Migration source journal missing'
[[ "$(psql_rehearsal 'select count(*) from public.migration0028_image_occurrence')" == 71 ]] || fail 'Migration occurrence journal missing'
[[ "$(psql_rehearsal 'select count(*) from public.fragment')" == 2331 ]] || fail 'Restored fragment count changed'
marquee_before=$(psql_rehearsal "select md5(coalesce(string_agg(md5(row_to_json(m)::text),'' ORDER BY m.id),'')) from public.marquee m")
curl --noproxy '*' --fail --silent --show-error --max-time 10 'http://127.0.0.1:58082/health/ready' >/dev/null || fail 'Reader is not healthy before repair'
if python3 "$helper" inspect "$config" | grep -q '^VALID:'; then
    fail 'JWT secret already valid for Java Base64; investigate isolated responder logs before changing anything'
fi
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="$feature/evidence/Step 2/private/${stamp}-isolated-editor-auth-repair"
mkdir -p "$out" || fail 'Cannot create private evidence directory'
[[ ! -L "$out" ]] || fail 'Private evidence directory must not be a symlink'
chmod 700 "$out" 2>/dev/null || true
# Use a private backup file, never stdout. Preserve the original bytes.
python3 "$helper" repair "$config" --backup "$out/responder-config.before.PRIVATE.json"
# Check the bind mount sees the updated file without revealing the secret.
python3 - "$config" "$responder" <<'PY_MOUNT'
import base64, json, subprocess, sys
host, container=sys.argv[1:]
local=json.load(open(host,encoding='utf-8'))
raw=subprocess.check_output(['docker','exec',container,'cat','/config/responder.json'],text=True)
remote=json.loads(raw)
if remote != local:
    raise SystemExit('FAIL: Docker container does not see edited config; DO NOT restart')
if len(base64.b64decode(remote['secret'],validate=True)) < 32:
    raise SystemExit('FAIL: JWT signing key too short')
print('PASS: isolated responder bind mount sees correct new Base64 JWT signing key')
PY_MOUNT
printf '%s\n' '=== Restart only labelled isolated responder to load new auth secret ==='
docker restart "$responder" >/dev/null
[[ -n "$(docker ps -q -f "name=^/${responder}$")" ]] || fail 'Isolated responder failed to restart; inspect private logs'
# Reader is a separate service and must remain healthy.
for attempt in $(seq 1 30); do
    if curl --noproxy '*' --fail --silent --max-time 5 'http://127.0.0.1:58082/health/ready' >/dev/null; then break; fi
    sleep 1
done
curl --noproxy '*' --fail --silent --show-error --max-time 10 'http://127.0.0.1:58082/health/ready' >/dev/null || fail 'Reader readiness failed after isolated responder restart'
[[ "$(psql_rehearsal 'select count(*) from public.migration0028_source')" == 71 ]] || fail 'Migration source journal changed'
[[ "$(psql_rehearsal 'select count(*) from public.migration0028_image_occurrence')" == 71 ]] || fail 'Migration occurrence journal changed'
[[ "$(psql_rehearsal 'select count(*) from public.fragment')" == 2331 ]] || fail 'Fragment count changed'
marquee_after=$(psql_rehearsal "select md5(coalesce(string_agg(md5(row_to_json(m)::text),'' ORDER BY m.id),'')) from public.marquee m")
[[ "$marquee_before" == "$marquee_after" ]] || fail 'Marquee records changed during isolated responder restart'
echo 'PASS: Reader ready and database journals, Fragment count and all Marquees unchanged'
echo 'PASS: 0028 isolated JWT secret correction complete; now retry sign-in in isolated Editor'
echo "PRIVATE evidence: $out"
echo 'NO production or development responder restart; no account or password changes'
