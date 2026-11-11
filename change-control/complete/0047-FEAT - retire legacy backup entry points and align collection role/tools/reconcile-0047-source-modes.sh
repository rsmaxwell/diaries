#!/usr/bin/env bash
# Feature-specific per-source-mode recovery from 0047 rsync drift on mars.
# Execute from Windows Cygwin; do not source interactively.
set -euo pipefail
[[ ${1:-} == --apply && $# == 1 ]] || { echo 'Usage: reconcile-0047-source-modes.sh --apply' >&2; exit 2; }
root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
feature="$root/change-control/in-progress/0047-FEAT - retire legacy backup entry points and align collection role"
accepted="$root/change-control/complete/0045-FEAT - reorganise backup and Btrfs Ansible deployment"
baseline="$accepted/evidence/Step 1/baseline-20261111-111819Z"
collector="$accepted/tools/collect-0045-host-state.py"
comparator="$accepted/tools/compare-0045-installed-state.py"
final_test="$feature/tools/apply-0047-and-compare.sh"
stamp=$(date -u +%Y%m%d-%H%M%SZ)
out="$feature/evidence/Step 2/metadata-correction-$stamp"
mkdir -p "$out"
for host in mars backup; do [[ -s "$baseline/$host-installed-static.json" ]] || exit 1; done
[[ -s "$collector" && -s "$comparator" && -s "$final_test" ]] || exit 1

echo '=== Confirm clean published Playbooks source and exact source-mode preflight ==='
ssh mango 'cd /home/richard/playbooks &&
  test "$(git branch --show-current)" = main &&
  test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" &&
  test -z "$(git status --porcelain)" &&
  PYTHONDONTWRITEBYTECODE=1 python3 -B roles/backup-collection/tests/verify-collection-source-modes.py &&
  git rev-parse HEAD' | tee "$out/playbooks-source-and-modes.txt"

echo '=== Capture Docker signing key before corrective apply ==='
ssh mars 'sudo -n sha256sum /etc/apt/keyrings/docker.asc' | tee "$out/mars-docker-key-before.sha256"

echo '=== Synchronize corrected source modes using collection role (mars only) ==='
ssh mango 'cd /home/richard/playbooks && ANSIBLE_NOCOLOR=1 ansible-playbook backup-collection.yaml --limit mars --vault-password-file ~/.vault_pass.txt'     2>&1 | tee "$out/collection-metadata-correction.txt"

echo '=== Confirm the only permitted changes are the two collection copy tasks ==='
python3 - "$out/collection-metadata-correction.txt" <<'PYIN'
import re, sys
lines = open(sys.argv[1], encoding='utf-8').read().splitlines()
expected = {
    'backup-collection : install_user_scripts | Copy scripts',
    'backup-collection : install_machine_scripts | Copy files',
}
current = None
changed = []
for line in lines:
    m = re.match(r'^TASK \[(.*?)\]', line)
    if m:
        current = m.group(1)
    if re.match(r'^changed: \[mars\]', line):
        changed.append(current)
        if current not in expected:
            raise SystemExit(f'FAIL: unexpected changed task {current!r}')
recap = lines[-1:]
for i, line in enumerate(lines):
    if line.startswith('PLAY RECAP'):
        recap = lines[i+1:]
        break
matches = [re.findall(r'([a-z_]+)=(\d+)', line) for line in recap if re.match(r'^mars\s+:', line)]
if len(matches)!=1:
    raise SystemExit('FAIL: expected exactly one mars recap')
result = dict((k,int(v)) for k,v in matches[0])
if result.get('failed') != 0 or result.get('unreachable') != 0 or result.get('changed') != len(changed):
    raise SystemExit(f'FAIL: unexpected mars recap {result}; changed tasks {changed}')
if len(changed)>2 or len(set(changed))!=len(changed):
    raise SystemExit(f'FAIL: unexpected changed tasks {changed}')
print('PASS: corrective apply changed only known filter-copy tasks:', changed)
PYIN

echo '=== Compare installed state immediately after corrective apply ==='
for host in mars backup; do
  ssh "$host" 'sudo -n python3 -' < "$collector" > "$out/$host-installed-static.json"
done
python3 "$comparator" "$baseline" "$out" | tee "$out/post-correction-static-comparison.txt"

ssh mars 'sudo -n sha256sum /etc/apt/keyrings/docker.asc' | tee "$out/mars-docker-key-after.sha256"
cmp -s "$out/mars-docker-key-before.sha256" "$out/mars-docker-key-after.sha256"

echo '=== Consolidated second application: require changed=0 and full equivalence ==='
bash "$final_test" --apply 2>&1 | tee "$out/final-idempotence-and-health.txt"

echo 'PASS: 0047 source-mode preservation and final installation-equivalence verification'
echo "Evidence: $out"
