#!/usr/bin/env bash
# 0028-FEAT: stage original source-page scans and test the isolated Reader.
# Run from the Windows PC/Cygwin Diaries parent checkout. NO database writes.
# Retains original DB, MQTT, responder, Reader and migration journals untouched.
# Only a labelled read-only scan sidecar is added and the labelled HTTP proxy replaced.
set -euo pipefail
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
label='uk.co.rsmaxwell.diaries.0028.isolated-rehearsal'
replay="$feature/evidence/Step 2/private/20261123T195519Z-mqtt-reader-replay"
backend='diaries-0028-replay-net'
frontend='diaries-0028-replay-http-front'
proxy='diaries-0028-replay-http-proxy'
scans='diaries-0028-replay-source-scans'
scan_volume='diaries-0028-replay-source-scans-volume'
scan_loader='diaries-0028-replay-scan-loader'
scan_loader_started=0
db='diaries-0028-rehearsal-db'
broker='diaries-0028-replay-broker'
responder='diaries-0028-replay-responder'
reader='diaries-0028-replay-reader'
tools="$feature/tools"
out="$replay/source-scans"
stage_pending=''
failed() {
    local rc=$?
    trap - EXIT
    # Delete only our own newly-created incomplete staging, never accepted evidence.
    if [[ -n "${stage_pending:-}" && "$stage_pending" == "$out/.pending-original-scans" && -d "$stage_pending" ]]; then
        rm -rf -- "$stage_pending"
    fi
    # The loader is a temporary, labelled, network-disabled container only.
    if [[ "${scan_loader_started:-0}" == 1 ]]; then
        if [[ "$(docker inspect --format "{{index .Config.Labels \"${label}\"}}" "$scan_loader" 2>/dev/null || true)" == true ]]; then
            docker rm -f "$scan_loader" >/dev/null 2>&1 || echo 'WARNING: labelled scan loader remains for inspection' >&2
        fi
    fi
    if (( rc != 0 )); then
        echo "FAIL: 0028 original-page-scan HTTP acceptance incomplete (exit $rc)" >&2
        echo 'Existing isolated DB, broker, responder, Reader and previous replay evidence remain untouched.' >&2
        echo 'No production database, production MQTT or image catalogue write was attempted.' >&2
    fi
}
trap failed EXIT
[[ $# -eq 0 ]] || { echo 'Usage: bash <script> (from the Diaries parent root)' >&2; exit 1; }
[[ -f .gitmodules && -d diaries-responder && -d diaries-web ]] || {
    echo 'FAIL: run from Windows/Cygwin Diaries parent checkout' >&2; exit 1;
}
for c in docker python3 cygpath curl sha256sum git grep cmp tr cut seq sleep tar wc; do
    command -v "$c" >/dev/null || { echo "FAIL: missing executable $c" >&2; exit 1; }
done
repo=$(pwd -P)
[[ -s "$replay/RESULT.txt" && -s "$replay/fixtures/EXPECTED.PRIVATE.json" ]] || {
    echo 'FAIL: accepted MQTT/Reader rehearsal evidence is unavailable' >&2;exit 1;
}
grep -Fq 'PASS: retained MQTT replay matches all 71' "$replay/RESULT.txt" || {
    echo 'FAIL: MQTT/Reader replay was not accepted' >&2;exit 1;
}
# Guard the backend/frontend and ALL relevant named containers before staging media.
python3 - "$backend" "$frontend" "$proxy" "$db" "$broker" "$responder" "$reader" "$label" <<'PY_GUARD'
import json, subprocess, sys
backend,frontend,proxy,db,broker,responder,reader,label=sys.argv[1:]
def inspect(name):
    return json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
for net,internal in ((backend,True),(frontend,False)):
    n=json.loads(subprocess.check_output(['docker','network','inspect',net],text=True))[0]
    if n.get('Internal') is not internal or n.get('Labels',{}).get(label)!='true':
        raise SystemExit(f'FAIL: network {net} does not match labelled isolation')
for name in (db,broker,responder,reader,proxy):
    d=inspect(name)
    if d['Config'].get('Labels',{}).get(label)!='true' or not d['State']['Running']:
        raise SystemExit(f'FAIL: missing or unlabelled running rehearsal container {name}')
    networks=set(d['NetworkSettings']['Networks'])
    if backend not in networks:
        raise SystemExit(f'FAIL: missing isolated backend membership: {name}')
    if name in (broker,responder,reader) and networks!={backend}:
        raise SystemExit(f'FAIL: {name} is not confined to the internal bridge')
    if name==db and frontend in networks:
        raise SystemExit('FAIL: database joined the browser-facing frontend')
    if name==proxy and networks!={frontend,backend}:
        raise SystemExit('FAIL: HTTP proxy must be the only dual-network service')
d=inspect(db)
if d['Config']['Image']!='postgres:18-alpine':
    raise SystemExit('FAIL: wrong PostgreSQL image')
if not any(m.get('Type')=='volume' and m.get('Name')=='diaries-0028-rehearsal-pgdata' for m in d['Mounts']):
    raise SystemExit('FAIL: unexpected database volume')
if (d['NetworkSettings']['Ports'] or {}).get('5432/tcp') != [{'HostIp':'127.0.0.1','HostPort':'55428'}]:
    raise SystemExit('FAIL: PostgreSQL is not bound exclusively to localhost 55428')
p=inspect(proxy)
if p['Config']['Image']!='nginx:alpine':
    raise SystemExit('FAIL: unexpected proxy image')
ports=p['NetworkSettings']['Ports'] or {}
for key,hostport in (('8081/tcp','58081'),('8082/tcp','58082')):
    if ports.get(key)!=[{'HostIp':'127.0.0.1','HostPort':hostport}]:
        raise SystemExit(f'FAIL: proxy port {key} differs from localhost:{hostport}')
if any(k not in ('8081/tcp','8082/tcp') and value for k,value in ports.items()):
    raise SystemExit('FAIL: unexpected additional published proxy port')
mounts=p['Mounts']
if len(mounts)!=1 or mounts[0]['Destination']!='/etc/nginx/conf.d/default.conf' or mounts[0]['RW'] is not False:
    raise SystemExit('FAIL: proxy config is not uniquely read-only mounted')
if not mounts[0]['Source'].endswith(('0028-mqtt-http-proxy.conf','0028-mqtt-http-proxy-with-scans.conf')):
    raise SystemExit('FAIL: proxy config source does not match 0028')
print('PASS: existing labelled isolated DB, broker, responder, Reader, networks and localhost proxy verified')
PY_GUARD
psql_isolated() { docker exec "$db" psql -X -A -t -v ON_ERROR_STOP=1 -U postgres -d diaries_0028_rehearsal -c "$1" | tr -d '\r'; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_source')" == 71 ]] || { echo 'FAIL: journal source count not 71' >&2;exit 1; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_image_occurrence')" == 71 ]] || { echo 'FAIL: journal occurrence count not 71' >&2;exit 1; }
[[ "$(psql_isolated 'select count(*) from public.fragment')" == 2331 ]] || { echo 'FAIL: isolated Fragment count changed' >&2;exit 1; }
marquee_before=$(psql_isolated "select md5(coalesce(string_agg(md5(row_to_json(m)::text),'' ORDER BY m.id),'')) from public.marquee m")
mkdir -p "$out"
{
    date -u
    git branch --show-current
    git rev-parse HEAD
    git status --short
    git submodule status
} > "$out/checkout.txt" 2>&1
# The read-only dataset consists of all pages referenced by the 71 reviewed
# converted source fragments, plus the two original pages shown in screenshots.
# No production DB connections are used; metadata is from the existing isolated DB.
query="COPY (
WITH targets AS (
 SELECT fragment_id AS id FROM public.migration0028_source
 UNION SELECT 65
 UNION SELECT 84
)
SELECT DISTINCT d.name AS diary_name, p.name AS page_name,
       p.extension AS extension, p.id AS page_id
FROM targets t JOIN public.fragment f ON f.id=t.id
 JOIN public.page p ON p.id=f.page_id
 JOIN public.diary d ON d.id=p.diary_id
ORDER BY diary_name,page_name,extension,page_id
) TO STDOUT WITH (FORMAT CSV, HEADER TRUE)"
docker exec "$db" psql -X -q -v ON_ERROR_STOP=1 -U postgres -d diaries_0028_rehearsal -c "$query" > "$out/page-list.new.PRIVATE.csv"
[[ -s "$out/page-list.new.PRIVATE.csv" ]] || { echo 'FAIL: original page list is empty' >&2;exit 1; }
if [[ -e "$out/page-list.PRIVATE.csv" ]]; then
    cmp -s "$out/page-list.PRIVATE.csv" "$out/page-list.new.PRIVATE.csv" || {
        echo 'FAIL: original page list changed since previous scan staging' >&2;exit 1;
    }
    rm "$out/page-list.new.PRIVATE.csv"
else
    mv "$out/page-list.new.PRIVATE.csv" "$out/page-list.PRIVATE.csv"
fi
# Require restored metadata for March 1828 page images img2839 and img2840.
python3 - "$out/page-list.PRIVATE.csv" <<'PY_EXPECTED'
import csv,sys
rows=list(csv.DictReader(open(sys.argv[1],encoding='utf-8',newline='')))
names={r['page_name'] for r in rows}
if not {'img2839','img2840'}.issubset(names):
    raise SystemExit('FAIL: expected original pages img2839 and img2840 not in isolated DB records')
if len(rows)<2 or len(rows)>73:
    raise SystemExit('FAIL: unexpected count of original pages')
print(f'PASS: {len(rows)} distinct original pages required for 71 conversions and shown screenshot examples')
PY_EXPECTED
source_root=${DIARIES_0028_SOURCE_DIARIES_ROOT:-'/cygdrive/p/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/diaries'}
[[ -d "$source_root" ]] || { echo "FAIL: original page scans not found at $source_root; set DIARIES_0028_SOURCE_DIARIES_ROOT" >&2;exit 1; }
if [[ -s "$out/staged/STAGING-RESULT.PRIVATE.json" ]]; then
    python3 "$tools/0028-stage-original-page-scans.py" \
      --csv "$out/page-list.PRIVATE.csv" --destination "$out/staged" --check-existing
else
    [[ ! -e "$out/staged" ]] || {
        echo 'FAIL: incomplete existing staged original scans; inspect private evidence before retrying' >&2; exit 1;
    }
    stage_pending="$out/.pending-original-scans"
    [[ ! -e "$stage_pending" ]] || {
        echo 'FAIL: incomplete prior temporary staging directory requires inspection' >&2;exit 1;
    }
    mkdir "$stage_pending"
    python3 "$tools/0028-stage-original-page-scans.py" \
      --csv "$out/page-list.PRIVATE.csv" --source "$source_root" --destination "$stage_pending"
    mv "$stage_pending" "$out/staged"
    stage_pending=''
fi
(cd "$out/staged" && sha256sum -c SHA256SUMS.txt) > "$out/staged-sha256.txt"
echo 'PASS: source NAS originals are unchanged; independently copied private scans verified'
# Only the additional read-only static server joins the internal backend.
# Do not bind-mount the deeply nested Windows staging tree into Docker Desktop.
# A 290-character host path caused nginx open() to fail with EIO. Stage a
# verified second copy inside a LABELLED Docker-managed volume instead.
# The private Windows evidence and NAS originals remain unchanged.
scans_conf_win=$(cygpath -aw "$repo/$tools/0028-original-page-scans-nginx.conf")
expected_scans=$(python3 - "$out/staged/STAGING-RESULT.PRIVATE.json" <<'PY_EXPECTED_SCAN_COUNT'
import json,sys
obj=json.load(open(sys.argv[1],encoding='utf-8'))
if obj.get('status')!='PASS' or obj.get('original_page_count')!=len(obj.get('page_scans',[])):
    raise SystemExit('FAIL: private scan staging inventory is incomplete')
print(obj['original_page_count'])
PY_EXPECTED_SCAN_COUNT
)
[[ "$expected_scans" == 41 ]] || { echo "FAIL: expected 41 staged original scans, got $expected_scans" >&2; exit 1; }
[[ -z "$(docker ps -a -q -f "name=^/${scan_loader}$")" ]] || {
    echo "FAIL: existing scan loader '$scan_loader' requires manual inspection; no automatic overwrite" >&2;exit 1;
}
new_volume=0
if ! docker volume inspect "$scan_volume" >/dev/null 2>&1; then
    docker volume create --label "${label}=true" "$scan_volume" > "$out/source-scan-volume-created.txt"
    new_volume=1
fi
python3 - "$scan_volume" "$scans" "$scan_loader" "$label" <<'PY_VOLUME_GUARD'
import json,subprocess,sys
volume,scans,loader,label=sys.argv[1:]
v=json.loads(subprocess.check_output(['docker','volume','inspect',volume],text=True))[0]
if v.get('Name')!=volume or v.get('Driver')!='local' or (v.get('Labels') or {}).get(label)!='true':
    raise SystemExit('FAIL: Docker scan volume identity/label mismatch')
attached=subprocess.check_output(['docker','ps','-a','--filter','volume='+volume,'--format','{{.Names}}'],text=True).splitlines()
if any(name not in (scans,loader) for name in attached):
    raise SystemExit('FAIL: original scan volume is attached to an unrelated container')
print('PASS: labelled, isolated Docker-managed scan volume verified')
PY_VOLUME_GUARD
# A no-network temporary container mounts the volume writable ONLY while
# importing and validating the previously SHA-256-verified Windows copies.
docker run -d --name "$scan_loader" --network none --label "${label}=true" \
    --mount "type=volume,source=$scan_volume,target=/data/diaries" \
    --entrypoint sh nginx:alpine -c 'tail -f /dev/null' > "$out/source-scan-loader-id.txt"
scan_loader_started=1
# If a previous attempt stopped before copying any file, safely retry the
# empty labelled volume. Partially populated volumes are NOT overwritten.
preexisting_scan_files=$(docker exec "$scan_loader" find /data/diaries -type f | wc -l | tr -d '[:space:]')
if [[ "$new_volume" == 1 || "$preexisting_scan_files" == 0 ]]; then
    echo '=== Stream already-staged original scans into the isolated Docker volume ==='
    # stdin TAR transfer avoids Docker Desktop accessing the long Windows path.
    tar -C "$out/staged/diaries" -cf - . | docker cp - "$scan_loader:/data/diaries"
else
    echo '=== Reuse existing labelled Docker scan volume; verify all bytes again ==='
fi
# Docker itself reads every file from its own volume; no host bind is involved.
docker exec -i "$scan_loader" sh -c 'cd /data && sha256sum -c' \
    < "$out/staged/SHA256SUMS.txt" > "$out/docker-volume-sha256.txt"
actual_scans=$(docker exec "$scan_loader" find /data/diaries -type f | wc -l | tr -d '[:space:]')
[[ "$actual_scans" == "$expected_scans" ]] || {
    echo "FAIL: Docker volume file count $actual_scans differs from $expected_scans" >&2;exit 1;
}
[[ -z "$(docker exec "$scan_loader" find /data/diaries -type l)" ]] || {
    echo 'FAIL: Docker volume contains unexpected symbolic links' >&2;exit 1;
}
docker rm -f "$scan_loader" > "$out/source-scan-loader-removed.txt"
scan_loader_started=0
echo "PASS: $expected_scans original page scans readable INSIDE Docker; byte hashes match private staging"
# Replace ONLY the labelled scan-serving container. The existing proxy,
# responder, broker, Reader and database are untouched. On reruns, verify
# both volume identity and read-only mounts before reuse.
scan_mode='absent'
if [[ -n "$(docker ps -a -q -f "name=^/${scans}$")" ]]; then
    scan_mode=$(python3 - "$scans" "$backend" "$frontend" "$label" "$scan_volume" <<'PY_EXISTING_SCANS'
import json,subprocess,sys
name,backend,frontend,label,volume=sys.argv[1:]
d=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
if d['Config'].get('Labels',{}).get(label)!='true' or d['Config']['Image']!='nginx:alpine' or not d['State']['Running']:
    raise SystemExit('FAIL: existing source scan server identity mismatch')
if set(d['NetworkSettings']['Networks'])!={backend} or frontend in d['NetworkSettings']['Networks']:
    raise SystemExit('FAIL: source scan server is not backend-only')
if any(v for v in (d['NetworkSettings']['Ports'] or {}).values()):
    raise SystemExit('FAIL: source scan server unexpectedly publishes a host port')
mounts={m['Destination']:m for m in d['Mounts']}
if len(mounts)!=2 or not all(v['RW'] is False for v in mounts.values()):
    raise SystemExit('FAIL: source server mounts are not uniquely read-only')
media=mounts.get('/usr/share/nginx/html/diaries')
config=mounts.get('/etc/nginx/conf.d/default.conf')
if not media or not config or config['Type']!='bind' or not config['Source'].replace('\\','/').endswith('/0028-original-page-scans-nginx.conf'):
    raise SystemExit('FAIL: unexpected source scan server configuration')
if media['Type']=='volume' and media.get('Name')==volume:
    print('volume')
elif media['Type']=='bind' and media['Source'].replace('\\','/').endswith('/source-scans/staged/diaries'):
    print('legacy-bind')
else:
    raise SystemExit('FAIL: source media mount differs from reviewed legacy bind or verified volume')
PY_EXISTING_SCANS
    )
fi
if [[ "$scan_mode" == legacy-bind ]]; then
    echo '=== Replace ONLY the labelled scan server with a read-only volume-backed server ==='
    docker inspect "$scans" > "$out/source-scans-before-volume.PRIVATE.json"
    docker logs "$scans" > "$out/source-scans-before-volume.log" 2>&1 || true
    docker rm -f "$scans" > "$out/legacy-source-scan-removed.txt"
fi
if [[ "$scan_mode" != volume ]]; then
    docker run -d --name "$scans" --network "$backend" --label "${label}=true" \
      --mount "type=volume,source=$scan_volume,target=/usr/share/nginx/html/diaries,readonly" \
      --mount "type=bind,source=$scans_conf_win,target=/etc/nginx/conf.d/default.conf,readonly" \
      nginx:alpine > "$out/source-scans-volume-container-id.txt"
else
    echo 'PASS: existing read-only volume-backed source scan server reused'
fi
docker exec "$scans" nginx -t > "$out/source-scans-nginx-test.txt" 2>&1 || {
    cat "$out/source-scans-nginx-test.txt" >&2;exit 1;
}
# Independently read the probe from the running, volume-backed Nginx container
# before trusting HTTP. This would have exposed the earlier bind-mount EIO.
docker exec "$scans" sha256sum \
  /usr/share/nginx/html/diaries/diary-1828-and-1829-and-jan-1830/img2839.jpg \
  > "$out/source-scans-container-probe-sha256.txt"
expected_probe=$(python3 - "$out/staged/STAGING-RESULT.PRIVATE.json" <<'PY_PROBE_HASH'
import json,sys
obj=json.load(open(sys.argv[1],encoding='utf-8'))
items=[r for r in obj['page_scans'] if r['relative_path']=='diary-1828-and-1829-and-jan-1830/img2839.jpg']
if len(items)!=1:
    raise SystemExit('FAIL: original img2839 is not uniquely represented in private evidence')
print(items[0]['sha256'])
PY_PROBE_HASH
)
actual_probe=$(cut -d' ' -f1 "$out/source-scans-container-probe-sha256.txt" | tr -d '\r')
[[ "$actual_probe" == "$expected_probe" ]] || {
    echo 'FAIL: image bytes changed between Docker-volume validation and Nginx container' >&2;exit 1;
}
echo 'PASS: volume-backed source scan server can read img2839 with original SHA-256'
# Gateway retains same loopback HTTP ports and networks; only its config is
# changed to route /diaries/* to the read-only source-scan container.
proxy_with_scans_win=$(cygpath -aw "$repo/$tools/0028-mqtt-http-proxy-with-scans.conf")
proxy_conf=$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/etc/nginx/conf.d/default.conf"}}{{.Source}}{{end}}{{end}}' "$proxy")
if [[ "$proxy_conf" != *'0028-mqtt-http-proxy-with-scans.conf' ]]; then
    echo '=== Replace ONLY labelled disposable HTTP proxy (no responder/Reader restart) ==='
    docker logs "$proxy" > "$out/http-proxy-before-scans.log" 2>&1 || true
    docker inspect "$proxy" > "$out/http-proxy-before-scans.PRIVATE.json"
    docker rm -f "$proxy" > "$out/previous-proxy-removed-id.txt"
    docker create --name "$proxy" --network "$frontend" --label "${label}=true" \
      -p 127.0.0.1:58081:8081 -p 127.0.0.1:58082:8082 \
      --mount "type=bind,source=$proxy_with_scans_win,target=/etc/nginx/conf.d/default.conf,readonly" \
      nginx:alpine > "$out/new-proxy-id.txt"
    docker network connect "$backend" "$proxy"
    docker start "$proxy" > "$out/new-proxy-start.txt"
else
    echo 'PASS: existing source-scan-enabled HTTP proxy reused'
fi
docker exec "$proxy" nginx -t > "$out/http-proxy-nginx-test.txt" 2>&1 || {
    cat "$out/http-proxy-nginx-test.txt" >&2;exit 1;
}
python3 - "$proxy" "$scans" "$backend" "$frontend" "$label" "$scan_volume" <<'PY_FINAL_GUARD'
import json,subprocess,sys
proxy,scans,backend,frontend,label,volume=sys.argv[1:]
def inspect(name):return json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
p=inspect(proxy);s=inspect(scans)
if set(p['NetworkSettings']['Networks'])!={backend,frontend} or set(s['NetworkSettings']['Networks'])!={backend}:
    raise SystemExit('FAIL: scan server/proxy isolation changed')
if p['Config']['Labels'].get(label)!='true' or s['Config']['Labels'].get(label)!='true':
    raise SystemExit('FAIL: missing labelled isolation')
for k,v in (('8081/tcp','58081'),('8082/tcp','58082')):
    if (p['NetworkSettings']['Ports'] or {}).get(k)!=[{'HostIp':'127.0.0.1','HostPort':v}]:
        raise SystemExit(f'FAIL: HTTP loopback port {v} missing')
if any(value for value in (s['NetworkSettings']['Ports'] or {}).values()):
    raise SystemExit('FAIL: source server has a published port')
mounts={m['Destination']:m for m in s['Mounts']}
media=mounts.get('/usr/share/nginx/html/diaries')
if not media or media['Type']!='volume' or media['Name']!=volume or media['RW'] is not False:
    raise SystemExit('FAIL: source scan files not mounted from the expected read-only Docker volume')
print('PASS: only HTTP proxy exposed on localhost; source scans read from labelled read-only Docker volume')
PY_FINAL_GUARD
# Verify all staged originals return actual bytes through the Reader's existing
# publicResponderBaseUrl; GET hashes checked for img2839 and img2840.
python3 - "$out/staged/STAGING-RESULT.PRIVATE.json" "$out/source-page-urls.PRIVATE.tsv" <<'PY_URLS'
import json,sys
from urllib.parse import quote
rows=json.load(open(sys.argv[1],encoding='utf-8'))['page_scans']
with open(sys.argv[2],'w',encoding='utf-8') as f:
    for r in rows:
        f.write(f"{r['page_name']}\t{quote(r['relative_path'],safe='/')}\t{r['sha256']}\n")
PY_URLS
# Docker may take a short time to begin accepting HTTP after container start.
first_encoded=$(python3 - "$out/staged/STAGING-RESULT.PRIVATE.json" <<'PY_FIRST'
import json,sys
from urllib.parse import quote
r=json.load(open(sys.argv[1],encoding='utf-8'))['page_scans'][0]
print(quote(r['relative_path'],safe='/'))
PY_FIRST
)
ready=no
for attempt in $(seq 1 30); do
    if curl --noproxy '*' --silent --fail --head --max-time 4 \
        "http://127.0.0.1:58081/diaries/$first_encoded" > /dev/null 2>&1;then
        ready=yes;break
    fi
    sleep 1
done
[[ "$ready" == yes ]] || {
    docker logs "$scans" > "$out/source-scans.log" 2>&1 || true
    docker logs "$proxy" > "$out/http-proxy.log" 2>&1 || true
    echo 'FAIL: original page scan HTTP gateway did not become ready' >&2;exit 1
}
count=0
while IFS=$'\t' read -r page_name encoded sha; do
    [[ -n "$page_name" && -n "$encoded" ]] || { echo 'FAIL: invalid page URL record' >&2;exit 1; }
    url="http://127.0.0.1:58081/diaries/$encoded"
    curl --noproxy '*' --fail --silent --show-error --head --max-time 15 "$url" > /dev/null
    if [[ "$page_name" == img2839 || "$page_name" == img2840 ]]; then
        actual=$(curl --noproxy '*' --fail --silent --show-error --max-time 30 "$url" | sha256sum | cut -d' ' -f1)
        [[ "$actual" == "$sha" ]] || { echo "FAIL: HTTP original $page_name digest mismatch" >&2;exit 1; }
        echo "PASS: original source page $page_name served intact through localhost proxy"
    fi
    count=$((count+1))
done < "$out/source-page-urls.PRIVATE.tsv"
reader_status=$(curl --noproxy '*' --silent --show-error --max-time 15 -o "$out/reader-ready.PRIVATE.json" -w '%{http_code}' http://127.0.0.1:58082/health/ready)
[[ "$reader_status" == 200 ]] || { echo "FAIL: Reader readiness changed: HTTP $reader_status" >&2;exit 1; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_source')" == 71 ]] || { echo 'FAIL: migration journal count changed' >&2;exit 1; }
[[ "$(psql_isolated 'select count(*) from public.migration0028_image_occurrence')" == 71 ]] || { echo 'FAIL: occurrence journal count changed' >&2;exit 1; }
[[ "$(psql_isolated "select md5(coalesce(string_agg(md5(row_to_json(m)::text),'' ORDER BY m.id),'')) from public.marquee m")" == "$marquee_before" ]] || {
    echo 'FAIL: isolated Marquee records changed' >&2; exit 1;
}
cat > "$out/RESULT.txt" <<EOF
PASS: ${count} original source page scans staged privately from NAS; source unchanged; SHA-256 independently verified.
PASS: source page URLs return HTTP success via isolated localhost proxy; img2839 and img2840 HTTP bytes match original digests.
PASS: Reader HTTP readiness persists; 71 source and occurrence journals unchanged; all Marquee rows unchanged.
NO: production DB changes, image registry changes, MQTT publications, production deployment.
NOT TESTED: browser visual acceptance or interactive Angular Editor GUI.
EOF
cat "$out/RESULT.txt"
echo "PRIVATE evidence: $out"
echo 'Reader: http://127.0.0.1:58082/diaries/1/1828/03?fragment=84#fragment-84'
echo 'PASS: 0028 read-only original page scan HTTP verification completed'
