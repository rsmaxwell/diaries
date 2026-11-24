#!/usr/bin/env bash
# 0028 Step 1: run existing 0024 Java *dry-run only* against production.
# This standalone script is invoked on mango; set -e never touches interactive shell.
set -euo pipefail

usage() {
    echo 'Usage: step1_run_0024_dryrun.sh ABSOLUTE_PRIVATE_DERIVED_DIR' >&2
    exit 2
}
[[ $# == 1 ]] || usage
RUN_DIR="$(realpath -- "$1")"
[[ -d "$RUN_DIR" && -f "$RUN_DIR/0028-0024-candidates.PRIVATE.csv" ]] || usage
[[ -f "$RUN_DIR/SHA256SUMS.txt" ]] || usage
[[ ! -e "$RUN_DIR/0024-dry-run" ]] || { echo 'FAIL: local output already exists; use a new derived directory' >&2; exit 1; }
case "$(basename -- "$RUN_DIR")" in
    20[0-9][0-9][0-1][0-9][0-3][0-9]T[0-2][0-9][0-5][0-9][0-5][0-9]Z-0024) ;;
    *) echo 'FAIL: derived directory must be named YYYYMMDDTHHMMSSZ-0024' >&2; exit 2 ;;
esac
RUN_ID="$(basename -- "$RUN_DIR")"
SOURCE="$RUN_DIR/0028-0024-candidates.PRIVATE.csv"
(
    cd "$RUN_DIR"
    sha256sum -c SHA256SUMS.txt
)

# A unique scratch directory is necessary because the existing Java utility
# writes its evidence within the running container. Only this scratch dir
# is removed, and only after verified transfer to the Diaries feature.
REMOTE_NAME="0028-step1-$RUN_ID"
echo "Preparing protected temporary production evidence directory: $REMOTE_NAME"
ssh -T pluto "test ! -e \"\$HOME/temp/$REMOTE_NAME\" && ( umask 077; mkdir -p -- \"\$HOME/temp/$REMOTE_NAME/dry-run\" )"
ssh -T pluto "umask 077; cat > \"\$HOME/temp/$REMOTE_NAME/candidates.csv\"" < "$SOURCE"

echo 'Running existing 0024 Java reconciler in DRY-RUN mode only...'
ssh -T pluto bash -s -- "$REMOTE_NAME" <<'REMOTE'
set -euo pipefail
NAME="$1"
ROOT="$HOME/temp/$NAME"
cd "$HOME/projects/diaries"
test -r "$ROOT/candidates.csv"
test -r compose.yaml
test -r .env
test -r config/responder/responder.json
# Deployed Dockerfiles have used different jar locations; resolve inside image.
# --mode dry-run performs scanning and evidence creation, NOT Image INSERTs.
docker compose --file compose.yaml --env-file .env run \
  --rm --no-deps --no-tty --pull never \
  --entrypoint sh \
  --volume "$ROOT:/migration-evidence" \
  diaries-responder \
  -c '
    JAR=/opt/diaries/diaries-responder.jar
    if test ! -r "$JAR"; then JAR=/opt/diaries/lib/diaries-responder.jar; fi
    if test ! -r "$JAR"; then echo "FAIL: responder jar not present" >&2; exit 11; fi
    exec java -cp "$JAR" com.rsmaxwell.diaries.responder.migration.migration0024.Migration0024ImageCatalogue \
      --config /config/responder.json \
      --output /migration-evidence/dry-run \
      --mode dry-run \
      --0022-candidates /migration-evidence/candidates.csv
  '
test -f "$ROOT/dry-run/0024-summary.json"
test -f "$ROOT/dry-run/SHA256SUMS.txt"
(cd "$ROOT/dry-run" && sha256sum -c SHA256SUMS.txt)
REMOTE

# Preserve raw evidence on mango under the feature's ignored/private path.
mkdir -m 700 -- "$RUN_DIR/0024-dry-run"
(
    set -o pipefail
    ssh -T pluto "cd \"\$HOME/temp/$REMOTE_NAME/dry-run\" && tar -cf - ." |
        tar -xf - -C "$RUN_DIR/0024-dry-run"
)
(
    cd "$RUN_DIR/0024-dry-run"
    sha256sum -c SHA256SUMS.txt
)
python3 - "$RUN_DIR" <<'PY'
import csv
import json
import sys
from pathlib import Path
from collections import Counter
root = Path(sys.argv[1])
summary = json.loads((root/'0024-dry-run/0024-summary.json').read_text())
if summary.get('outcome') != 'DRY_RUN_COMPLETE' or summary.get('mode') != 'dry-run':
    raise SystemExit('FAIL: 0024 result was not an accepted dry-run')
with (root/'0024-dry-run/0024-candidate-cross-reference.csv').open(newline='',encoding='utf8') as f:
    rows = list(csv.DictReader(f))
with (root/'0028-0024-candidates.PRIVATE.csv').open(newline='',encoding='utf8') as f:
    candidates = list(csv.DictReader(f))
occ = json.loads((root/'0028-page-ownership-summary.json').read_text())['occurrenceRows']
if len(rows) != occ or len(candidates) == 0:
    raise SystemExit(f'FAIL: 0024 cross-reference coverage mismatch: {len(rows)} vs {occ}')
print('PASS: 0024 DRY-RUN_COMPLETE, evidence hashes verified')
print('Fragments:', len(candidates), 'source occurrences:', len(rows))
print('Cross-reference statuses:', dict(sorted(Counter(r['status'] for r in rows).items())))
print('Image Files-root statuses:', json.dumps(summary.get('counts',{}),sort_keys=True))
print('Evidence stored:', root/'0024-dry-run')
print('NOTICE: 0024 results are hints only; no 0028 decisions approved')
PY

# Copy verified and counts reconciled; remove only the newly-created temporary
# scratch tree (not any historic 0024 evidence, Files, database or snapshots).
ssh -T pluto "test -f \"\$HOME/temp/$REMOTE_NAME/candidates.csv\" && test -f \"\$HOME/temp/$REMOTE_NAME/dry-run/SHA256SUMS.txt\" && rm -rf -- \"\$HOME/temp/$REMOTE_NAME\""
echo 'PASS: production scratch evidence removed after verified copy to mango'
