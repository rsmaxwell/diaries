#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
if [[ "${MODE}" != "pre" && "${MODE}" != "post" ]]; then
    echo "Usage: $0 pre|post [output-directory]" >&2
    exit 2
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${2:-$HOME/step15-${MODE}-${STAMP}}"
PROJECT_DIR="${DIARIES_PROJECT_DIR:-$HOME/projects/diaries}"
COMPOSE_FILE="${PROJECT_DIR}/compose.yaml"
ENV_FILE="${PROJECT_DIR}/.env"
RESPONDER_CONFIG="${PROJECT_DIR}/config/responder/responder.json"
WEB_CONFIG="${PROJECT_DIR}/config/web/diaries-web.json"
ACL_FILE="${PROJECT_DIR}/config/mosquitto/aclfile.txt"

EXPECTED_CLIENT_IMAGE="${EXPECTED_CLIENT_IMAGE:-rsmaxwell/diaries-client:0.0.9-build-74}"
EXPECTED_WEB_IMAGE="${EXPECTED_WEB_IMAGE:-rsmaxwell/diaries-web:0.0.9-build-7}"
EXPECTED_RESPONDER_IMAGE="${EXPECTED_RESPONDER_IMAGE:-rsmaxwell/diaries-responder:0.0.9-build-82}"
EXPECTED_FILES_PATH="${EXPECTED_FILES_PATH:-files}"

mkdir -p "${OUT}"
exec > >(tee "${OUT}/console.txt") 2>&1

failures=0
warnings=0

pass() { printf 'PASS: %s\n' "$*"; }
warn() { printf 'WARN: %s\n' "$*"; warnings=$((warnings + 1)); }
fail() { printf 'FAIL: %s\n' "$*"; failures=$((failures + 1)); }

require_file() {
    local path="$1"
    if [[ ! -f "${path}" ]]; then
        fail "required file missing: ${path}"
        return 1
    fi
}

compose() {
    docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" "$@"
}

db_query() {
    local sql="$1"
    compose exec -T diaries-db sh -c \
        'psql -v ON_ERROR_STOP=1 -At -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"' \
        sh "${sql}"
}

container_record() {
    local service="$1"
    local expected="${2:-}"
    local cid
    cid="$(compose ps -q "${service}" 2>/dev/null || true)"
    if [[ -z "${cid}" ]]; then
        fail "${service} has no running/created container"
        printf '%s\t%s\t%s\t%s\t%s\n' "${service}" '<missing>' '<missing>' '<missing>' '<missing>' \
            >> "${OUT}/container-identities.tsv"
        return
    fi

    local configured image_id state health
    configured="$(docker inspect --format '{{.Config.Image}}' "${cid}")"
    image_id="$(docker inspect --format '{{.Image}}' "${cid}")"
    state="$(docker inspect --format '{{.State.Status}}' "${cid}")"
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}' "${cid}")"
    printf '%s\t%s\t%s\t%s\t%s\n' "${service}" "${configured}" "${image_id}" "${state}" "${health}" \
        >> "${OUT}/container-identities.tsv"

    if [[ "${MODE}" == "post" && -n "${expected}" ]]; then
        if [[ "${configured}" == "${expected}" ]]; then
            pass "${service} running configured image ${expected}"
        else
            fail "${service} image is ${configured}; expected ${expected}"
        fi
    fi
    if [[ "${state}" != "running" ]]; then
        fail "${service} state is ${state}; expected running"
    elif [[ "${health}" != "healthy" && "${health}" != "n/a" ]]; then
        fail "${service} health is ${health}; expected healthy"
    fi
}

printf 'Step 15 production evidence\n'
printf 'mode: %s\n' "${MODE}"
printf 'captured: %s\n' "$(date --iso-8601=seconds)"
printf 'host: %s\n' "$(hostname -f 2>/dev/null || hostname)"
printf 'project: %s\n' "${PROJECT_DIR}"
printf 'output: %s\n\n' "${OUT}"

for file in "${COMPOSE_FILE}" "${ENV_FILE}" "${RESPONDER_CONFIG}" "${WEB_CONFIG}" "${ACL_FILE}"; do
    require_file "${file}" || true
done
if (( failures > 0 )); then
    echo "Required runtime files are missing; cannot continue safely."
    exit 1
fi

cd "${PROJECT_DIR}"

if compose config --quiet; then
    pass "Docker Compose configuration is valid"
else
    fail "Docker Compose configuration is invalid"
fi

compose ps --all > "${OUT}/compose-ps.txt" || fail "could not capture Compose status"
compose config --images > "${OUT}/compose-images.txt" || fail "could not capture Compose image list"

echo -e 'service\tconfigured_image\timage_id\tstate\thealth' > "${OUT}/container-identities.tsv"
container_record diaries-client "${EXPECTED_CLIENT_IMAGE}"
container_record diaries-web "${EXPECTED_WEB_IMAGE}"
container_record diaries-responder "${EXPECTED_RESPONDER_IMAGE}"
container_record diaries-mqtt
container_record diaries-db

# Record only non-secret deployment settings.
jq '{imageFragmentWritesEnabled}' "${RESPONDER_CONFIG}" > "${OUT}/responder-authoring-gate.json"
jq '{http: {basePath: .http.basePath, publicBaseUrl: .http.publicBaseUrl}, content}' \
    "${WEB_CONFIG}" > "${OUT}/web-public-config.json"

GATE="$(jq -r 'if has("imageFragmentWritesEnabled") then (.imageFragmentWritesEnabled | tostring) else "<missing>" end' "${RESPONDER_CONFIG}")"
if [[ "${GATE}" == "false" ]]; then
    pass "ImageFragment production authoring gate is explicitly disabled"
else
    fail "imageFragmentWritesEnabled is ${GATE}; expected explicit false"
fi

FILES_PATH="$(jq -r '.content.filesPath // "<missing>"' "${WEB_CONFIG}")"
if [[ "${MODE}" == "post" ]]; then
    if [[ "${FILES_PATH}" == "${EXPECTED_FILES_PATH}" ]]; then
        pass "diaries-web content.filesPath is ${EXPECTED_FILES_PATH}"
    else
        fail "diaries-web content.filesPath is ${FILES_PATH}; expected ${EXPECTED_FILES_PATH}"
    fi
else
    if [[ "${FILES_PATH}" == "<missing>" ]]; then
        warn "pre-deployment web config has no explicit content.filesPath (expected before Step 15 deployment)"
    else
        pass "pre-deployment web config already has content.filesPath=${FILES_PATH}"
    fi
fi

# Extract only the diaries-web ACL block; do not expose pwfile contents.
awk '
  $1 == "user" { active = ($2 == "diaries-web") }
  active { print }
' "${ACL_FILE}" > "${OUT}/diaries-web-acl.txt"

if grep -Fxq 'topic deny diaries/rpc/#' "${OUT}/diaries-web-acl.txt" && \
   grep -Fxq 'topic read diaries/images/+' "${OUT}/diaries-web-acl.txt"; then
    pass "diaries-web ACL denies RPC and grants canonical Image read"
else
    fail "diaries-web ACL is missing the expected RPC deny or Image read rule"
fi
if grep -Eq '^(topic|pattern)[[:space:]]+(write|readwrite)[[:space:]]' "${OUT}/diaries-web-acl.txt"; then
    fail "diaries-web ACL contains a write/readwrite rule"
else
    pass "diaries-web ACL contains no write/readwrite rule"
fi

# Check the 0025 persistence shape and capture counts without exposing row contents.
SCHEMA_COLUMNS="$(db_query "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name IN ('page_id','type','image_id');" 2>/dev/null || echo ERROR)"
IMAGE_TABLE="$(db_query "SELECT CASE WHEN to_regclass('public.image') IS NULL THEN 0 ELSE 1 END;" 2>/dev/null || echo ERROR)"
IMAGE_COUNT="$(db_query "SELECT count(*) FROM public.fragment WHERE type='IMAGE';" 2>/dev/null || echo ERROR)"
CATALOGUE_COUNT="$(db_query "SELECT count(*) FROM public.image;" 2>/dev/null || echo ERROR)"
{
    printf 'fragment_required_columns=%s\n' "${SCHEMA_COLUMNS}"
    printf 'image_table_present=%s\n' "${IMAGE_TABLE}"
    printf 'image_fragment_rows=%s\n' "${IMAGE_COUNT}"
    printf 'image_catalogue_rows=%s\n' "${CATALOGUE_COUNT}"
} > "${OUT}/database-readiness.txt"

if [[ "${SCHEMA_COLUMNS}" == "3" && "${IMAGE_TABLE}" == "1" ]]; then
    pass "0025 fragment/image schema is present"
else
    fail "0025 schema readiness failed (fragment columns=${SCHEMA_COLUMNS}, image table=${IMAGE_TABLE})"
fi

OLD_READER_ROLLBACK_SAFE=false
if [[ "${IMAGE_COUNT}" =~ ^[0-9]+$ ]]; then
    if [[ "${IMAGE_COUNT}" == "0" ]]; then
        OLD_READER_ROLLBACK_SAFE=true
        pass "no production IMAGE Fragment rows; old-reader rollback is not blocked by IMAGE data"
    else
        warn "${IMAGE_COUNT} production IMAGE Fragment row(s) exist; do not roll back to a reader that hides IMAGE Fragments"
    fi
else
    fail "could not determine production IMAGE Fragment count"
fi
printf 'old_reader_rollback_safe=%s\n' "${OLD_READER_ROLLBACK_SAFE}" > "${OUT}/rollback-state.txt"

sha256sum "${COMPOSE_FILE}" "${RESPONDER_CONFIG}" "${WEB_CONFIG}" "${ACL_FILE}" \
    > "${OUT}/runtime-config-sha256.txt"

if [[ "${MODE}" == "post" ]]; then
    # Internal readiness demonstrates that the reader has connected/subscribed/replayed.
    if compose exec -T diaries-web sh -c \
        'wget --quiet --output-document=- http://localhost:8082/diaries-web/health/ready' \
        > "${OUT}/web-readiness.json" 2> "${OUT}/web-readiness.err"; then
        pass "diaries-web readiness endpoint succeeded"
    else
        fail "diaries-web readiness endpoint failed"
    fi

    PUBLIC_WEB_BASE="$(jq -r '.http.publicBaseUrl' "${WEB_CONFIG}")"
    PUBLIC_RESPONDER_BASE="$(jq -r '.content.publicResponderBaseUrl' "${WEB_CONFIG}")"

    ROOT_STATUS="$(curl --silent --show-error --location --output /dev/null \
        --write-out '%{http_code}' "${PUBLIC_WEB_BASE}" || true)"
    printf '%s\n' "${ROOT_STATUS}" > "${OUT}/reader-root-status.txt"
    if [[ "${ROOT_STATUS}" == "200" ]]; then
        pass "public reader root returned HTTP 200"
    else
        fail "public reader root returned HTTP ${ROOT_STATUS:-<none>}"
    fi

    ABOUT_STATUS="$(curl --silent --show-error --location --output "${OUT}/reader-about.html" \
        --write-out '%{http_code}' "${PUBLIC_WEB_BASE}/about" || true)"
    printf '%s\n' "${ABOUT_STATUS}" > "${OUT}/reader-about-status.txt"
    if [[ "${ABOUT_STATUS}" == "200" ]]; then
        pass "public reader about page returned HTTP 200"
    else
        fail "public reader about page returned HTTP ${ABOUT_STATUS:-<none>}"
    fi

    MARQUEE_SAMPLE="$(db_query "SELECT p.diary_id || '|' || f.year || '|' || lpad(f.month::text,2,'0') || '|' || f.id FROM public.fragment f JOIN public.page p ON p.id=f.page_id WHERE COALESCE(f.type,'MARQUEE')='MARQUEE' ORDER BY f.year,f.month,f.day,f.sequence,f.id LIMIT 1;" 2>/dev/null || true)"
    if [[ -n "${MARQUEE_SAMPLE}" ]]; then
        IFS='|' read -r diary_id year month fragment_id <<< "${MARQUEE_SAMPLE}"
        MARQUEE_URL="${PUBLIC_WEB_BASE}/diaries/${diary_id}/${year}/${month}?fragment=${fragment_id}"
        MARQUEE_STATUS="$(curl --silent --show-error --location --output /dev/null \
            --write-out '%{http_code}' "${MARQUEE_URL}" || true)"
        printf '%s\n' "${MARQUEE_URL}" > "${OUT}/marquee-smoke-url.txt"
        printf '%s\n' "${MARQUEE_STATUS}" > "${OUT}/marquee-smoke-status.txt"
        if [[ "${MARQUEE_STATUS}" == "200" ]]; then
            pass "existing MARQUEE month/fragment reader smoke returned HTTP 200"
        else
            fail "existing MARQUEE reader smoke returned HTTP ${MARQUEE_STATUS:-<none>}"
        fi
    else
        warn "no MARQUEE Fragment sample was available for production smoke"
    fi

    IMAGE_ROUTE_OK=false
    : > "${OUT}/image-route-attempts.tsv"
    if [[ "${CATALOGUE_COUNT}" =~ ^[0-9]+$ && "${CATALOGUE_COUNT}" -gt 0 ]]; then
        while IFS= read -r relative_path; do
            [[ -n "${relative_path}" ]] || continue
            encoded_path="$(python3 - "${relative_path}" <<'PYENC'
import sys
from urllib.parse import quote
print('/'.join(quote(part, safe='') for part in sys.argv[1].split('/')))
PYENC
)"
            image_url="${PUBLIC_RESPONDER_BASE}/${FILES_PATH}/${encoded_path}"
            code="$(curl --silent --show-error --location --max-time 20 --output /dev/null \
                --write-out '%{http_code}' "${image_url}" || true)"
            printf '%s\t%s\n' "${code}" "${image_url}" >> "${OUT}/image-route-attempts.tsv"
            if [[ "${code}" == "200" ]]; then
                IMAGE_ROUTE_OK=true
                printf '%s\n' "${image_url}" > "${OUT}/image-route-success-url.txt"
                break
            fi
        done < <(db_query "SELECT relative_path FROM public.image ORDER BY id LIMIT 20;" 2>/dev/null || true)

        if [[ "${IMAGE_ROUTE_OK}" == "true" ]]; then
            pass "catalogued Image is reachable through the configured public Files route"
        else
            fail "no tested catalogue Image returned HTTP 200 through the public Files route"
        fi
    else
        warn "Image catalogue is empty; public Files route could not be exercised with catalogue data"
    fi
fi

# Machine-readable summary. No credentials are included.
jq -n \
  --arg mode "${MODE}" \
  --arg captured "$(date --iso-8601=seconds)" \
  --arg host "$(hostname -f 2>/dev/null || hostname)" \
  --arg expectedClient "${EXPECTED_CLIENT_IMAGE}" \
  --arg expectedWeb "${EXPECTED_WEB_IMAGE}" \
  --arg expectedResponder "${EXPECTED_RESPONDER_IMAGE}" \
  --arg filesPath "${FILES_PATH}" \
  --arg gate "${GATE}" \
  --arg imageFragments "${IMAGE_COUNT}" \
  --arg catalogueImages "${CATALOGUE_COUNT}" \
  --arg rollbackSafe "${OLD_READER_ROLLBACK_SAFE}" \
  --argjson failures "${failures}" \
  --argjson warnings "${warnings}" \
  '{
    mode: $mode,
    captured: $captured,
    host: $host,
    expectedImages: {client: $expectedClient, web: $expectedWeb, responder: $expectedResponder},
    filesPath: $filesPath,
    imageFragmentWritesEnabled: ($gate == "true"),
    imageFragmentRows: ($imageFragments | tonumber? // $imageFragments),
    imageCatalogueRows: ($catalogueImages | tonumber? // $catalogueImages),
    oldReaderRollbackSafe: ($rollbackSafe == "true"),
    failures: $failures,
    warnings: $warnings,
    passed: ($failures == 0)
  }' > "${OUT}/result.json"

( cd "${OUT}" && sha256sum -- * 2>/dev/null | grep -v 'SHA256SUMS.txt' > SHA256SUMS.txt ) || true

echo
echo "Evidence directory: ${OUT}"
if (( failures > 0 )); then
    echo "Step 15 ${MODE} verification: FAILED (${failures} failure(s), ${warnings} warning(s))"
    exit 1
fi
echo "Step 15 ${MODE} verification: PASSED (${warnings} warning(s))"
