#!/usr/bin/env bash
# Windows Cygwin: read-only release-source provenance and content hashes.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
EVIDENCE="$FEATURE/evidence/step-3-release-source-manifest"
mkdir -p "$EVIDENCE" || exit 1
STAMP=$(date -u '+%Y%m%d-%H%M%S')
LOG="$EVIDENCE/source-$STAMP-$$.log"
(
  set -euo pipefail
  test -f .gitmodules || exit 1
  echo "Source manifest UTC=$(date -u '+%FT%TZ')"
  for repo in diaries-client diaries-responder diaries-web; do
    echo "=== $repo ==="
    git -C "$repo" rev-parse HEAD
    git -C "$repo" status --short --branch
    git -C "$repo" diff --check
    # Hash tracked modifications plus untracked files, excluding .gitignored output.
    (cd "$repo" && {
      git diff --name-only -z
      git ls-files --others --exclude-standard -z
    } | sort -zu | while IFS= read -r -d '' name; do
      if test -f "$name"; then sha256sum -- "$name"; fi
    done)
  done
  echo '=== Parent change-control / config source ==='
  git rev-parse HEAD
  git diff --check
  echo 'PASS: read-only source manifest; NO git add, commit or push performed'
) > "$LOG" 2>&1
rc=$?
cat "$LOG"
echo "Evidence: $LOG"
exit "$rc"
