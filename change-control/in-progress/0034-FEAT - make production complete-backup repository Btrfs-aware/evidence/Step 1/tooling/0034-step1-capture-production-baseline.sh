#!/usr/bin/env bash
set -uo pipefail

# 0034-FEAT Step 1 read-only production storage capture.
# Usage:
#   ./0034-step1-capture-production-baseline.sh [project-dir]
#
# This script MUST NOT create a backup, stop/start services, mutate mounts or
# change repository contents. It records the existing 0033 production state.

PROJECT_DIR="${1:-/home/richard/projects/diaries}"
BACKUP_ROOT="$PROJECT_DIR/data/dataset-backups/production"
RESTORE_ROOT="$PROJECT_DIR/data/dataset-restores/production"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
FAILED=0

section() {
    printf '\n===== %s =====\n' "$1"
}

run_capture() {
    local label="$1"
    shift
    printf '\n--- %s ---\n' "$label"
    printf '$'
    printf ' %q' "$@"
    printf '\n'
    "$@" 2>&1
    local rc=$?
    printf '[exit=%s]\n' "$rc"
    return "$rc"
}

require_file() {
    local path="$1"
    if [[ ! -f "$path" ]]; then
        printf 'ERROR: required file missing: %s\n' "$path"
        FAILED=1
    fi
}

require_dir() {
    local path="$1"
    if [[ ! -d "$path" ]]; then
        printf 'ERROR: required directory missing: %s\n' "$path"
        FAILED=1
    fi
}

section "0034 Step 1 production baseline"
printf 'captured_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'host=%s\n' "$(hostname -f 2>/dev/null || hostname)"
printf 'user=%s\n' "$(id -un)"
printf 'project_dir=%s\n' "$PROJECT_DIR"
printf 'backup_root=%s\n' "$BACKUP_ROOT"
printf 'restore_root=%s\n' "$RESTORE_ROOT"
uname -a

require_dir "$PROJECT_DIR"
require_dir "$BACKUP_ROOT"
require_dir "$RESTORE_ROOT"
require_file "$SCRIPTS_DIR/backup-dataset.sh"
require_file "$SCRIPTS_DIR/complete-dataset-manifest.py"

section "Resolved storage paths"
for path in "$PROJECT_DIR" "$BACKUP_ROOT" "$RESTORE_ROOT"; do
    if [[ -e "$path" ]]; then
        printf '%s -> %s\n' "$path" "$(readlink -f "$path")"
    fi
done

section "Mount and filesystem identity"
if command -v findmnt >/dev/null 2>&1; then
    run_capture "findmnt backup root" findmnt -T "$BACKUP_ROOT" -o TARGET,SOURCE,FSTYPE,OPTIONS || FAILED=1
else
    echo "findmnt not installed"
fi
run_capture "statfs backup root" stat -f -c 'path=%n fs_type=%T fs_id=%i block_size=%S total_blocks=%b free_blocks=%f available_blocks=%a' "$BACKUP_ROOT" || FAILED=1
run_capture "df human backup root" df -hT "$BACKUP_ROOT" || FAILED=1
run_capture "df bytes backup root" df -B1 "$BACKUP_ROOT" || FAILED=1

FS_TYPE="$(stat -f -c '%T' "$BACKUP_ROOT" 2>/dev/null || true)"
printf 'detected_fs_type=%s\n' "$FS_TYPE"
if [[ "$FS_TYPE" == "btrfs" ]]; then
    section "Btrfs baseline"
    if command -v btrfs >/dev/null 2>&1; then
        run_capture "btrfs filesystem show" btrfs filesystem show "$BACKUP_ROOT" || true
        run_capture "btrfs filesystem usage" btrfs filesystem usage -b "$BACKUP_ROOT" || true
        run_capture "btrfs filesystem du backup root" btrfs filesystem du -s "$BACKUP_ROOT" || true
    else
        echo "Filesystem reports btrfs but btrfs userspace command is unavailable."
    fi
else
    section "Btrfs baseline"
    echo "Current backup root is not reported as btrfs; this is a valid Step-1 baseline result."
fi

section "Current backup inventory"
LATEST=""
if [[ -d "$BACKUP_ROOT" ]]; then
    mapfile -t COMPLETE < <(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | grep -E '^[0-9]{8}-[0-9]{6}Z$' | sort || true)
    mapfile -t PARTIAL < <(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | grep -E '^\.[0-9]{8}-[0-9]{6}Z\.partial$' | sort || true)
    printf 'completed_count=%s\n' "${#COMPLETE[@]}"
    printf 'partial_count=%s\n' "${#PARTIAL[@]}"
    printf '%s\n' "${COMPLETE[@]:-}" | sed '/^$/d; s/^/completed=/'
    printf '%s\n' "${PARTIAL[@]:-}" | sed '/^$/d; s/^/partial=/'
    if (( ${#COMPLETE[@]} > 0 )); then
        LATEST="${COMPLETE[-1]}"
        printf 'latest_completed=%s\n' "$LATEST"
    else
        echo "ERROR: no completed schema-2 backup directory found"
        FAILED=1
    fi
fi

section "Newest completed backup validation"
if [[ -n "$LATEST" ]]; then
    run_capture "schema-2 validator" python3 "$SCRIPTS_DIR/complete-dataset-manifest.py" verify --backup-dir "$BACKUP_ROOT/$LATEST" || FAILED=1
    if [[ -f "$BACKUP_ROOT/$LATEST/dataset-manifest.json" ]]; then
        run_capture "manifest completion markers" python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p,encoding="utf-8")); print("schemaVersion="+str(d.get("schemaVersion"))); print("backupType="+str(d.get("backupType"))); print("completeDatasetBackup="+str(d.get("completeDatasetBackup"))); print("status="+str(d.get("status"))); print("backupId="+str(d.get("backupId"))); print("logicalDataset="+str(d.get("logicalDataset")))' "$BACKUP_ROOT/$LATEST/dataset-manifest.json" || FAILED=1
    fi
fi

section "0033 production preflight (read-only)"
if [[ -x "$SCRIPTS_DIR/backup-dataset.sh" ]]; then
    (cd "$PROJECT_DIR" && run_capture "backup-dataset.sh preflight" ./scripts/backup-dataset.sh preflight) || FAILED=1
else
    echo "ERROR: backup-dataset.sh is not executable"
    FAILED=1
fi

section "Deployed complete-dataset script SHA-256"
SCRIPT_NAMES=(
    backup-dataset.sh
    restore-dataset.sh
    production-complete-dataset.py
    complete-dataset-manifest.py
    complete-dataset-verification.py
    complete-dataset-restore-stage.py
    complete-dataset-postflight.py
)
for name in "${SCRIPT_NAMES[@]}"; do
    path="$SCRIPTS_DIR/$name"
    if [[ -f "$path" ]]; then
        sha256sum "$path"
    else
        echo "MISSING $path"
        FAILED=1
    fi
done

section "Mutation guard summary"
echo "This capture did not invoke backup creation, restore, stop.sh, start.sh, docker compose stop/start, mount, remount, cp, mv, rm or filesystem mutation commands."

section "Result"
if (( FAILED != 0 )); then
    echo "STEP-1 BASELINE CAPTURE FAILED: review errors above; no production mutation was requested by this script."
    exit 1
fi
echo "STEP-1 BASELINE CAPTURE PASSED"
