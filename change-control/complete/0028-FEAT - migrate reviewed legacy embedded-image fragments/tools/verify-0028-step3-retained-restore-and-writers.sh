#!/usr/bin/env bash
# 0028: once-only verification of one accepted retained backup in a NEW disposable
# network-disabled Docker PostgreSQL. All mars/pluto/backup calls are READ-ONLY.
# Run as a standalone script in Windows Cygwin from the Diaries parent root.
set -euo pipefail
umask 077
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
reader="$feature/tools/step3_retained_restore_stream.py"
writer="$feature/tools/step3_writer_channel_inventory.py"
paired="$feature/evidence/Step 3/private/20261124T101320Z-retained-components/RETAINED-CONTENTS-RESULT.json"
backup_id='20261124-003112Z'
container='diaries-0028-retained-restore-db'
volume='diaries-0028-retained-restore-pgdata'
label='uk.co.rsmaxwell.diaries.0028.recovery=retained-20261124-003112Z'

if [[ ! -f "$feature/IMPLEMENTATION-STEPS.md" || ! -f "$reader" || ! -f "$writer" || ! -s "$paired" ]]; then
  echo 'FAIL: Diaries root/source scripts or previously accepted retained-pair evidence missing' >&2
  exit 2
fi
for c in ssh docker python3 git; do
  command -v "$c" >/dev/null 2>&1 || { echo "FAIL: missing $c" >&2; exit 2; }
done
# Do not repeat a possibly expensive restore or overwrite an existing Docker resource.
if docker container inspect "$container" >/dev/null 2>&1 || docker volume inspect "$volume" >/dev/null 2>&1; then
  echo "FAIL: dedicated retained-restore container/volume exists; refusing to recreate or overwrite it" >&2
  echo "Inspect the previous evidence or the labelled Docker resources instead." >&2
  exit 2
fi
docker image inspect postgres:18-alpine >/dev/null 2>&1 || {
  echo 'FAIL: postgres:18-alpine must already be available locally; no image pulls are authorised' >&2
  exit 2
}
echo '=== Offline source/identity regression checks (no SSH/Docker writes) ==='
python3 "$feature/tests/test_step3_retained_restore_and_writers.py"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="$feature/evidence/Step 3/private/${stamp}-retained-restore-and-writers"
mkdir -p "$out"
printf 'PRIVATE Step 3 recovery/writer evidence: %s\n' "$out"
{
  echo '=== Windows Diaries parent branch and revision ==='
  git branch --show-current
  git rev-parse HEAD
  git status --short
  echo '=== Submodule revision/status ==='
  git submodule status
  git -C diaries-responder status --short
} > "$out/WINDOWS-GIT-IDENTITY.txt" 2>&1 || {
  echo 'FAIL: cannot capture Windows Git checkout identity; no remote or Docker action attempted' >&2
  exit 2
}
printf 'Retained source: mars / production/%s\n' "$backup_id"

# Inspect actual live production writer routes. No changes to pluto.
echo '=== pluto: current production writer-channel inventory (READ-ONLY) ==='
if ssh -o BatchMode=yes -o RequestTTY=no -o ConnectTimeout=15 pluto 'python3 -' \
     < "$writer" > "$out/pluto-writer-channels.json" 2> "$out/pluto-writer-channels.err"; then
  echo 'PASS: captured database clients, published ports, restart policies and backup timer states'
else
  code=$?
  echo "FAIL: writer-channel inventory failed (exit $code); inspect private log" >&2
  exit 2
fi

# Both host identities were previously accepted; pin EXACT backup ID and manifest.
echo '=== mars: resolve the accepted immutable retained backup and hash sample Files (READ-ONLY) ==='
if ssh -o BatchMode=yes -o RequestTTY=no -o ConnectTimeout=15 mars \
    "sudo -n python3 - --inspect $backup_id" < "$reader" \
    > "$out/mars-retained-source.json" 2> "$out/mars-retained-source.err"; then
  echo 'PASS: retained custom dump descriptor and three sampled Files payloads checked'
else
  code=$?
  echo "FAIL: retained source inspection failed (exit $code); inspect private log" >&2
  exit 2
fi
python3 "$reader" --compare "$paired" "$out/mars-retained-source.json" "$out/BOUND-RESTORE-IDENTITY.json"
mapfile -t identities < <(python3 - "$out/BOUND-RESTORE-IDENTITY.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1],encoding='utf-8'))
for name in ('backupId','manifestSha256','customDumpSha256','customDumpBytes'):
 print(obj[name])
PY
)
if [[ "${#identities[@]}" -ne 4 || "${identities[0]}" != "$backup_id" ]]; then
  echo 'FAIL: unexpected source identity fields' >&2
  exit 2
fi

# Create a dedicated isolated verification target. No host ports, Docker network NONE,
# no production credentials. PostgreSQL must be writable *only* in its own new volume.
echo '=== Create clean network-disabled PostgreSQL 18 restore target on Windows Docker ==='
docker volume create --label "$label" "$volume" > "$out/docker-volume-created.txt"
docker run --detach --pull never --name "$container" --network none \
  --label "$label" --mount "type=volume,source=$volume,target=/var/lib/postgresql" \
  --env POSTGRES_DB=diaries --env POSTGRES_USER=postgres \
  --env POSTGRES_HOST_AUTH_METHOD=trust \
  postgres:18-alpine > "$out/docker-container-id.txt"
for i in $(seq 1 45); do
  if docker exec "$container" pg_isready -U postgres -d diaries >/dev/null 2>&1; then break; fi
  sleep 2
done
if ! docker exec "$container" pg_isready -U postgres -d diaries >/dev/null 2>&1; then
  echo 'FAIL: isolated PostgreSQL did not become ready; container retained' >&2
  exit 2
fi
port_bindings=$(docker inspect -f '{{json .HostConfig.PortBindings}}' "$container")
if [[ "$(docker inspect -f '{{.HostConfig.NetworkMode}}' "$container")" != none ||
      ( "$port_bindings" != '{}' && "$port_bindings" != 'null' ) ]]; then
  echo 'FAIL: restore container network or published-port isolation mismatch' >&2
  exit 2
fi
echo 'PASS: dedicated PostgreSQL container has no Docker network and no published ports'

# The remote Python validates the source identity *before* sending bytes, and verifies
# full dump SHA-256 at EOF. The local pg_restore writes ONLY to the isolated container.
echo '=== Stream the pinned retained custom dump from mars into isolated PostgreSQL ==='
set +e
ssh -o BatchMode=yes -o RequestTTY=no -o ConnectTimeout=15 mars \
  "sudo -n python3 - --stream ${identities[0]} ${identities[1]} ${identities[2]} ${identities[3]}" \
  < "$reader" 2> "$out/mars-stream-stderr.log" | \
  docker exec -i "$container" pg_restore --exit-on-error --no-owner --no-privileges \
    --username postgres --dbname diaries \
    > "$out/pg-restore.stdout.log" 2> "$out/pg-restore.stderr.log"
statuses=("${PIPESTATUS[@]}")
set -e
printf 'ssh_source_exit=%s\npg_restore_exit=%s\n' "${statuses[0]}" "${statuses[1]}" > "$out/RESTORE-EXIT-STATUS.txt"
if [[ "${statuses[0]}" -ne 0 || "${statuses[1]}" -ne 0 ]]; then
  echo "FAIL: retained dump stream/restore failed (SSH ${statuses[0]}, PostgreSQL ${statuses[1]})" >&2
  echo "Inspect private logs; the isolated target is retained and will NOT be overwritten" >&2
  exit 2
fi

echo '=== Read back restored database counts; do not run migration ==='
docker exec "$container" psql -X -v ON_ERROR_STOP=1 -U postgres -d diaries \
  -At -F '|' -c 'SELECT (SELECT count(*) FROM fragment),(SELECT count(*) FROM marquee),(SELECT count(*) FROM image),(SELECT count(*) FROM page);' \
  > "$out/RESTORED-COUNTS.txt"
python3 - "$out" <<'PY'
import json,pathlib,sys
out=pathlib.Path(sys.argv[1]); bound=json.loads((out/'BOUND-RESTORE-IDENTITY.json').read_text())
writer=json.loads((out/'pluto-writer-channels.json').read_text())
values=(out/'RESTORED-COUNTS.txt').read_text().strip().split('|')
assert len(values)==4 and all(x.isdigit() and int(x)>0 for x in values), 'invalid restored counts'
assert writer['writerIsolationVerified'] is False and writer['productionApplyAuthorised'] is False
report={'schema':1,'feature':'0028-FEAT','recoveryClass':'RETAINED_DB_RESTORE_VERIFIED',
        'databaseSourceHost':'mars','backupId':bound['backupId'],
        'manifestSha256':bound['manifestSha256'],'customDumpSha256':bound['customDumpSha256'],
        'restoredCounts':dict(zip(('fragments','marquees','images','pages'),map(int,values))),
        'filesPayloadSampleHashesVerified':3,'allFilesPayloadsVerified':False,
        'databaseRestoreVerified':True,'productionWriterIsolationVerified':False,
        'freshWriterStoppedRecoveryPointVerified':False,'productionApplyAuthorised':False}
(out/'READINESS-RESULT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS: retained backup custom dump fully restored to isolated network-disabled PostgreSQL')
print('Restored counts: fragments={fragments}, marquees={marquees}, images={images}, pages={pages}'.format(**report['restoredCounts']))
print('PASS: three retained Files payload checksums; full Files restore NOT verified')
print('OPEN: production writer isolation, final recovery point, owner approval')
print('PRIVATE receipt: '+str(out/'READINESS-RESULT.json'))
PY
echo 'Existing migration rehearsal, production backups and production services untouched.'
echo 'PASS: 0028 retained-dump recovery test and writer discovery complete; PRODUCTION APPLY NOT AUTHORISED'
