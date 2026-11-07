
#!/usr/bin/env bash
set -euo pipefail

# Run from Windows Cygwin.
# Copy 0040-FEAT historical test retirement evidence from mango.

HOST="mango"
FEATURE_NAME="0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage"

REMOTE_FEATURE="/home/richard/diaries/change-control/in-progress/$FEATURE_NAME"

# Derive the Windows feature directory from this script's location.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_FEATURE="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "$(basename "$LOCAL_FEATURE")" != "$FEATURE_NAME" ]]; then
    echo "FAIL: Script is not inside the expected 0040-FEAT tools directory"
    exit 1
fi

REMOTE_ARCHIVE="$REMOTE_FEATURE/tests/retired-step12-3"
LOCAL_ARCHIVE="$LOCAL_FEATURE/tests/retired-step12-3"

LOG_REL="evidence/Step 12/raw-logs"

LOG_FILES=(
    "step12-test-retirement-plan-20261107-115418.txt"
    "step12-test-retirement-apply-20261107-120508.txt"
)

echo "Source:      $HOST:$REMOTE_FEATURE"
echo "Destination: $LOCAL_FEATURE"
echo

# Verify the remote archive and evidence are present.
echo "=== Check remote files ==="

ssh "$HOST" \
    "test -f '$REMOTE_ARCHIVE/manifest.json'"

for name in "${LOG_FILES[@]}"; do
    ssh "$HOST" \
        "test -f '$REMOTE_FEATURE/$LOG_REL/$name'"
done

echo "PASS: Remote files found"


# Copy the historical archive safely, including into an existing directory.
echo
echo "=== Copy historical test archive ==="

mkdir -p "$LOCAL_FEATURE/tests"

# Download into a temporary directory first, without touching existing files.
STAGING="$(mktemp -d "$LOCAL_FEATURE/tests/.retired-step12-3-transfer.XXXXXXXX")"

scp -rp \
    "$HOST:$REMOTE_ARCHIVE" \
    "$STAGING/"

# Verify the downloaded archive and merge missing files only.
python3 - "$STAGING/retired-step12-3" "$LOCAL_ARCHIVE" <<'PY'
import hashlib
import json
import pathlib
import sys

source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])

manifest_file = source / "manifest.json"
manifest = json.loads(manifest_file.read_text())

assert manifest["schema"] == 2
assert len(manifest["files"]) == 146

if target.is_symlink() or (target.exists() and not target.is_dir()):
    raise RuntimeError("Unsafe destination archive directory")

records = []

# Validate everything before copying anything.
for item in manifest["files"]:
    relative = pathlib.Path(item["archive"])

    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"Unsafe archive path: {relative}")

    src = source / relative
    dst = target / relative

    if src.is_symlink() or not src.is_file():
        raise RuntimeError(f"Missing or unsafe source: {src}")

    expected = item["sha256"]
    actual = hashlib.sha256(src.read_bytes()).hexdigest()

    if actual != expected:
        raise RuntimeError(f"Source checksum mismatch: {relative}")

    # Check all existing destination components for symlinks.
    parent = target
    for part in relative.parts[:-1]:
        parent = parent / part
        if parent.is_symlink():
            raise RuntimeError(f"Unsafe destination directory: {parent}")

    if dst.is_symlink():
        raise RuntimeError(f"Unsafe destination file: {dst}")

    if dst.exists():
        if not dst.is_file():
            raise RuntimeError(f"Destination is not a file: {dst}")
        current = hashlib.sha256(dst.read_bytes()).hexdigest()
        if current != expected:
            raise RuntimeError(f"Conflicting existing file: {relative}")

    records.append((src, dst))

target_manifest = target / "manifest.json"
if target_manifest.is_symlink():
    raise RuntimeError("Unsafe existing manifest")
if target_manifest.exists():
    if target_manifest.read_bytes() != manifest_file.read_bytes():
        raise RuntimeError("Existing archive manifest differs")

# Copy missing files, leaving existing matching files unchanged.
target.mkdir(parents=True, exist_ok=True)

copied = 0

for src, dst in records:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        with dst.open("xb") as output:
            output.write(src.read_bytes())
        copied += 1

# Write manifest last.
if not target_manifest.exists():
    with target_manifest.open("xb") as output:
        output.write(manifest_file.read_bytes())

print(f"PASS: Archive reconciled; {copied} files copied")
print(f"PASS: {len(records)} archived files verified")
PY

# Remove only the temporary download after successful reconciliation.
rm -rf -- "$STAGING"

# Verify that the archive manifests match.
REMOTE_HASH="$(
    ssh "$HOST" "sha256sum '$REMOTE_ARCHIVE/manifest.json'" |
        awk '{print $1}'
)"

LOCAL_HASH="$(
    sha256sum "$LOCAL_ARCHIVE/manifest.json" |
        awk '{print $1}'
)"

if [[ "$REMOTE_HASH" != "$LOCAL_HASH" ]]; then
    echo "FAIL: Archive manifests differ"
    exit 1
fi

echo "PASS: Archive manifests match"

# Verify all archived files against the manifest.
echo
echo "=== Verify archived file checksums ==="

python3 - "$LOCAL_ARCHIVE" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text())

assert manifest["schema"] == 2
assert len(manifest["files"]) == 146

for record in manifest["files"]:
    relative = pathlib.Path(record["archive"])

    assert not relative.is_absolute()
    assert ".." not in relative.parts

    path = root / relative

    assert path.is_file(), f"Missing: {path}"

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == record["sha256"], \
        f"Checksum mismatch: {path}"

print("PASS: All 146 archived files verified")
PY

# Copy the evidence logs.
echo
echo "=== Copy evidence logs ==="

mkdir -p "$LOCAL_FEATURE/$LOG_REL"

for name in "${LOG_FILES[@]}"; do
    relative="$LOG_REL/$name"
    destination="$LOCAL_FEATURE/$relative"

    if [[ -e "$destination" ]]; then
        echo "Already exists: $name"
    else
        echo "Copying: $name"

        scp -p \
            "$HOST:$REMOTE_FEATURE/$relative" \
            "$destination"
    fi

    remote_hash="$(
        ssh "$HOST" \
            "sha256sum '$REMOTE_FEATURE/$relative'" |
            awk '{print $1}'
    )"

    local_hash="$(
        sha256sum "$destination" |
            awk '{print $1}'
    )"

    if [[ "$remote_hash" != "$local_hash" ]]; then
        echo "FAIL: Evidence checksum mismatch: $name"
        exit 1
    fi

    echo "PASS: $name"
done

echo
echo "=========================================="
echo "PASS: 0040-FEAT evidence synchronised"
echo "=========================================="
echo
echo "Archive: $LOCAL_ARCHIVE"
echo "Evidence: $LOCAL_FEATURE/$LOG_REL"
