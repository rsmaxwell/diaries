#!/usr/bin/env bash
# Windows Cygwin Bash; deliberately no persistent shell options.
(
  set -euo pipefail
  cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
  FEATURE="change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling"
  if [[ $# -ne 1 ]]; then echo "Usage: bash \"$FEATURE/tools/step2-49-audit-files.sh\" /path/to/diaries-content/files"; exit 2; fi
  ROOT="$1"
  TS="$(date -u +%Y%m%d-%H%M%S)"
  python3 "$FEATURE/tools/step2-49-audit-files.py" \
    --files-root "$ROOT" \
    --manifest "$FEATURE/reports/0029-49-placement-provisional-20261125.csv" \
    --output "$FEATURE/evidence/step-2-development-preflight/0029-49-image-file-audit-${TS}.csv"
) && echo 'PASS: image file audit runner' || { echo 'FAIL: image file audit runner (inspect output)'; false; }
