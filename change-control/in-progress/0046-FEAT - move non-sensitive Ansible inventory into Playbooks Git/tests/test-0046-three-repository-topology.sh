#!/usr/bin/env bash
# Offline Git integration test for 0046 staging topology. Uses disposable local repositories only.
set -euo pipefail
base=$(mktemp -d)
trap 'rm -rf "$base"' EXIT
export GIT_CONFIG_GLOBAL="$base/gitconfig"
git config --global user.name '0046 test fixture'
git config --global user.email 'test@example.invalid'
git config --global protocol.file.allow always
mkdir -p "$base/remotes" "$base/controller/inventory" "$base/playbooks"
git init --bare "$base/remotes/inventory.git" >/dev/null
git init --bare "$base/remotes/playbooks.git" >/dev/null
git init --bare "$base/remotes/controller.git" >/dev/null
for i in $(seq 1 44); do printf '# encrypted fixture %s\n' "$i" > "$base/controller/inventory/file-$(printf '%02d' "$i").yaml"; done

git -C "$base/playbooks" init -b main >/dev/null
printf 'test\n' > "$base/playbooks/p.yaml"
git -C "$base/playbooks" add .
git -C "$base/playbooks" commit -m 'test public playbooks source' >/dev/null
play_sha=$(git -C "$base/playbooks" rev-parse HEAD)
git -C "$base/playbooks" remote add origin "$base/remotes/playbooks.git"
git -C "$base/playbooks" push -u origin main >/dev/null

git -C "$base/controller/inventory" init -b main >/dev/null
git -C "$base/controller/inventory" remote add origin "$base/remotes/inventory.git"
git -C "$base/controller/inventory" add -A
git -C "$base/controller/inventory" commit -m 'test prepared inventory baseline' >/dev/null
git -C "$base/controller/inventory" push -u origin main >/dev/null

git -C "$base/controller" init -b main >/dev/null
git -C "$base/controller" submodule add --force "$base/remotes/inventory.git" inventory >/dev/null
git clone --no-checkout "$base/remotes/playbooks.git" "$base/controller/playbooks" >/dev/null
git -C "$base/controller/playbooks" checkout --detach "$play_sha" >/dev/null
git -C "$base/controller" submodule add --force "$base/remotes/playbooks.git" playbooks >/dev/null
git -C "$base/controller" add .gitmodules inventory playbooks
git -C "$base/controller" commit -m 'test three-repository parent' >/dev/null
git -C "$base/controller" remote add origin "$base/remotes/controller.git"
git -C "$base/controller" push -u origin main >/dev/null

[ "$(git -C "$base/controller/playbooks" rev-parse HEAD)" = "$play_sha" ]
[ "$(git -C "$base/controller" ls-tree HEAD inventory | awk '{print $1}')" = 160000 ]
[ "$(git -C "$base/controller" ls-tree HEAD playbooks | awk '{print $1}')" = 160000 ]
[ -z "$(git -C "$base/controller" status --porcelain)" ]
[ -z "$(git -C "$base/controller/inventory" status --porcelain)" ]
[ -z "$(git -C "$base/playbooks" status --porcelain)" ]
printf 'PASS: synthetic three-repository submodules, detached frozen pin, pushes and clean trees\n'
