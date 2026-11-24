#!/usr/bin/env bash
# Explicitly invoked, guarded cleanup of disposable 0028 replay Docker objects.
# Includes isolated Editor GUI and WebSocket bridge when present.
# Does NOT remove the restored database, its volume, original media or evidence.
set -euo pipefail
[[ "${1:-}" == '--confirm-remove-isolated-replay' && $# -eq 1 ]] || {
  echo 'Usage: bash <script> --confirm-remove-isolated-replay' >&2; exit 1;
}
label='uk.co.rsmaxwell.diaries.0028.isolated-rehearsal'
network='diaries-0028-replay-net'
frontend='diaries-0028-replay-http-front'
proxy='diaries-0028-replay-http-proxy'
db='diaries-0028-rehearsal-db'
scan_volume='diaries-0028-replay-source-scans-volume'
for name in "diaries-0028-replay-editor-proxy" "diaries-0028-replay-editor" "diaries-0028-replay-editor-ws-bridge" "$proxy" diaries-0028-replay-scan-loader diaries-0028-replay-source-scans diaries-0028-replay-reader diaries-0028-replay-responder diaries-0028-replay-broker; do
  if [[ -n "$(docker ps -a -q -f "name=^/${name}$")" ]]; then
    [[ "$(docker inspect --format "{{index .Config.Labels \"${label}\"}}" "$name")" == true ]] || {
      echo "FAIL: refusing unlabelled container: $name" >&2; exit 1;
    }
  fi
done
if docker network inspect "$network" >/dev/null 2>&1; then
  [[ "$(docker network inspect --format "{{index .Labels \"${label}\"}}" "$network")" == true ]] || {
    echo 'FAIL: refusing unlabelled network' >&2; exit 1;
  }
fi
if docker network inspect "$frontend" >/dev/null 2>&1; then
  [[ "$(docker network inspect --format "{{index .Labels \"${label}\"}}" "$frontend")" == true ]] || {
    echo 'FAIL: refusing unlabelled HTTP frontend network' >&2; exit 1;
  }
fi
if docker volume inspect "$scan_volume" >/dev/null 2>&1; then
  [[ "$(docker volume inspect --format "{{index .Labels \"${label}\"}}" "$scan_volume")" == true ]] || {
    echo 'FAIL: refusing unlabelled original-scan volume' >&2;exit 1;
  }
fi
for name in "diaries-0028-replay-editor-proxy" "diaries-0028-replay-editor" "diaries-0028-replay-editor-ws-bridge" "$proxy" diaries-0028-replay-scan-loader diaries-0028-replay-source-scans diaries-0028-replay-reader diaries-0028-replay-responder diaries-0028-replay-broker; do
  if [[ -n "$(docker ps -a -q -f "name=^/${name}$")" ]]; then
    docker rm -f "$name"
  fi
done
if docker network inspect "$frontend" >/dev/null 2>&1; then
  docker network rm "$frontend"
fi
if docker network inspect "$network" >/dev/null 2>&1; then
  if [[ -n "$(docker ps -a -q -f "name=^/${db}$")" ]]; then
    membership_template="{{index .NetworkSettings.Networks \"${network}\"}}"
    membership=$(docker inspect --format "$membership_template" "$db")
    if [[ "$membership" != '<no value>' && -n "$membership" ]]; then
      docker network disconnect "$network" "$db"
    fi
  fi
  docker network rm "$network"
fi
if docker volume inspect "$scan_volume" >/dev/null 2>&1; then
  docker volume rm "$scan_volume"
fi
echo 'PASS: only labelled 0028 MQTT/HTTP/Editor replay containers, scan volume, proxies and bridges removed; restored DB and private evidence retained'
