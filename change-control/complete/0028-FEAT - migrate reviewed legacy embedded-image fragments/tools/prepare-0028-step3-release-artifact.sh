#!/usr/bin/env bash
# Windows PC / Cygwin. Compile and pin a NEW, clean-source 0028 migration CLI JAR.
# Does not connect to any host, create a backup, or run the migration.
(
  set -euo pipefail
  umask 077
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  test -f "$feature/IMPLEMENTATION-STEPS.md" && test -f 'diaries-responder/build.gradle' || {
    echo 'FAIL: run from the Windows Diaries parent repository root' >&2; exit 2;
  }
  command -v git >/dev/null && command -v sha256sum >/dev/null && command -v python3 >/dev/null || {
    echo 'FAIL: requires git, sha256sum and python3 on PATH' >&2; exit 2;
  }
  test -x ./gradlew || { echo 'FAIL: Gradle wrapper is not executable' >&2; exit 2; }
  if ! git -C diaries-responder diff --quiet || ! git -C diaries-responder diff --cached --quiet ||
     test -n "$(git -C diaries-responder ls-files --others --exclude-standard)"; then
    echo 'FAIL: responder submodule has uncommitted/untracked source: commit intended code first; no files were changed by this script' >&2
    git -C diaries-responder status --short
    exit 2
  fi
  commit=$(git -C diaries-responder rev-parse HEAD)
  parent=$(git rev-parse HEAD)
  branch=$(git -C diaries-responder branch --show-current)
  test -n "$commit" && test -n "$parent" || { echo 'FAIL: missing Git revisions' >&2; exit 2; }
  echo '=== Build pinned responder fat JAR (does not deploy) ==='
  ./gradlew :diaries-responder:shadowJar --no-daemon
  mapfile -t jars < <(find diaries-responder/build/libs -maxdepth 1 -type f -name 'diaries-responder-*-fat.jar' -print)
  test "${#jars[@]}" -eq 1 || { echo 'FAIL: expected exactly one responder fat JAR; remove stale build variants manually if needed' >&2; exit 2; }
  # Inspect the JAR's ZIP central directory directly. On Windows, `jar tf`
  # outputs CRLF text, so `grep -Fx` can falsely report a missing class.
  python3 "$feature/tools/0028_step3_verify_jar_entries.py" "${jars[0]}"
  if test "$commit" != "$(git -C diaries-responder rev-parse HEAD)" ||
     test -n "$(git -C diaries-responder status --porcelain)"; then
    echo 'FAIL: responder changed while building; refusing to pin artifact' >&2; exit 2
  fi
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$feature/evidence/Step 3/private/${stamp}-release-artifact"
  test ! -e "$out" || { echo 'FAIL: refusing to overwrite release evidence' >&2; exit 2; }
  mkdir -p "$out"
  cp -- "${jars[0]}" "$out/diaries-0028-reviewed-migration-fat.jar"
  sha256sum "$out/diaries-0028-reviewed-migration-fat.jar" > "$out/migration-jar.sha256"
  {
    printf 'schema=1\nfeature=0028-FEAT\nsource_commit=%s\nsource_branch=%s\nparent_commit_at_build=%s\n' "$commit" "$branch" "$parent"
    printf 'artifact=diaries-0028-reviewed-migration-fat.jar\n'
    printf 'artifact_sha256=%s\n' "$(sha256sum "$out/diaries-0028-reviewed-migration-fat.jar" | awk '{print $1}')"
    printf 'status=BUILT_NOT_DEPLOYED_NOT_APPROVED\n'
  } > "$out/ARTIFACT-IDENTITY.txt"
  git status --short > "$out/parent-status.txt"
  git submodule status > "$out/submodule-status.txt"
  git -C diaries-responder status --short > "$out/responder-status.txt"
  printf 'PASS: pinned migration CLI built and hashed: %s\n' "$out"
  printf 'PENDING: runtime compatibility, writer isolation, fresh backup, owner approval. NO production work performed.\n'
)