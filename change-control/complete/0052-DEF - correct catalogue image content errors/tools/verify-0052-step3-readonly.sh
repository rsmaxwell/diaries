#!/usr/bin/env bash
# 0052-DEF Step 3: read-only catalogue/Files acceptance on Windows + pluto.
# Run in Windows 11 Cygwin Bash from the Diaries parent repository root.
# Writes evidence only inside change-control/in-progress/0052-DEF .../evidence/Step 3/private/.
# Does not modify any image, database, MQTT state or deployment.

(
    set -euo pipefail

    feature='change-control/in-progress/0052-DEF - correct catalogue image content errors'
    if [[ ! -f "$feature/IMPLEMENTATION-STEPS.md" ]]; then
        printf 'FAIL: Run from the Windows Diaries repository root; expected %s\n' "$feature" >&2
        exit 1
    fi
    command -v git >/dev/null || { echo 'FAIL: git not found' >&2; exit 1; }
    command -v docker >/dev/null || { echo 'FAIL: docker not found' >&2; exit 1; }
    command -v ssh >/dev/null || { echo 'FAIL: ssh not found' >&2; exit 1; }
    command -v sha256sum >/dev/null || { echo 'FAIL: sha256sum not found' >&2; exit 1; }

    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    out="$feature/evidence/Step 3/private/$stamp"
    mkdir -p "$out"
    printf '0052 Step 3 evidence: %s\n' "$out"

    # Useful traceability while leaving all local working files untouched.
    {
        printf 'Run timestamp UTC: %s\n' "$stamp"
        printf 'Windows working directory: %s\n' "$PWD"
        printf 'Parent branch: '; git branch --show-current
        printf 'Parent revision: '; git rev-parse HEAD
        printf '\nParent and submodule working-tree changes:\n'; git status --short
        printf '\nPinned / working submodule revisions:\n'; git submodule status
    } > "$out/checkout.txt" 2>&1

    read -r -d '' query <<'SQL' || true
SELECT id, version, relative_path, mime_type, width, height, checksum
FROM public.image
WHERE id IN (3, 18, 21, 25)
ORDER BY id;
SQL

    echo '=== Development catalogue (diaries-development-db) ==='
    printf '%s\n' "$query" |
        docker exec -i diaries-development-db sh -c \
        'psql -X -A -t -F "|" -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' \
        > "$out/development-catalogue.txt"
    cat "$out/development-catalogue.txt"

    echo '=== Production catalogue (pluto:diaries-postgres) ==='
    printf '%s\n' "$query" |
        ssh pluto "docker exec -i diaries-postgres sh -c 'psql -X -A -t -F \"|\" -v ON_ERROR_STOP=1 -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -f -'" \
        > "$out/production-catalogue.txt"
    cat "$out/production-catalogue.txt"

    # These checks compare catalogue metadata for the two corrected images
    # and the protected catalogue identities (St Isaac and Jordan Staircase).
    check_catalogue() {
        local file=$1 name=$2
        local id version relative mime width height sha
        local count=0
        while IFS='|' read -r id version relative mime width height sha; do
            case "$id" in
                3)
                    [[ "$relative" == 'diary-1828-and-1829-and-jan-1830/images/img2840-image-map-whitley-park.jpg' && \
                       "$mime" == 'image/jpeg' && "$width" == 776 && "$height" == 502 && \
                       "$sha" == '71263a0b4b8ed3bac18dd650d841c165a58f23d11717f7399b1139811b7b10fc' ]] || {
                        echo "FAIL: $name Image 3 metadata mismatch" >&2; return 1;
                    }
                    ((count+=1)) ;;
                18)
                    [[ "$relative" == 'diary-1828-and-1829-and-jan-1830/images/img2900-image-hermitage.png' && \
                       "$mime" == 'image/png' && "$width" == 720 && "$height" == 480 && \
                       "$sha" == '9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0' ]] || {
                        echo "FAIL: $name Image 18 metadata mismatch" >&2; return 1;
                    }
                    ((count+=1)) ;;
                21)
                    [[ "$sha" == '3f5d54daa8129b47f6f9e1c99ec74cc3997bdb439f30cae80e5e50fccec0cc08' ]] || {
                        echo "FAIL: $name protected Image 21 metadata mismatch" >&2; return 1;
                    }
                    ((count+=1)) ;;
                25)
                    [[ "$sha" == '2097979bd1ca47370a55c0f6053167a96f541a5c04adfe4ff52dc564ccc97d5a' ]] || {
                        echo "FAIL: $name protected Image 25 metadata mismatch" >&2; return 1;
                    }
                    ((count+=1)) ;;
                *) echo "FAIL: Unexpected $name image record ID $id" >&2; return 1 ;;
            esac
            [[ "$version" =~ ^[0-9]+$ ]] || { echo "FAIL: Invalid $name version for Image $id" >&2; return 1; }
        done < "$file"
        [[ "$count" -eq 4 ]] || { echo "FAIL: Expected 4 $name catalogue rows; found $count" >&2; return 1; }
        echo "PASS: $name catalogue entries 3,18,21,25"
    }
    check_catalogue "$out/development-catalogue.txt" Development
    check_catalogue "$out/production-catalogue.txt" Production

    # Windows P: is the mapped NAS 'photo' share; no remote NAS command required.
    content='/cygdrive/p/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content'
    diary='diary-1828-and-1829-and-jan-1830/images'
    check_file() {
        local environment=$1 root=$2 filename=$3 expected=$4
        local path="$content/$root/$diary/$filename"
        [[ -f "$path" ]] || { echo "FAIL: Missing $environment file $path" >&2; return 1; }
        local actual
        actual=$(sha256sum "$path")
        actual=${actual%% *}
        printf '%s | %s | %s | %s\n' "$environment" "$filename" "$actual" "$path" >> "$out/files-sha256.txt"
        [[ "$actual" == "$expected" ]] || { echo "FAIL: $environment $filename hash mismatch" >&2; return 1; }
        echo "PASS: $environment $filename"
    }
    : > "$out/files-sha256.txt"
    for root in files files-development-common; do
        check_file "$root" "$root" 'img2840-image-map-whitley-park.jpg' \
            '71263a0b4b8ed3bac18dd650d841c165a58f23d11717f7399b1139811b7b10fc'
        check_file "$root" "$root" 'img2900-image-hermitage.png' \
            '9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0'
        check_file "$root" "$root" 'img2903-image-st-isaac-church.png' \
            '2097979bd1ca47370a55c0f6053167a96f541a5c04adfe4ff52dc564ccc97d5a'
        check_file "$root" "$root" 'img2900-image-the-jordan-staircase-state-hermitage-museum-st-petersburg-russia-B2KPFE.jpg' \
            '3f5d54daa8129b47f6f9e1c99ec74cc3997bdb439f30cae80e5e50fccec0cc08'
    done

    cat > "$out/RESULT.txt" <<RESULT
PASS — 0052 Step 3 read-only database catalogue and NAS Files verification.
Timestamp UTC: $stamp
Production and development catalogue Images 3/18 match approved identity.
Protected catalogue Images 21/25 match their expected checksums.
Production and development Files copies all match expected checksums.
NOT TESTED HERE: retained MQTT topics; public Reader; development Editor visuals;
fragment ordering/Marquee; production responder logs; owner closure acceptance.
RESULT
    cat "$out/RESULT.txt"
) && { echo 'PASS: read-only verification completed'; exit 0; } \
  || { rc=$?; echo 'FAIL: read-only verification incomplete; see error and evidence under Step 3/private/' >&2; exit "$rc"; }
