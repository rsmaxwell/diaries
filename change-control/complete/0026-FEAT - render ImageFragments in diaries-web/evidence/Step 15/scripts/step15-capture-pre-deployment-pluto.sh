#!/usr/bin/env bash
#
# 0026-FEAT — Step 15
# Capture PRE-DEPLOYMENT production evidence on Pluto.
#
# Usage:
#   chmod +x step15-capture-pre-deployment-pluto.sh
#   ./step15-capture-pre-deployment-pluto.sh
#
# Optional overrides:
#   DIARIES_PROJECT_DIR=/home/richard/projects/diaries ./step15-capture-pre-deployment-pluto.sh
#   ./step15-capture-pre-deployment-pluto.sh /path/to/output-directory
#
# This script is read-only with respect to the Diaries application and database.
# It does NOT capture .env, password files, decrypted vault data, or full docker inspect output.

set -euo pipefail

STAMP="$(date +%Y%m%d-%H%M%S)"
PROJECT_DIR="${DIARIES_PROJECT_DIR:-$HOME/projects/diaries}"
OUT="${1:-$HOME/step15-pre-pluto-${STAMP}}"

COMPOSE_FILE="${PROJECT_DIR}/compose.yaml"
ENV_FILE="${PROJECT_DIR}/.env"
RESPONDER_CONFIG="${PROJECT_DIR}/config/responder/responder.json"
WEB_CONFIG="${PROJECT_DIR}/config/web/diaries-web.json"
ACL_FILE="${PROJECT_DIR}/config/mosquitto/aclfile.txt"

# Step 15 release candidate. These are recorded for context only during the PRE capture;
# the currently running containers are not required to match them yet.
EXPECTED_CLIENT_IMAGE="rsmaxwell/diaries-client:0.0.9-build-74"
EXPECTED_WEB_IMAGE="rsmaxwell/diaries-web:0.0.9-build-7"
EXPECTED_RESPONDER_IMAGE="rsmaxwell/diaries-responder:0.0.9-build-82"
EXPECTED_GIT_COMMIT="e5aa410bcf83e73f83bf81cb5aee9571ccba2755"

mkdir -p "${OUT}"

# Preserve the caller's stdout/stderr, then capture the evidence transcript through tee.
# We explicitly close and wait for tee before computing checksums so console.txt is final
# when SHA256SUMS.txt is generated.
exec 3>&1 4>&2
exec > >(tee "${OUT}/console.txt") 2>&1
TEE_PID=$!

failures=0
warnings=0

pass() { printf 'PASS: %s\n' "$*"; }
warn() { printf 'WARN: %s\n' "$*"; warnings=$((warnings + 1)); }
fail() { printf 'FAIL: %s\n' "$*"; failures=$((failures + 1)); }

need_command() {
    local cmd="$1"
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        fail "required command is not available: ${cmd}"
        return 1
    fi
}

require_file() {
    local path="$1"
    if [[ ! -f "${path}" ]]; then
        fail "required runtime file is missing: ${path}"
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
    local cid configured image_id state health started_at

    cid="$(compose ps -q "${service}" 2>/dev/null || true)"
    if [[ -z "${cid}" ]]; then
        fail "${service} has no running/created container"
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
            "${service}" '<missing>' '<missing>' '<missing>' '<missing>' '<missing>' \
            >> "${OUT}/container-identities.tsv"
        return
    fi

    configured="$(docker inspect --format '{{.Config.Image}}' "${cid}")"
    image_id="$(docker inspect --format '{{.Image}}' "${cid}")"
    state="$(docker inspect --format '{{.State.Status}}' "${cid}")"
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}' "${cid}")"
    started_at="$(docker inspect --format '{{.State.StartedAt}}' "${cid}")"

    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
        "${service}" "${configured}" "${image_id}" "${state}" "${health}" "${started_at}" \
        >> "${OUT}/container-identities.tsv"

    if [[ "${state}" != "running" ]]; then
        fail "${service} state is ${state}; expected running before deployment"
    elif [[ "${health}" != "healthy" && "${health}" != "n/a" ]]; then
        fail "${service} health is ${health}; expected healthy"
    else
        pass "${service} is ${state} (health=${health}, image=${configured})"
    fi
}

HOST_SHORT="$(hostname -s 2>/dev/null || hostname)"
HOST_FQDN="$(hostname -f 2>/dev/null || hostname)"
CAPTURED="$(date --iso-8601=seconds)"

printf '0026-FEAT — Step 15 PRE-DEPLOYMENT Pluto evidence\n'
printf 'captured: %s\n' "${CAPTURED}"
printf 'host: %s\n' "${HOST_FQDN}"
printf 'project: %s\n' "${PROJECT_DIR}"
printf 'output: %s\n\n' "${OUT}"

if [[ "${HOST_SHORT}" == "pluto" || "${HOST_FQDN}" == pluto.* ]]; then
    pass "running on Pluto (${HOST_FQDN})"
else
    warn "host is ${HOST_FQDN}, not obviously Pluto; verify that this is the intended production target"
fi

for cmd in docker jq awk grep sha256sum tar; do
    need_command "${cmd}" || true
done

for file in "${COMPOSE_FILE}" "${ENV_FILE}" "${RESPONDER_CONFIG}" "${WEB_CONFIG}" "${ACL_FILE}"; do
    require_file "${file}" || true
done

if (( failures > 0 )); then
    echo
    echo "Required commands/runtime files are missing; evidence capture cannot continue safely."
    exit 1
fi

cd "${PROJECT_DIR}"

# Basic host/runtime identity. Avoid environment dumps because they may contain secrets.
{
    printf 'captured=%s\n' "${CAPTURED}"
    printf 'hostname=%s\n' "${HOST_FQDN}"
    printf 'kernel=%s\n' "$(uname -srmo)"
    printf 'uptime=%s\n' "$(uptime -p 2>/dev/null || true)"
    printf 'docker=%s\n' "$(docker --version 2>/dev/null || true)"
    printf 'docker_compose=%s\n' "$(docker compose version 2>/dev/null || true)"
} > "${OUT}/host-runtime.txt"

cat > "${OUT}/release-candidate.txt" <<RC
step=15
production_target=pluto
git_commit=${EXPECTED_GIT_COMMIT}
diaries_client_image=${EXPECTED_CLIENT_IMAGE}
diaries_web_image=${EXPECTED_WEB_IMAGE}
diaries_responder_image=${EXPECTED_RESPONDER_IMAGE}
RC

if compose config --quiet; then
    pass "Docker Compose configuration is valid"
else
    fail "Docker Compose configuration is invalid"
fi

compose ps --all > "${OUT}/compose-ps.txt" || fail "could not capture Docker Compose status"
compose config --images > "${OUT}/compose-images.txt" || fail "could not capture configured image list"

printf 'service\tconfigured_image\timage_id\tstate\thealth\tstarted_at\n' > "${OUT}/container-identities.tsv"
container_record diaries-client
container_record diaries-web
container_record diaries-responder
container_record diaries-mqtt
container_record diaries-db

# Record selected public/non-secret configuration only.
if jq '{imageFragmentWritesEnabled}' "${RESPONDER_CONFIG}" > "${OUT}/responder-authoring-gate.json"; then
    pass "captured responder authoring-gate setting"
else
    fail "could not parse responder configuration"
fi

if jq '{http: {basePath: .http.basePath, publicBaseUrl: .http.publicBaseUrl}, content}' \
        "${WEB_CONFIG}" > "${OUT}/web-public-config.json"; then
    pass "captured non-secret diaries-web public/content configuration"
else
    fail "could not parse diaries-web configuration"
fi

GATE="$(jq -r 'if has("imageFragmentWritesEnabled") then (.imageFragmentWritesEnabled | tostring) else "<missing>" end' "${RESPONDER_CONFIG}")"
if [[ "${GATE}" == "false" ]]; then
    pass "ImageFragment production authoring gate is explicitly disabled"
else
    fail "imageFragmentWritesEnabled is ${GATE}; expected explicit false before production deployment"
fi

FILES_PATH="$(jq -r '.content.filesPath // "<missing>"' "${WEB_CONFIG}")"
if [[ "${FILES_PATH}" == "<missing>" ]]; then
    warn "pre-deployment diaries-web config has no explicit content.filesPath (this is expected if Step 15 has not yet been deployed)"
else
    pass "pre-deployment diaries-web config already has content.filesPath=${FILES_PATH}"
fi

# Capture only the diaries-web ACL stanza; never capture password-file contents.
awk '
  $1 == "user" { active = ($2 == "diaries-web") }
  active { print }
' "${ACL_FILE}" > "${OUT}/diaries-web-acl.txt"

if grep -Fxq 'topic deny diaries/rpc/#' "${OUT}/diaries-web-acl.txt" && \
   grep -Fxq 'topic read diaries/images/+' "${OUT}/diaries-web-acl.txt"; then
    pass "diaries-web ACL denies RPC and permits canonical Image reads"
else
    fail "diaries-web ACL is missing the expected RPC deny or diaries/images/+ read rule"
fi

if grep -Eq '^(topic|pattern)[[:space:]]+(write|readwrite)[[:space:]]' "${OUT}/diaries-web-acl.txt"; then
    fail "diaries-web ACL contains a write/readwrite rule"
else
    pass "diaries-web ACL contains no write/readwrite rule"
fi

# Database readiness and rollback evidence. These queries are read-only and capture counts only.
SCHEMA_COLUMNS="$(db_query "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name IN ('page_id','type','image_id');" 2>/dev/null || echo ERROR)"
IMAGE_TABLE="$(db_query "SELECT CASE WHEN to_regclass('public.image') IS NULL THEN 0 ELSE 1 END;" 2>/dev/null || echo ERROR)"
IMAGE_COUNT="$(db_query "SELECT count(*) FROM public.fragment WHERE type='IMAGE';" 2>/dev/null || echo ERROR)"
CATALOGUE_COUNT="$(db_query "SELECT count(*) FROM public.image;" 2>/dev/null || echo ERROR)"
MARQUEE_COUNT="$(db_query "SELECT count(*) FROM public.fragment WHERE COALESCE(type,'MARQUEE')='MARQUEE';" 2>/dev/null || echo ERROR)"

{
    printf 'fragment_required_columns=%s\n' "${SCHEMA_COLUMNS}"
    printf 'image_table_present=%s\n' "${IMAGE_TABLE}"
    printf 'image_fragment_rows=%s\n' "${IMAGE_COUNT}"
    printf 'marquee_fragment_rows=%s\n' "${MARQUEE_COUNT}"
    printf 'image_catalogue_rows=%s\n' "${CATALOGUE_COUNT}"
} > "${OUT}/database-readiness.txt"

if [[ "${SCHEMA_COLUMNS}" == "3" && "${IMAGE_TABLE}" == "1" ]]; then
    pass "0025 Fragment/Image production schema is present"
else
    fail "0025 schema readiness failed (fragment columns=${SCHEMA_COLUMNS}, image table=${IMAGE_TABLE})"
fi

OLD_READER_ROLLBACK_SAFE=false
if [[ "${IMAGE_COUNT}" =~ ^[0-9]+$ ]]; then
    if [[ "${IMAGE_COUNT}" == "0" ]]; then
        OLD_READER_ROLLBACK_SAFE=true
        pass "no production IMAGE Fragment rows; old-reader rollback is not blocked by IMAGE data"
    else
        warn "${IMAGE_COUNT} production IMAGE Fragment row(s) exist; an old reader that hides IMAGE Fragments is not a safe rollback target"
    fi
else
    fail "could not determine production IMAGE Fragment count"
fi
printf 'old_reader_rollback_safe=%s\n' "${OLD_READER_ROLLBACK_SAFE}" > "${OUT}/rollback-state.txt"

# Hash deployed runtime configuration without copying secret-bearing files into evidence.
sha256sum "${COMPOSE_FILE}" "${RESPONDER_CONFIG}" "${WEB_CONFIG}" "${ACL_FILE}" \
    > "${OUT}/runtime-config-sha256.txt"

# Machine-readable result summary.
jq -n \
  --arg mode "pre" \
  --arg captured "${CAPTURED}" \
  --arg host "${HOST_FQDN}" \
  --arg projectDir "${PROJECT_DIR}" \
  --arg expectedGitCommit "${EXPECTED_GIT_COMMIT}" \
  --arg expectedClient "${EXPECTED_CLIENT_IMAGE}" \
  --arg expectedWeb "${EXPECTED_WEB_IMAGE}" \
  --arg expectedResponder "${EXPECTED_RESPONDER_IMAGE}" \
  --arg filesPath "${FILES_PATH}" \
  --arg gate "${GATE}" \
  --arg imageFragments "${IMAGE_COUNT}" \
  --arg marqueeFragments "${MARQUEE_COUNT}" \
  --arg catalogueImages "${CATALOGUE_COUNT}" \
  --arg rollbackSafe "${OLD_READER_ROLLBACK_SAFE}" \
  --argjson failures "${failures}" \
  --argjson warnings "${warnings}" \
  '{
    step: 15,
    mode: $mode,
    captured: $captured,
    host: $host,
    projectDirectory: $projectDir,
    releaseCandidate: {
      gitCommit: $expectedGitCommit,
      client: $expectedClient,
      web: $expectedWeb,
      responder: $expectedResponder
    },
    preDeploymentConfiguration: {
      filesPath: $filesPath,
      imageFragmentWritesEnabled: ($gate == "true")
    },
    database: {
      imageFragmentRows: ($imageFragments | tonumber? // $imageFragments),
      marqueeFragmentRows: ($marqueeFragments | tonumber? // $marqueeFragments),
      imageCatalogueRows: ($catalogueImages | tonumber? // $catalogueImages)
    },
    oldReaderRollbackSafe: ($rollbackSafe == "true"),
    failures: $failures,
    warnings: $warnings,
    passed: ($failures == 0)
  }' > "${OUT}/result.json"

# Finish the captured transcript before hashing any evidence file.  This avoids
# the previous race where console.txt changed after SHA256SUMS.txt was written.
echo
if (( failures > 0 )); then
    echo "Step 15 PRE-deployment verification: FAILED (${failures} failure(s), ${warnings} warning(s))"
else
    echo "Step 15 PRE-deployment verification: PASSED (${warnings} warning(s))"
    echo "Preserve this evidence before running the production deployment."
fi

# Restore the caller's stdout/stderr. Closing the process-substitution pipe lets
# tee finish; wait for it so console.txt is guaranteed complete before hashing.
exec 1>&3 2>&4
exec 3>&- 4>&-
wait "${TEE_PID}"

# Checksums for the final evidence files, including the now-complete console.txt.
(
    cd "${OUT}"
    find . -maxdepth 1 -type f ! -name 'SHA256SUMS.txt' -printf '%f\n' \
        | sort \
        | xargs -r sha256sum \
        > SHA256SUMS.txt
)

ARCHIVE="${OUT}.tar.gz"
if tar -C "$(dirname "${OUT}")" -czf "${ARCHIVE}" "$(basename "${OUT}")"; then
    echo "PASS: created evidence archive ${ARCHIVE}"
else
    echo "WARN: could not create evidence archive; the evidence directory itself is complete"
fi

echo
echo "Evidence directory: ${OUT}"
echo "Evidence archive:   ${ARCHIVE}"

if (( failures > 0 )); then
    exit 1
fi
