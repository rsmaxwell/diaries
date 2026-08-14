#!/usr/bin/env bash
set -Eeuo pipefail

if (( BASH_VERSINFO[0] < 4 )); then
  echo "This script requires Bash 4 or later. Found: $BASH_VERSION" >&2
  exit 1
fi

PROGRAM_NAME=${0##*/}
ROOT_DIR="."
EXECUTE=false
OVERWRITE=false
DIARY_NAME=""

usage() {
  cat <<USAGE
Usage: $PROGRAM_NAME [--root DIR] [--execute] [--overwrite] <diary-name>

Moves the largest copy of each image filename from the old staging layout to:
  files/<diary-name>/images/

Dry-run is the default.
USAGE
}

while (($#)); do
  case "$1" in
    --root) ROOT_DIR=$2; shift 2 ;;
    --execute) EXECUTE=true; shift ;;
    --overwrite) OVERWRITE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *) [[ -z "$DIARY_NAME" ]] || { echo "Only one diary may be supplied" >&2; exit 2; }; DIARY_NAME=$1; shift ;;
  esac
done

[[ -n "$DIARY_NAME" ]] || { usage >&2; exit 2; }
ROOT_DIR=$(cd "$ROOT_DIR" && pwd -P)
OLD_DIARY_ROOT="$ROOT_DIR/files/staging/$DIARY_NAME"
SHARED_OLD_ROOT="$ROOT_DIR/files/images"
DESTINATION_DIR="$ROOT_DIR/files/$DIARY_NAME/images"

[[ -d "$OLD_DIARY_ROOT" ]] || { echo "Missing: $OLD_DIARY_ROOT" >&2; exit 1; }
$EXECUTE && mkdir -p "$DESTINATION_DIR"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
CANDIDATES="$TMP/candidates.nul"
SELECTED="$TMP/selected.nul"

find "$OLD_DIARY_ROOT" \
  -type d -name '@eaDir' -prune -o \
  -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o \
             -iname '*.gif' -o -iname '*.webp' -o -iname '*.svg' -o \
             -iname '*.tif' -o -iname '*.tiff' \) -print0 > "$CANDIDATES"

[[ -s "$CANDIDATES" ]] || { echo "No image files found"; exit 0; }

# Also consider same-named files in the old shared files/images directory.
#
# IMPORTANT: read the staged candidates from a separate, fixed file. Do not
# append to the same file being read, otherwise the loop keeps consuming its
# own appended output and may never finish.
STAGED_CANDIDATES="$TMP/staged-candidates.nul"
cp -- "$CANDIDATES" "$STAGED_CANDIDATES"

if [[ -d "$SHARED_OLD_ROOT" ]]; then
  # Search the shared old directory once for each distinct staged basename.
  declare -A staged_names=()

  while IFS= read -r -d '' staged; do
    name=${staged##*/}
    staged_names["$name"]=1
  done < "$STAGED_CANDIDATES"

  for name in "${!staged_names[@]}"; do
    find "$SHARED_OLD_ROOT" \
      -type d -name '@eaDir' -prune -o \
      -type f -name "$name" -print0
  done >> "$CANDIDATES"
fi

# Pick the largest file for each basename. For equal-sized files, use the
# lexically first path so the result is deterministic.
declare -A best_path=()
declare -A best_size=()

while IFS= read -r -d '' candidate; do
  name=${candidate##*/}
  size=$(stat -c '%s' "$candidate")

  if [[ -z ${best_path[$name]+present} ]] ||
     (( size > best_size[$name] )) ||
     { (( size == best_size[$name] )) && [[ "$candidate" < "${best_path[$name]}" ]]; }; then
    best_path["$name"]=$candidate
    best_size["$name"]=$size
  fi
done < "$CANDIDATES"

# Write the selected paths in sorted filename order. A temporary newline list
# is safe here because diary image filenames are not expected to contain
# literal newline characters.
NAMES="$TMP/names.txt"
printf '%s\n' "${!best_path[@]}" | LC_ALL=C sort > "$NAMES"

while IFS= read -r name; do
  printf '%s\0' "${best_path[$name]}"
done < "$NAMES" > "$SELECTED"

count=0
moved=0
skipped=0

$EXECUTE || echo "DRY RUN: add --execute to move files"
echo "Diary: $DIARY_NAME"
echo "Destination: $DESTINATION_DIR"
echo

while IFS= read -r -d '' source; do
  ((count+=1))
  name=${source##*/}
  target="$DESTINATION_DIR/$name"
  size=$(stat -c '%s' "$source")

  echo "Selected: $source"
  echo "Size:     $size bytes"
  echo "Target:   $target"

  if [[ -e "$target" && "$OVERWRITE" != true ]]; then
    echo "SKIP: target exists (use --overwrite after checking it)"
    ((skipped+=1))
  elif $EXECUTE; then
    if $OVERWRITE; then mv -f -- "$source" "$target"; else mv -- "$source" "$target"; fi
    echo "MOVED"
    ((moved+=1))
  else
    echo "WOULD MOVE"
  fi
  echo
done < "$SELECTED"

echo "Selected filenames: $count"
$EXECUTE && echo "Moved: $moved"
echo "Skipped: $skipped"
echo

echo "Unselected duplicate copies are deliberately left in place."
echo "Source material under diaries/$DIARY_NAME/metadata is untouched."
