#!/usr/bin/env bash
# 0048: one controlled deployment + second-pass idempotence and installed-mode
# and filter hash checks. Invoked on mango from the Windows Diaries feature.
set -euo pipefail
controller=/home/richard/ansible-controller
playbooks="$controller/playbooks"
role="$playbooks/roles/backup-collection"
export ANSIBLE_CONFIG=/etc/ansible/ansible.cfg
export ANSIBLE_INVENTORY="$controller/inventory/hosts"

printf '%s\n' '0048 STEP 4 — DEPLOY AND VERIFY MARS BACKUP-COLLECTION USER/MACHINE TASKS'
printf 'UTC: %s HOST: %s\n' "$(date -u +%FT%TZ)" "$(hostname)"
cd "$controller"
[[ "$(git branch --show-current)" == main ]] || { echo 'FAIL: controller is not on main' >&2; exit 1; }
[[ -z "$(git status --porcelain --ignore-submodules=none)" ]] || { echo 'FAIL: controller/submodule checkout dirty' >&2; exit 1; }
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || { echo 'FAIL: controller not at published main' >&2; exit 1; }
[[ "$(git rev-parse HEAD:playbooks)" == "$(git -C playbooks rev-parse HEAD)" ]] || { echo 'FAIL: Playbooks checkout not pinned' >&2; exit 1; }
[[ "$(git -C playbooks rev-parse HEAD)" == "$(git -C playbooks rev-parse origin/main)" ]] || { echo 'FAIL: Playbooks not published' >&2; exit 1; }
[[ "$(git rev-parse HEAD:inventory)" == "$(git -C inventory rev-parse HEAD)" ]] || { echo 'FAIL: inventory pin mismatch' >&2; exit 1; }
[[ ! -e "$role/source-modes.json" ]] || { echo 'FAIL: obsolete source-modes.json remains' >&2; exit 1; }
[[ -f "$HOME/.vault_pass.txt" && -f "$ANSIBLE_INVENTORY" ]] || { echo 'FAIL: Ansible inventory/vault file unavailable' >&2; exit 1; }
cd "$playbooks"
python3 "$role/tests/verify-collection-source-modes.py"
ansible-playbook backup-collection.yaml --syntax-check --vault-password-file "$HOME/.vault_pass.txt"

printf '%s\n' '=== Recheck the exact expected task changes (check mode) ==='
# Permit only the two known rsync changes. If anything else would change, STOP.
ansible-playbook backup-collection.yaml --limit mars --tags user,machine \
  --check --vault-password-file "$HOME/.vault_pass.txt" 2>&1 | awk '
  /^TASK \[/ { task=$0 }
  /^changed: \[mars\]/ {
    if (task !~ /install_user_scripts \| Copy scripts/ &&
        task !~ /install_machine_scripts \| Copy files/) {
      print "FAIL: unexpected changed task in preview: " task > "/dev/stderr"
      unexpected=1
    }
    changed++
  }
  { print; fflush() }
  /^mars[[:space:]]*:/ { recap=1; if ($0 ~ /failed=0/ && $0 ~ /unreachable=0/ && $0 ~ /changed=2/) expected_recap=1 }
  END { if (unexpected || !recap || !expected_recap || changed!=2) exit 1 }
'
printf '%s\n' 'PASS: check-mode changed tasks are exactly the two approved rsync tasks'

printf '%s\n' '=== Rollback reference and predeployment modes ==='
printf 'ROLLBACK_PLAYBOOKS=df68a0e3bc57bae29a76f46a58c30835126d7f20\n'
printf 'CURRENT_PLAYBOOKS=%s\n' "$(git rev-parse HEAD)"
ssh -n mars 'sudo -n stat -c "%a %U:%G %n" /home/richard /root /home/richard/scripts/backup /home/richard/scripts/backup/home /root/scripts/backup /root/scripts/backup/home /root/scripts/backup/remote'

printf '%s\n' '=== Controlled live targeted Ansible deployment ==='
ansible-playbook backup-collection.yaml --limit mars --tags user,machine \
  --vault-password-file "$HOME/.vault_pass.txt"

printf '%s\n' '=== Second application must be fully idempotent ==='
ansible-playbook backup-collection.yaml --limit mars --tags user,machine \
  --vault-password-file "$HOME/.vault_pass.txt" 2>&1 | awk '
  {print; fflush()}
  /^mars[[:space:]]*:/ {
     recap=1
     if ($0 ~ /changed=0/ && $0 ~ /failed=0/ && $0 ~ /unreachable=0/) good=1
  }
  END { if (!recap || !good) exit 1 }
'
printf '%s\n' 'PASS: second live Ansible application changed=0, failed=0, unreachable=0'

printf '%s\n' '=== Verify nine deployed filter contents against current sources ==='
(
  cd "$role" || exit 1
  for part in backup/home backup-machine/home backup-machine/remote; do
    if [[ "$part" == backup/home ]]; then
      dest=/home/richard/scripts/backup/home
    elif [[ "$part" == backup-machine/home ]]; then
      dest=/root/scripts/backup/home
    else
      dest=/root/scripts/backup/remote
    fi
    for name in includes excludes-1 excludes-2; do
      sha="$(sha256sum "files/$part/$name" | awk '{print $1}')"
      printf '%s  %s/%s\n' "$sha" "$dest" "$name"
    done
  done
) | ssh mars 'sudo -n sha256sum --check -'

printf '%s\n' '=== Inspect installed modes, ancestry and backup scheduling ==='
ssh mars 'sudo -n bash -s' <<'MARSCHECK'
for path in \
  /home/richard /root \
  /home/richard/scripts/backup /home/richard/scripts/backup/home \
  /root/scripts/backup /root/scripts/backup/home /root/scripts/backup/remote; do
  stat -c '%a %U:%G %n' "$path" || exit 1
done
[[ "$(stat -c '%a' /home/richard)" == 750 && "$(stat -c '%a' /root)" == 700 ]] || exit 1
for path in \
  /home/richard/scripts/backup /home/richard/scripts/backup/home \
  /root/scripts/backup /root/scripts/backup/home /root/scripts/backup/remote; do
  [[ "$(stat -c '%a' "$path")" == 755 ]] || exit 1
  [[ "$(stat -c '%U:%G' "$path")" == 'richard:richard' ]] || exit 1
done
for path in \
  /home/richard/scripts/backup/home \
  /root/scripts/backup/home /root/scripts/backup/remote; do
  for name in includes excludes-1 excludes-2; do
    [[ "$(stat -c '%a' "$path/$name")" == 644 ]] || exit 1
    [[ "$(stat -c '%U:%G' "$path/$name")" == 'richard:richard' ]] || exit 1
  done
done
for path in \
  /home/richard/scripts/backup/backup.sh \
  /home/richard/scripts/backup/cron/backup.sh \
  /home/richard/scripts/backup/home/backup.sh \
  /root/scripts/backup/backup.sh \
  /root/scripts/backup/cron/backup.sh \
  /root/scripts/backup/home/backup.sh \
  /root/scripts/backup/remote/backup.sh; do
  [[ "$(stat -c '%a' "$path")" == 744 ]] || exit 1
done
# A named/default ACL would alter the accepted access model: reject drift.
for path in \
  /home/richard/scripts/backup /home/richard/scripts/backup/home \
  /root/scripts/backup /root/scripts/backup/home /root/scripts/backup/remote \
  /home/richard/scripts/backup/home/includes \
  /home/richard/scripts/backup/home/excludes-1 \
  /home/richard/scripts/backup/home/excludes-2 \
  /root/scripts/backup/home/includes \
  /root/scripts/backup/home/excludes-1 \
  /root/scripts/backup/home/excludes-2 \
  /root/scripts/backup/remote/includes \
  /root/scripts/backup/remote/excludes-1 \
  /root/scripts/backup/remote/excludes-2; do
  acl="$(getfacl -cp "$path")" || exit 1
  if printf '%s\n' "$acl" | grep -E '^(user|group):[^:]|^mask::|^default:'; then
    echo "FAIL: extended or default ACL on $path" >&2
    exit 1
  fi
done
[[ "$(stat -c '%a' /home/richard/scripts/backup/cron)" == 750 ]] || exit 1
[[ "$(stat -c '%a' /home/richard/log/backup)" == 750 ]] || exit 1
printf '%s\n' '=== Root backup cron (read-only) ==='
crontab -l -u root | grep -F '/root/scripts/backup/backup.sh' || exit 1
printf '%s\n' '=== Backup and snapshot timers (read-only) ==='
systemctl list-timers --all --no-pager | grep -E 'diaries-pull|btrfs|snapshot|backup' || true
printf '%s\n' 'PASS: installed permission and schedule checks'
MARSCHECK

printf '%s\n' 'PASS: 0048 targeted mars deployment, repeat idempotence and installed verification'
printf '%s\n' 'WARNING: Formal operational acceptance and change-control closure still require review of evidence.'
