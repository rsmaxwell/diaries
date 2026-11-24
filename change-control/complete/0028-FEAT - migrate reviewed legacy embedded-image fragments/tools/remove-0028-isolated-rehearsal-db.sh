#!/usr/bin/env bash
# Explicit cleanup of ONLY the labelled, disposable 0028 rehearsal Docker objects.
# Run after acceptance/evidence review. Never touches any production/development DB.
(
  set -euo pipefail
  container='diaries-0028-rehearsal-db'
  volume='diaries-0028-rehearsal-pgdata'
  label='uk.co.rsmaxwell.diaries.0028.isolated-rehearsal'
  command -v docker >/dev/null || { echo 'FAIL: Docker required' >&2; exit 1; }
  if docker container inspect "$container" >/dev/null 2>&1; then
    [[ "$(docker inspect -f "{{index .Config.Labels \"$label\"}}" "$container")" == true ]] || {
      echo "FAIL: unexpected container identity; refusing deletion" >&2; exit 1;
    }
    docker rm -f "$container"
    echo 'PASS: removed only labelled isolated 0028 PostgreSQL container'
  fi
  if docker volume inspect "$volume" >/dev/null 2>&1; then
    [[ "$(docker volume inspect -f "{{index .Labels \"$label\"}}" "$volume")" == true ]] || {
      echo 'FAIL: unexpected volume identity; refusing deletion' >&2; exit 1;
    }
    docker volume rm "$volume"
    echo 'PASS: removed only labelled isolated 0028 PostgreSQL volume'
  fi
  echo 'PRIVATE source dump, media copy and reports under 0028 evidence are untouched.'
)
