#!/usr/bin/env bash
# Run in Windows Cygwin. Normal Ansible application; NEVER source this script.
set -euo pipefail
[[ ${1:-} == --apply && $# == 1 ]] || { echo 'Usage: apply-0047-and-compare.sh --apply' >&2; exit 2; }
root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
feature="$root/change-control/in-progress/0047-FEAT - retire legacy backup entry points and align collection role"
accepted="$root/change-control/complete/0045-FEAT - reorganise backup and Btrfs Ansible deployment"
baseline="$accepted/evidence/Step 1/baseline-20261111-111819Z"
collector="$accepted/tools/collect-0045-host-state.py"
comparator="$accepted/tools/compare-0045-installed-state.py"
stamp=$(date -u +%Y%m%d-%H%M%SZ)
out="$feature/evidence/Step 2/deployment-$stamp"
mkdir -p "$out"
for host in mars backup; do [[ -s "$baseline/$host-installed-static.json" ]] || exit 1; done
[[ -s $collector && -s $comparator ]] || exit 1

echo '=== Playbooks source preflight ==='
ssh mango 'cd /home/richard/playbooks &&
  test "$(git branch --show-current)" = main &&
  test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" &&
  test -z "$(git status --porcelain)" &&
  test -f roles/backup-collection/tasks/main.yaml &&
  test ! -e roles/local-backup &&
  test ! -e local-backup.yaml &&
  test ! -e remote-backup.yaml &&
  git rev-parse HEAD' | tee "$out/playbooks-source.txt"

ssh mars 'sudo -n sha256sum /etc/apt/keyrings/docker.asc' | tee "$out/mars-docker-key-before.sha256"

echo '=== Normal apply on mars (backup-collection) ==='
ssh mango 'cd /home/richard/playbooks && ANSIBLE_NOCOLOR=1 ansible-playbook backup-collection.yaml --limit mars --vault-password-file ~/.vault_pass.txt' \
  2>&1 | tee "$out/apply-backup-collection.txt"
echo '=== Normal apply on mars and backup (native replication) ==='
ssh mango 'cd /home/richard/playbooks && ANSIBLE_NOCOLOR=1 ansible-playbook btrfs-replication.yaml --limit mars,backup --vault-password-file ~/.vault_pass.txt' \
  2>&1 | tee "$out/apply-btrfs-replication.txt"

echo '=== Assert idempotent play recaps ==='
python3 - "$out/apply-backup-collection.txt" "$out/apply-btrfs-replication.txt" <<'PY'
import re,sys
for name,path,hosts in [('collection',sys.argv[1],{'mars'}),('replication',sys.argv[2],{'mars','backup'})]:
  text=open(path,encoding='utf-8').read().split('PLAY RECAP')[-1]
  matched={}
  for line in text.splitlines():
    for host in hosts:
      if re.match(r'^'+re.escape(host)+r'\s+:',line):
        fields=dict((key,int(value)) for key,value in re.findall(r'([a-z_]+)=(\d+)',line))
        matched[host]=fields
  if set(matched)!=hosts: raise SystemExit('FAIL: missing recap hosts for '+name)
  for host,fields in matched.items():
    if any(fields.get(k,-1)!=0 for k in ('changed','failed','unreachable')):
      raise SystemExit(f'FAIL: nonzero Ansible changes/errors for {name} {host}: {fields}')
    print(f'PASS: {name} on {host} changed=0 failed=0 unreachable=0')
PY

echo '=== Static installed-state comparison with accepted 0045 baseline ==='
for host in mars backup; do
  ssh "$host" 'sudo -n python3 -' < "$collector" > "$out/$host-installed-static.json"
done
python3 "$comparator" "$baseline" "$out" | tee "$out/installed-state-comparison.txt"

ssh mars 'sudo -n sha256sum /etc/apt/keyrings/docker.asc' | tee "$out/mars-docker-key-after.sha256"
cmp -s "$out/mars-docker-key-before.sha256" "$out/mars-docker-key-after.sha256" || { echo 'FAIL: Docker signing key changed'; exit 1; }

echo '=== Read-only Btrfs health ==='
for host in mars backup; do
  ssh "$host" 'sudo -n /usr/local/sbin/btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json status && sudo -n systemctl show btrfs-clear-stale-qgroups.service -p Result -p ExecMainStatus' > "$out/$host-snapshot-health.txt"
  echo "PASS: $host health command returned successfully"
done

echo 'PASS: 0047 normal apply idempotent, static installation equivalent and Docker key unchanged'
echo "Evidence: $out"
