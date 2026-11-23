#!/usr/bin/env bash
# 0052-DEF: consolidated read-only NAS, PostgreSQL and HTTP baseline.
# RUN ONLY as a separate non-interactive process, from Windows Cygwin:
#   bash ".../tools/collect-0052-step1-readonly.sh" both
# Optional modes: production | development | both
# Output: this feature's ignored evidence/Step 1/private/<UTC>/ directory.
# No SQL, file or MQTT writes. Does not assume databases share image IDs.
set -euo pipefail
umask 077

mode="${1:-both}"
case "$mode" in production|development|both) ;; *) echo 'Usage: bash collect-0052-step1-readonly.sh [production|development|both]' >&2; exit 2;; esac

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
feature_dir="$(cd -- "$script_dir/.." && pwd)"
repo_dir="$(cd -- "$feature_dir/../../.." && pwd)"
sql="$script_dir/step1-live-catalogue-readonly.sql"
[[ -r "$sql" ]] || { echo "Missing SQL: $sql" >&2; exit 2; }

evidence_dir="$feature_dir/evidence/Step 1/private/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p -- "$evidence_dir"
summary="$evidence_dir/summary.log"
: > "$summary"
failures=0
declare -A file_hashes=()
record() { printf '%s\n' "$*" | tee -a "$summary"; }
problem() { record "FAIL: $*"; failures=$((failures+1)); }

record "0052-DEF Step 1 READ-ONLY inventory (UTC): $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
record "Mode: $mode"
record "Evidence: $evidence_dir"

if {
    echo '=== Parent checkout ==='
    git -C "$repo_dir" branch --show-current
    git -C "$repo_dir" rev-parse HEAD
    git -C "$repo_dir" status --short --untracked-files=no
    echo '=== Submodules ==='
    git -C "$repo_dir" submodule status
  } > "$evidence_dir/git-checkout.log" 2>&1; then
  record 'PASS: Windows parent checkout and submodules recorded'
else
  problem 'Git checkout inspection failed (git-checkout.log)'
fi

# NAS data is inspected from the Windows P: mapping, not changed. Subpath is
# the actual NAS path shown in the owner's 23 Nov Cygwin terminal log.
content_root="${DIARIES_NAS_CONTENT_ROOT:-/cygdrive/p/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content}"
diary_name='diary-1828-and-1829-and-jan-1830'
metadata="$content_root/diaries/$diary_name/metadata/images-root"
relative="$diary_name/images"
file_manifest="$evidence_dir/nas-files.log"
: > "$file_manifest"

check_file() {
  local label="$1" path="$2" expected="${3:-}" hash
  printf '\n### %s\nPATH: %s\n' "$label" "$path" >> "$file_manifest"
  if [[ ! -f "$path" ]]; then
    printf 'MISSING\n' >> "$file_manifest"
    # Missing optional historical/derived paths still require inventory review.
    problem "Missing expected file: $label (see nas-files.log)"
    return 0
  fi
  if ! hash="$(sha256sum -- "$path" | awk '{print $1}')"; then
    problem "Could not checksum $label"
    return 0
  fi
  printf 'SHA256: %s\n' "$hash" >> "$file_manifest"
  file_hashes["$label"]="$hash"
  ls -l -- "$path" >> "$file_manifest" 2>&1 || true
  file -- "$path" >> "$file_manifest" 2>&1 || true
  if [[ -n "$expected" ]]; then
    if [[ "$hash" == "$expected" ]]; then
      record "PASS: $label selected SHA-256 matches"
    else
      problem "$label SHA-256 differs from approved source; STOP before replacement"
    fi
  else
    record "HASHED: $label"
  fi
}

check_file 'Whitley approved replacement PNG' \
  "$metadata/source/img2840-whitley-park-map/whitley-park-historical-map-large.png" \
  d9f54457b8b4ac67a9a91df5e8c7c32c2767531dd2d6461c3f7faf9c31e4706a
check_file 'Whitley original metadata source JPEG' "$metadata/source/img2840-image-map-whitley-park.jpg"
check_file 'Whitley processed metadata JPEG' "$metadata/images/img2840-image-map-whitley-park.jpg"
check_file 'Whitley production Files JPEG' "$content_root/files/$relative/img2840-image-map-whitley-park.jpg"
check_file 'Whitley development Files JPEG' "$content_root/files-development-common/$relative/img2840-image-map-whitley-park.jpg"

check_file 'Hermitage approved source PNG' "$metadata/source/img2900-image-hermitage.png" \
  9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0
check_file 'Hermitage processed metadata PNG' "$metadata/images/img2900-image-hermitage.png" \
  9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0
check_file 'Hermitage production Files PNG' "$content_root/files/$relative/img2900-image-hermitage.png"
check_file 'Hermitage development Files PNG' "$content_root/files-development-common/$relative/img2900-image-hermitage.png"

for image in 'img2903-image-st-isaac-church.png' \
             'img2900-image-the-jordan-staircase-state-hermitage-museum-st-petersburg-russia-B2KPFE.jpg'; do
  check_file "Protected production $image" "$content_root/files/$relative/$image"
  check_file "Protected development $image" "$content_root/files-development-common/$relative/$image"
done
record 'NAS read-only file check completed; see nas-files.log for paths and checksums'

# Auto-discover only one target PostgreSQL container. Do not dump container
# environment, Compose config, credentials or volumes into public evidence.
select_container() {
  local where="$1" list="$2" name
  local -a matches=()
  while IFS= read -r name; do
    [[ -n "$name" ]] || continue
    if [[ "$where" == production ]]; then
      [[ "$name" == 'diaries-db' || "$name" == 'diaries-production-db' ]] || continue
    else
      [[ "$name" == 'diaries-development-db' || "$name" == 'diaries-local-db' || "$name" == 'diaries-published-smoke-db' ]] || continue
    fi
    matches+=("$name")
  done <<< "$list"
  if (( ${#matches[@]} != 1 )); then
    return 1
  fi
  printf '%s\n' "${matches[0]}"
}

run_production_sql() {
  local names container
  if ! names="$(ssh -o BatchMode=yes -o ConnectTimeout=12 pluto 'docker ps --format "{{.Names}}"' 2> "$evidence_dir/production-docker-errors.log")"; then
    problem 'Production SSH/Docker discovery failed (production-docker-errors.log)'
    return
  fi
  printf '%s\n' "$names" > "$evidence_dir/production-container-names.log"
  if ! container="$(select_container production "$names")"; then
    problem 'Could not unambiguously identify production Diaries PostgreSQL container (production-container-names.log)'
    return
  fi
  record "Production database container: $container"
  if ssh -o BatchMode=yes -o ConnectTimeout=12 pluto \
     "docker exec -i '$container' sh -c 'exec psql -X -v ON_ERROR_STOP=1 -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\"'" \
     < "$sql" > "$evidence_dir/production-catalogue-private.log" 2>&1; then
    record 'PASS: Production catalogue SQL completed in READ ONLY transaction'
  else
    problem 'Production catalogue SQL failed (production-catalogue-private.log)'
  fi
}

run_development_sql() {
  local names container
  if ! names="$(docker ps --format '{{.Names}}' 2> "$evidence_dir/development-docker-errors.log")"; then
    problem 'Windows local Docker discovery failed (development-docker-errors.log)'
    return
  fi
  printf '%s\n' "$names" > "$evidence_dir/development-container-names.log"
  if ! container="$(select_container development "$names")"; then
    problem 'Could not unambiguously identify one running local Diaries PostgreSQL container (development-container-names.log)'
    return
  fi
  record "Development database container: $container"
  if docker exec -i "$container" sh -c 'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
     < "$sql" > "$evidence_dir/development-catalogue-private.log" 2>&1; then
    record 'PASS: Development catalogue SQL completed in READ ONLY transaction'
  else
    problem 'Development catalogue SQL failed (development-catalogue-private.log)'
  fi
}

if [[ "$mode" == production || "$mode" == both ]]; then run_production_sql; fi
if [[ "$mode" == development || "$mode" == both ]]; then run_development_sql; fi

# HTTP URLs follow the confirmed shared Nginx route /diaries-responder/files
# and the local static-file route /files. Hash streaming response bytes;
# never save image contents under evidence or overwrite the NAS.
http_hash() {
  local label="$1" url="$2" outfile="$3" nas_label="$4" response_hash expected_hash
  if curl --fail --silent --show-error --location --connect-timeout 10 --max-time 120 \
       --header 'Cache-Control: no-cache' "$url" 2> "$evidence_dir/${outfile}-errors.log" \
       | sha256sum > "$evidence_dir/${outfile}.log"; then
    response_hash="$(awk '{print $1}' "$evidence_dir/${outfile}.log")"
    expected_hash="${file_hashes[$nas_label]:-}"
    if [[ -n "$expected_hash" ]]; then
      if [[ "$response_hash" == "$expected_hash" ]]; then
        record "PASS: HTTP response matches NAS served Files bytes: $label"
      else
        problem "HTTP/NAS served file checksum mismatch: $label"
      fi
    else
      record "HASHED: HTTP response $label (no NAS baseline for automatic comparison)"
    fi
  else
    problem "Could not hash HTTP response: $label (${outfile}-errors.log)"
  fi
}
if [[ "$mode" == production || "$mode" == both ]]; then
  http_hash 'Production Hermitage' \
    "https://pluto.rsmaxwell.co.uk/diaries-responder/files/$relative/img2900-image-hermitage.png" 'production-hermitage-http' 'Hermitage production Files PNG'
  http_hash 'Production Whitley' \
    "https://pluto.rsmaxwell.co.uk/diaries-responder/files/$relative/img2840-image-map-whitley-park.jpg" 'production-whitley-http' 'Whitley production Files JPEG'
fi
if [[ "$mode" == development || "$mode" == both ]]; then
  # Local responder HTTP may be offline in development-infrastructure mode.
  http_hash 'Development Hermitage (local responder port 8081)' \
    "http://localhost:8081/files/$relative/img2900-image-hermitage.png" 'development-hermitage-http' 'Hermitage development Files PNG'
  http_hash 'Development Whitley (local responder port 8081)' \
    "http://localhost:8081/files/$relative/img2840-image-map-whitley-park.jpg" 'development-whitley-http' 'Whitley development Files JPEG'
fi

record 'NOTE: MQTT retained-state publication is not queried; it remains a separate read-only verification.'
record "Collected private evidence at: $evidence_dir"
if ((failures)); then
  record "PARTIAL/FAIL: $failures check(s) require review; no data was changed"
  exit 1
fi
record 'PASS: Read-only collection completed; no data was changed'
