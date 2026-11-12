#!/usr/bin/env bash
# 0046-FEAT Step 2: stage private inventory and private controller Git repositories.
# Run non-interactively on mango: bash -s -- --preflight / --apply, with stdin redirected to this file.
# Does NOT change /etc/ansible, the working Playbooks checkout, or managed hosts.
set -euo pipefail

MODE="${1:-}"
case "$MODE" in
  --preflight|--apply) ;;
  *) echo 'Usage: bash -s -- --preflight | --apply' >&2; exit 2 ;;
esac

OWNER='rsmaxwell'
INVENTORY_REPO="$OWNER/inventory"
CONTROLLER_REPO="$OWNER/ansible-controller"
PLAYBOOKS_REPO="$OWNER/playbooks"
PLAYBOOKS_DIR='/home/richard/playbooks'
CONTROLLER_DIR='/home/richard/ansible-controller'
INVENTORY_DIR="$CONTROLLER_DIR/inventory"
EXPECTED_PLAYBOOKS_SHA='dca638c00cc3b0fe2f2a46ef01c060cb1a1f6296'
INVENTORY_REMOTE="git@github.com:$INVENTORY_REPO.git"
CONTROLLER_REMOTE="git@github.com:$CONTROLLER_REPO.git"
PLAYBOOKS_REMOTE="git@github.com:$PLAYBOOKS_REPO.git"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
info() { printf '%s\n' "$*"; }
check_repo_absent_or_empty() {
  local repo="$1" ssh_remote="$2" output canonical private refs

  if output=$(gh api "repos/$repo" \
      --jq '[.full_name, (.private | tostring)] | @tsv' 2>&1); then

    IFS=$'\t' read -r canonical private <<< "$output"

    if [ "$canonical" != "$repo" ]; then
      if [ "$repo" = "$CONTROLLER_REPO" ] &&
         [ "$canonical" = "$PLAYBOOKS_REPO" ]; then
        info "PASS: $repo redirects to $PLAYBOOKS_REPO; new repository creation will be attempted"
        return 0
      fi
      fail "Unexpected repository redirect: $repo -> $canonical"
    fi

    [ "$private" = 'true' ] ||
      fail "$repo already exists but is not PRIVATE"

    refs=$(git ls-remote "$ssh_remote" 2>/dev/null) ||
      fail "$repo is private but cannot be read over Git SSH"

    [ -z "$refs" ] ||
      fail "$repo is non-empty; reconcile existing repository manually"

    info "PASS: existing $repo is PRIVATE and empty"
  else
    case "$output" in
      *'HTTP 404'*|*'404 Not Found'*)
        info "PASS: $repo is not currently accessible (HTTP 404); creation will be attempted"
        ;;
      *)
        fail "Cannot safely check $repo using GitHub API"
        ;;
    esac
  fi
}
create_if_absent() {
  local repo="$1" output canonical private create='false'

  if output=$(gh api "repos/$repo" \
      --jq '[.full_name, (.private | tostring)] | @tsv' 2>&1); then

    IFS=$'\t' read -r canonical private <<< "$output"

    if [ "$canonical" = "$repo" ]; then
      [ "$private" = 'true' ] ||
        fail "$repo exists but is not PRIVATE"
      info "PASS: $repo already exists and is PRIVATE"

    elif [ "$repo" = "$CONTROLLER_REPO" ] &&
         [ "$canonical" = "$PLAYBOOKS_REPO" ]; then
      info "INFO: Replacing old repository-name redirect for $repo"
      create='true'

    else
      fail "Unexpected repository redirect: $repo -> $canonical"
    fi
  else
    case "$output" in
      *'HTTP 404'*|*'404 Not Found'*)
        create='true'
        ;;
      *)
        fail "Cannot safely check $repo before creation"
        ;;
    esac
  fi

  if [ "$create" = 'true' ]; then
    gh repo create "$repo" --private \
      --description 'Ansible 0046 private repository' >/dev/null ||
      fail "Failed to create $repo"

    info "PASS: created PRIVATE $repo"
  fi

  output=$(gh api "repos/$repo" \
    --jq '[.full_name, (.private | tostring)] | @tsv') ||
    fail "Cannot verify $repo after creation"

  IFS=$'\t' read -r canonical private <<< "$output"

  [ "$canonical" = "$repo" ] ||
    fail "Repository identity mismatch: $repo -> $canonical"

  [ "$private" = 'true' ] ||
    fail "Privacy verification failed for $repo"
}

preflight() {
  local remote sha gh_login file_count
  info '=== 0046 three-repository staging: read-only preflight on mango ==='
  for binary in bash git gh ssh find wc; do command -v "$binary" >/dev/null 2>&1 || fail "Missing required executable: $binary"; done
  [ "$(id -un)" = 'richard' ] || fail 'Run as richard on mango, not as root or another user'
  [ -d "$PLAYBOOKS_DIR/.git" ] || [ -f "$PLAYBOOKS_DIR/.git" ] || fail "No Git checkout at $PLAYBOOKS_DIR"
  [ -d "$INVENTORY_DIR" ] || fail "Prepared inventory not found at $INVENTORY_DIR"
  [ ! -e "$CONTROLLER_DIR/.git" ] || fail "Controller working directory already has Git metadata: $CONTROLLER_DIR"
  [ ! -e "$INVENTORY_DIR/.git" ] || fail "Prepared inventory already has Git metadata: $INVENTORY_DIR"
  [ ! -e "$CONTROLLER_DIR/playbooks" ] || fail "Existing $CONTROLLER_DIR/playbooks must be reviewed before staging"
  [ ! -e "$CONTROLLER_DIR/.gitmodules" ] || fail "Existing $CONTROLLER_DIR/.gitmodules must be reviewed"
  [ ! -L "$INVENTORY_DIR" ] || fail 'Prepared inventory directory must not be a symlink'
  [ ! -L "$CONTROLLER_DIR" ] || fail 'Controller directory must not be a symlink'
  [ ! -L "$PLAYBOOKS_DIR" ] || fail 'Playbooks directory must not be a symlink'

  # The accepted prepared-inventory proof established 44 files. Require no additional files or symlinks.
  [ -z "$(find "$INVENTORY_DIR" -type l -print -quit)" ] || fail 'Prepared inventory contains symlinks; review required'
  file_count=$(find "$INVENTORY_DIR" -type f | wc -l | tr -d '[:space:]')
  [ "$file_count" = '44' ] || fail "Prepared inventory expected 44 files; found $file_count (review rather than silently proceeding)"
  [ -z "$(find "$INVENTORY_DIR" -mindepth 1 -name '.git' -print -quit)" ] || fail 'Unexpected nested Git metadata in inventory'
  [ -z "$(find "$CONTROLLER_DIR" -mindepth 1 -maxdepth 1 ! -name inventory -print -quit)" ] || fail 'Controller staging directory contains entries other than inventory/'
  info 'PASS: prepared 44-file inventory found; no staging Git repository exists'

  sha=$(git -C "$PLAYBOOKS_DIR" rev-parse --verify HEAD) || fail 'Cannot resolve Playbooks revision'
  [ "$sha" = "$EXPECTED_PLAYBOOKS_SHA" ] || fail "Playbooks SHA changed ($sha); expected $EXPECTED_PLAYBOOKS_SHA"
  [ -z "$(git -C "$PLAYBOOKS_DIR" status --porcelain=v1 --untracked-files=all)" ] || fail 'Playbooks checkout has uncommitted or untracked changes'
  remote=$(git -C "$PLAYBOOKS_DIR" remote get-url origin) || fail 'Playbooks origin remote missing'
  case "$remote" in
    'git@github.com:rsmaxwell/playbooks'|'git@github.com:rsmaxwell/playbooks.git'|\
    'ssh://git@github.com/rsmaxwell/playbooks'|'ssh://git@github.com/rsmaxwell/playbooks.git'|\
    'https://github.com/rsmaxwell/playbooks'|'https://github.com/rsmaxwell/playbooks.git') ;;
    *) fail "Unexpected Playbooks origin remote: $remote" ;;
  esac
  [ "$(gh repo view "$PLAYBOOKS_REPO" --json visibility --jq .visibility)" = 'PRIVATE' ] || fail 'Expected private GitHub Playbooks repository during migration'
  info "PASS: private Playbooks origin verified; clean frozen SHA $sha"

  gh auth status >/dev/null 2>&1 || fail 'GitHub CLI authentication is unavailable on mango (run gh auth login)'
  gh_login=$(gh api user --jq .login) || fail 'Cannot identify GitHub CLI identity'
  [ "$gh_login" = "$OWNER" ] || fail "GitHub CLI is authenticated as $gh_login, not expected owner $OWNER"
  [ -n "$(git config --global user.name 2>/dev/null || true)" ] || fail 'Set Git global user.name on mango before staging'
  [ -n "$(git config --global user.email 2>/dev/null || true)" ] || fail 'Set Git global user.email on mango before staging'
  git ls-remote "$PLAYBOOKS_REMOTE" HEAD >/dev/null 2>&1 || fail 'Git-over-SSH access to github.com is not available on mango'
  info 'PASS: GitHub CLI authenticated as repo owner; Git SSH and commit identity available'
  check_repo_absent_or_empty "$INVENTORY_REPO" "$INVENTORY_REMOTE"
  check_repo_absent_or_empty "$CONTROLLER_REPO" "$CONTROLLER_REMOTE"
  info 'PASS: all 0046 staging preflight checks passed; no mutations made'
}

preflight
[ "$MODE" = '--apply' ] || exit 0

info '=== 0046 staging apply: creating/publishing PRIVATE Git repositories ==='
info 'NOTE: do not blindly retry a partially completed apply; preserve evidence and reconcile.'
create_if_absent "$INVENTORY_REPO"
create_if_absent "$CONTROLLER_REPO"

# Commit the ALREADY REVIEWED prepared inventory, never the live /etc/ansible tree.
git -C "$INVENTORY_DIR" init -b main >/dev/null
git -C "$INVENTORY_DIR" remote add origin "$INVENTORY_REMOTE"
git -C "$INVENTORY_DIR" add -A
tracked_count=$(git -C "$INVENTORY_DIR" ls-files | wc -l | tr -d '[:space:]')
[ "$tracked_count" = '44' ] || fail "Only $tracked_count of the expected 44 inventory paths staged; check Git ignore rules (NOT pushed)"
git -C "$INVENTORY_DIR" commit -m '0046-FEAT: establish protected inventory baseline' >/dev/null
git -C "$INVENTORY_DIR" push -u origin main >/dev/null
[ "$(git ls-remote "$INVENTORY_REMOTE" refs/heads/main | awk '{print $1}')" = "$(git -C "$INVENTORY_DIR" rev-parse HEAD)" ] || fail 'Inventory remote commit does not match local commit'
info 'PASS: prepared encrypted inventory committed and pushed to PRIVATE repository'

# Compose parent using Git links rather than moving the operational Playbooks copy.
git -C "$CONTROLLER_DIR" init -b main >/dev/null
# Git can adopt a valid repository already checked out at inventory/ as a submodule.
git -C "$CONTROLLER_DIR" submodule add --force "$INVENTORY_REMOTE" inventory >/dev/null
git clone --no-checkout "$PLAYBOOKS_REMOTE" "$CONTROLLER_DIR/playbooks" >/dev/null
if ! git -C "$CONTROLLER_DIR/playbooks" cat-file -e "$EXPECTED_PLAYBOOKS_SHA^{commit}" 2>/dev/null; then
  git -C "$CONTROLLER_DIR/playbooks" fetch origin "$EXPECTED_PLAYBOOKS_SHA" >/dev/null
fi
git -C "$CONTROLLER_DIR/playbooks" checkout --detach "$EXPECTED_PLAYBOOKS_SHA" >/dev/null
git -C "$CONTROLLER_DIR" submodule add --force "$PLAYBOOKS_REMOTE" playbooks >/dev/null

git -C "$CONTROLLER_DIR" add .gitmodules inventory playbooks
git -C "$CONTROLLER_DIR" commit -m '0046-FEAT: establish private Ansible controller with pinned submodules' >/dev/null
git -C "$CONTROLLER_DIR" remote add origin "$CONTROLLER_REMOTE"
git -C "$CONTROLLER_DIR" push -u origin main >/dev/null
[ "$(git ls-remote "$CONTROLLER_REMOTE" refs/heads/main | awk '{print $1}')" = "$(git -C "$CONTROLLER_DIR" rev-parse HEAD)" ] || fail 'Controller remote commit does not match local commit'

[ "$(gh api "repos/$INVENTORY_REPO" --jq .private)" = 'true' ] || fail 'Published inventory repository is not PRIVATE'
[ "$(gh api "repos/$CONTROLLER_REPO" --jq .private)" = 'true' ] || fail 'Published controller repository is not PRIVATE'
[ "$(gh repo view "$PLAYBOOKS_REPO" --json visibility --jq .visibility)" = 'PRIVATE' ] || fail 'Playbooks repository is not PRIVATE during migration'
[ "$(git -C "$CONTROLLER_DIR/playbooks" rev-parse HEAD)" = "$EXPECTED_PLAYBOOKS_SHA" ] || fail 'Playbooks submodule SHA differs'
[ "$(git -C "$CONTROLLER_DIR" ls-tree HEAD inventory | awk '{print $1}')" = '160000' ] || fail 'Inventory is not a Git submodule'
[ "$(git -C "$CONTROLLER_DIR" ls-tree HEAD playbooks | awk '{print $1}')" = '160000' ] || fail 'Playbooks is not a Git submodule'
[ -z "$(git -C "$CONTROLLER_DIR" status --porcelain=v1 --untracked-files=all)" ] || fail 'Controller Git tree not clean'
[ -z "$(git -C "$INVENTORY_DIR" status --porcelain=v1 --untracked-files=all)" ] || fail 'Inventory Git tree not clean'
[ -z "$(git -C "$PLAYBOOKS_DIR" status --porcelain=v1 --untracked-files=all)" ] || fail 'Operational Playbooks checkout changed'

info "PASS: PRIVATE inventory repository at $INVENTORY_REPO"
info "PASS: PRIVATE controller repository at $CONTROLLER_REPO"
info "PASS: PRIVATE Playbooks submodule pinned to $EXPECTED_PLAYBOOKS_SHA"
info 'PASS: controller and submodule Git trees clean; repository staging complete'
info 'UNCHANGED: /etc/ansible, /home/richard/playbooks and managed host configurations'
info '0046 remains IN PROGRESS until estate-wide equivalence testing and controlled cutover'
