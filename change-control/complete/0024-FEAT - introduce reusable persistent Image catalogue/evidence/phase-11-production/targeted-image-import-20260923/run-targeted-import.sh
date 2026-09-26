#!/usr/bin/env bash

set -euo pipefail

EVIDENCE_DIR="${1:?usage: run-targeted-import.sh EVIDENCE_DIR}"
DATABASE_CONTAINER="diaries-postgres"
BACKUP_FILE="/home/richard/projects/diaries/data/database-backups/production/diaries-production-20260923-193936.sql"
EXPECTED_BACKUP_SHA256="a4a8757d47fe08b1fef374a503c274d376d38bbb9266c494382df6317e8a34c6"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ -d "${EVIDENCE_DIR}" ]] || fail "Evidence directory does not exist: ${EVIDENCE_DIR}"
[[ -f "${EVIDENCE_DIR}/correction.sql" ]] || fail "Correction SQL is missing"
[[ -f "${BACKUP_FILE}" ]] || fail "Production backup is missing"

actual_backup_sha256="$(sha256sum "${BACKUP_FILE}" | awk '{print $1}')"
[[ "${actual_backup_sha256}" == "${EXPECTED_BACKUP_SHA256}" ]] ||
    fail "Production backup checksum changed"

running_names="$(docker ps --format '{{.Names}}')"
grep -Fxq "${DATABASE_CONTAINER}" <<<"${running_names}" ||
    fail "Production database container is not running"
if grep -Eq '^diaries-(responder|client|web)$' <<<"${running_names}"; then
    fail "A production application writer is running"
fi

started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '%s  %s\n' "${actual_backup_sha256}" "${BACKUP_FILE}" > "${EVIDENCE_DIR}/backup-reference.txt"

docker exec "${DATABASE_CONTAINER}" \
    psql -X -U postgres -d diaries -v ON_ERROR_STOP=1 -At -F '|' \
    -c "SELECT count(*),min(id),max(id),md5(jsonb_agg(to_jsonb(i) ORDER BY id)::text) FROM public.image AS i;
        SELECT last_value,is_called FROM public.image_id_seq;
        SELECT id,version,page_id,type,year,month,day,sequence,md5(text) FROM public.fragment WHERE id IN (566,1461) ORDER BY id;" \
    > "${EVIDENCE_DIR}/before-state.txt"

set +e
docker exec -i "${DATABASE_CONTAINER}" \
    psql -X -U postgres -d diaries -v ON_ERROR_STOP=1 \
    < "${EVIDENCE_DIR}/correction.sql" \
    > "${EVIDENCE_DIR}/transaction.log" 2>&1
transaction_result=$?
set -e

cat "${EVIDENCE_DIR}/transaction.log"

if [[ ${transaction_result} -ne 0 ]]; then
    ended_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '{\n  "startedAtUtc": "%s",\n  "endedAtUtc": "%s",\n  "outcome": "FAILED",\n  "psqlExitCode": %d\n}\n' \
        "${started_at}" "${ended_at}" "${transaction_result}" \
        > "${EVIDENCE_DIR}/summary.json"
    (
        cd "${EVIDENCE_DIR}"
        find . -maxdepth 1 -type f ! -name SHA256SUMS.txt -printf '%P\0' |
            sort -z |
            xargs -0 sha256sum > SHA256SUMS.txt
    )
    exit "${transaction_result}"
fi

docker exec "${DATABASE_CONTAINER}" \
    psql -X -U postgres -d diaries -v ON_ERROR_STOP=1 -At -F '|' \
    -c "SELECT count(*),min(id),max(id),md5(jsonb_agg(to_jsonb(i) ORDER BY id)::text) FROM public.image AS i;
        SELECT count(*),md5(jsonb_agg(to_jsonb(i) ORDER BY id)::text) FROM public.image AS i WHERE id BETWEEN 72 AND 83;
        SELECT last_value,is_called FROM public.image_id_seq;
        SELECT id,version,page_id,type,year,month,day,sequence,md5(text) FROM public.fragment WHERE id IN (566,1461) ORDER BY id;" \
    > "${EVIDENCE_DIR}/after-state.txt"

docker exec "${DATABASE_CONTAINER}" \
    psql -X -U postgres -d diaries -v ON_ERROR_STOP=1 \
    -c "DO \$verify\$
        DECLARE
            complete_count bigint;
            complete_digest text;
            inserted_count bigint;
            inserted_digest text;
            sequence_value bigint;
            sequence_called boolean;
        BEGIN
            SELECT count(*),md5(jsonb_agg(to_jsonb(i) ORDER BY id)::text)
              INTO complete_count,complete_digest FROM public.image AS i;
            SELECT count(*),md5(jsonb_agg(to_jsonb(i) ORDER BY id)::text)
              INTO inserted_count,inserted_digest FROM public.image AS i WHERE id BETWEEN 72 AND 83;
            SELECT last_value,is_called INTO sequence_value,sequence_called FROM public.image_id_seq;
            IF complete_count <> 83 OR complete_digest <> 'a4e88f1911437b9ed31f98f9008de723'
               OR inserted_count <> 12 OR inserted_digest <> 'a60fd4ef85b4c2d7c2f1fbe180a2d04b'
               OR sequence_value <> 83 OR NOT sequence_called THEN
                RAISE EXCEPTION 'Post-import verification failed';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM public.fragment
                 WHERE id=566 AND version=3
                   AND md5(text)='88028219b08dd39f500e7ede406e3949'
            ) THEN
                RAISE EXCEPTION 'Fragment 566 changed unexpectedly';
            END IF;
        END
        \$verify\$;" \
    > "${EVIDENCE_DIR}/post-import-verification.txt"

ended_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '{\n  "startedAtUtc": "%s",\n  "endedAtUtc": "%s",\n  "outcome": "COMMITTED",\n  "insertedImageRows": 12,\n  "finalImageRows": 83,\n  "imageSequence": 83,\n  "fragment566Preserved": true,\n  "productionBackupSha256": "%s"\n}\n' \
    "${started_at}" "${ended_at}" "${actual_backup_sha256}" \
    > "${EVIDENCE_DIR}/summary.json"

(
    cd "${EVIDENCE_DIR}"
    find . -maxdepth 1 -type f ! -name SHA256SUMS.txt -printf '%P\0' |
        sort -z |
        xargs -0 sha256sum > SHA256SUMS.txt
)

echo "Targeted production Image import committed and verified."
