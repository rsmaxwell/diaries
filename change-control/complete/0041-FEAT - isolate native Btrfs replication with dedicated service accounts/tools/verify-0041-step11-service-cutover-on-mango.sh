#!/usr/bin/env bash
# 0041 Step 11: durable, Ansible-managed canonical unit transition or rollback.
# Runs only as a fresh, non-interactive bash process on mango; nested ssh -n.
set -Eeuo pipefail
# The Step 11 Ansible controller must use UTF-8, not the POSIX C locale.
mode="${1:-}"
[[ $# == 1 && ( "$mode" == --preflight || "$mode" == --execute || "$mode" == --rollback ) ]] || { echo 'Usage: --preflight|--execute|--rollback' >&2; exit 64; }
fail() { echo "FAIL: $*" >&2; exit 1; }
[[ $(hostname -s) == mango ]] || fail 'Run only on mango'
cd /home/richard/ansible-controller/playbooks || fail 'Playbooks working copy missing'

printf '0041 STEP 11 %s: %s UTC on mango\n' "$mode" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo 'SCOPE: canonical sender service unit only; no transfer, timer change or agreed-parent edits'
echo '=== Verify source, controller checkout, and inventory ==='
[[ $(git rev-parse --abbrev-ref HEAD) == main ]] || fail 'Unexpected Playbooks branch'
git status --short
printf 'Playbooks HEAD: '; git rev-parse HEAD
printf 'Inventory HEAD: '; git -C ../inventory rev-parse HEAD
git submodule status 2>/dev/null || true

if [[ "$mode" != --rollback ]]; then
  # Exact ZIP review artefacts; refuse if a different source version is deployed.
  check_file() {
    local expected="$1" file="$2" actual
    [[ -f "$file" ]] || fail "Missing reviewed Playbooks file: $file"
    actual=$(sha256sum "$file" | awk '{print $1}')
    [[ "$actual" == "$expected" ]] || fail "Unexpected Playbooks changes: $file"
    echo "PASS: reviewed source $file"
  }
  check_file d07750d266fd500945bfc2eb8bb8f3f8b8dcec4f54e01e1cecca2c8e2b643560 roles/btrfs-replication/README-0041-DEDICATED-IDENTITIES.md
  check_file c5165b1696d39febf850f1a5d49a1fe4911031500cc91ddc07e30afb62dea749 roles/btrfs-replication/defaults/main.yaml
  check_file f65c3ab33324bf2880546ee9f2f19cda0509974b1d959a6da8e1a16b19f06801 roles/btrfs-replication/tasks/source-scheduling.yaml
  check_file f12f00585c8b324bd6a728bb9bf93f732d8a26295aacebef9c69f0482428d636 roles/btrfs-replication/templates/btrfs-native-push.service.j2
fi

# Retain the already proven dedicated transport and privileged gates.
check_installed() {
  local host="$1" file="$2" expected="$3" actual
  actual=$(ssh -n -o BatchMode=yes "$host" "sha256sum '$file'" | awk '{print $1}')
  [[ "$actual" == "$expected" ]] || fail "Installed program changed on $host:$file"
}
check_installed mars /usr/local/bin/btrfs-simplified-replication 01bc877c52ef1051f2f00d4058d740c53af34e1c4cb2545a3e066a6530787a20
check_installed backup /usr/local/bin/btrfs-simplified-replication 01bc877c52ef1051f2f00d4058d740c53af34e1c4cb2545a3e066a6530787a20
check_installed mars /usr/local/libexec/btrfs-replication-sender-cycle-0041 334cc199ef36465dae2d8c817b676fc47e534807f7a0358a231190dd4d22e76a
check_installed backup /usr/local/libexec/btrfs-replication-receiver-gate-0041 689f7ba5bc067859f745704c7b2e298814a7fe71918d058747542931ef6c68bc
check_installed backup /usr/local/libexec/btrfs-replication-ssh-dispatch-0041 8f1f602a8f695e01df984ce58d2de9d6d841799d0b9ab843f1ed91b59c35706f

echo '=== Capture service/timer and protected state BEFORE ==='
service_before=$(ssh -n -o BatchMode=yes mars 'systemctl cat btrfs-native-push.service') || fail 'Cannot inspect service'
timer_before=$(ssh -n -o BatchMode=yes mars 'systemctl cat btrfs-native-push.timer') || fail 'Cannot inspect timer'
[[ "$timer_before" == *'OnCalendar=*-*-* 03:30:00 UTC'* ]] || fail 'Unexpected production timer calendar'
[[ $(ssh -n mars 'systemctl is-active btrfs-native-push.timer') == active ]] || fail '03:30 timer not active'
[[ $(ssh -n mars 'systemctl is-enabled btrfs-native-push.timer') == enabled ]] || fail '03:30 timer not enabled'
[[ $(ssh -n mars 'systemctl is-active btrfs-native-push.service || true') != active ]] || fail 'Sender is active; refuse cutover'
[[ $(ssh -n backup 'systemctl is-active btrfs-receiver-simple-prune.service || true') != active ]] || fail 'Receiver prune active; refuse cutover'
[[ $(ssh -n mars 'systemctl is-active btrfs-snapshot-prune.service || true') != active ]] || fail 'Source prune active; refuse cutover'
[[ $(ssh -n mars 'systemctl is-active btrfs-snapshot-create.service || true') != active ]] || fail 'Source snapshot creation active; refuse cutover'

if [[ "$mode" == --rollback ]]; then
  [[ "$service_before" == *'User=btrfs-send'* && "$service_before" == *'ExecStart=/usr/bin/sudo -n /usr/local/libexec/btrfs-replication-sender-cycle-0041'* ]] || fail 'Canonical service is not the reviewed dedicated version'
else
  [[ "$service_before" == *'User=root'* && "$service_before" == *'ExecStart=/usr/local/bin/btrfs-simplified-replication sender cycle'* ]] || fail 'Canonical service is not the reviewed legacy version'
fi

old_source=$(ssh -n mars 'sudo -n sha256sum /media/usb/@snapshots/.simple-agreed-parent.json' | awk '{print $1}')
old_receiver=$(ssh -n backup 'sudo -n sha256sum /@data/mars-received/.replication-state/.simple-agreed-parent.json' | awk '{print $1}')
[[ "$old_source" =~ ^[0-9a-f]{64}$ && "$old_source" == "$old_receiver" ]] || fail 'Source and receiver agreed-parent records differ'
echo "Agreed-parent state sha256: $old_source"
old_source_perms=$(ssh -n mars 'sudo -n stat -c "%U:%G %a %n" /media/usb/@snapshots/.simple-agreed-parent.json /run/lock/btrfs-snapshot-manager.lock')
old_receiver_perms=$(ssh -n backup 'sudo -n stat -c "%U:%G %a %n" /@data/mars-received/.replication-state/.simple-agreed-parent.json /@data/mars-received/.replication-state/writer.lock')

# Confirm independent dedicated status, without running a transfer.
status=$(ssh -n mars 'sudo -n env BTRFS_REPLICATION_IDENTITY_MODE=dedicated /usr/local/bin/btrfs-simplified-replication sender status') || fail 'Dedicated status failed'
python3 -c 'import json,sys; d=json.loads(sys.argv[1]); assert d["receiver_parent_verified"] is True and d["relation"]=="equal" and d["state"]==d["receiver"]; print("PASS: agreed parent verified through dedicated transport")' "$status" || fail 'Unstable parent state'

# No cutover during a period likely to collide with scheduled backup.
window_ok=$(python3 -c '
from datetime import datetime,timedelta,timezone
now=datetime.now(timezone.utc)
future=now.replace(hour=3,minute=30,second=0,microsecond=0)
if future <= now: future+=timedelta(days=1)
print("yes" if (future-now).total_seconds()>3600 else "no")
') || fail 'Schedule window calculation failed'
[[ "$window_ok" == yes ]] || fail 'Less than one hour until 03:30 schedule'

source /home/richard/ansible-controller/enter.sh
cd /home/richard/ansible-controller/playbooks || fail 'Cannot enter Playbooks after environment setup'
# Ansible refuses POSIX/C/non-UTF-8 locales. Select an installed locale only
# after enter.sh, since the controller environment setup may change variables.
ensure_ansible_utf8_locale() {
  local candidate reported
  for candidate in C.UTF-8 C.utf8 en_GB.UTF-8 en_US.UTF-8; do
    if LANG="$candidate" LC_ALL="$candidate" python3 -c \
      'import locale,sys; sys.exit(0 if locale.nl_langinfo(locale.CODESET).replace("-", "").lower() == "utf8" else 1)' \
      >/dev/null 2>&1; then
      export LANG="$candidate" LC_ALL="$candidate"
      reported=$(python3 -c 'import locale; print(locale.nl_langinfo(locale.CODESET))')
      echo "PASS: Ansible controller locale LANG=$LANG LC_ALL=$LC_ALL codeset=$reported"
      return 0
    fi
  done
  fail "No usable UTF-8 locale installed on mango (locale -a: $(locale -a | tr '\n' ' '))"
}
ensure_ansible_utf8_locale

if [[ "$mode" == --rollback ]]; then
  echo '=== Explicit rollback: restore legacy identity in active unit and in permanent role default ==='
  # Extra-vars force legacy rendering before touching the role default.
  ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --tags scheduling \
    -e btrfs_native_sender_service_identity=legacy --vault-password-file "$HOME/.vault_pass.txt" || fail 'Legacy service restoration failed'
  [[ $(ssh -n mars 'systemctl show btrfs-native-push.service -p User --value') == root ]] || fail 'Legacy service did not load as root'
  # Change only one exact line in Playbooks source; preserve all other local edits.
  python3 - <<'PYEDIT'
from pathlib import Path
p=Path('roles/btrfs-replication/defaults/main.yaml')
s=p.read_text()
a='btrfs_native_sender_service_identity: dedicated\n'
b='btrfs_native_sender_service_identity: legacy\n'
if s.count(a)!=1 or b in s:
    raise SystemExit('FAIL: source default unexpected; edit manually to keep rollback persistent')
p.write_text(s.replace(a,b))
print('PASS: durable role default restored to legacy (review and commit this source change)')
PYEDIT
else
  echo '=== Controlled scheduling-only Ansible preview (read-only) ==='
  ansible-playbook btrfs-replication.yaml --check --diff --limit 'mars,backup' \
    --tags scheduling --vault-password-file "$HOME/.vault_pass.txt" || fail 'Ansible check-mode preview failed'
  if [[ "$mode" == --preflight ]]; then
    echo 'PASS: 0041 Step 11 preflight completed; no production changes'
    exit 0
  fi
  echo '=== Deploy canonical dedicated sender service (timer schedule unchanged) ==='
  ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --tags scheduling \
    --vault-password-file "$HOME/.vault_pass.txt" || fail 'Ansible cutover failed; review live unit before rollback'
fi

echo '=== Independent post-change verification ==='
service_after=$(ssh -n mars 'systemctl cat btrfs-native-push.service')
user_after=$(ssh -n mars 'systemctl show btrfs-native-push.service -p User --value')
exec_after=$(ssh -n mars 'systemctl show btrfs-native-push.service -p ExecStart --value')
load_after=$(ssh -n mars 'systemctl show btrfs-native-push.service -p LoadState --value')
[[ "$load_after" == loaded ]] || fail 'Canonical service failed systemd load'
if [[ "$mode" == --rollback ]]; then
  [[ "$user_after" == root && "$service_after" == *'ExecStart=/usr/local/bin/btrfs-simplified-replication sender cycle'* ]] || fail 'Legacy service not restored'
else
  [[ "$user_after" == btrfs-send ]] || fail 'Dedicated service user not loaded'
  [[ "$service_after" == *'ExecStart=/usr/bin/sudo -n /usr/local/libexec/btrfs-replication-sender-cycle-0041'* ]] || fail 'Dedicated service ExecStart missing'
  [[ "$exec_after" == *'/usr/local/libexec/btrfs-replication-sender-cycle-0041'* ]] || fail 'Loaded ExecStart differs'
fi
[[ $(ssh -n mars 'systemctl cat btrfs-native-push.timer') == "$timer_before" ]] || fail '03:30 timer unit unexpectedly changed'
[[ $(ssh -n mars 'systemctl is-active btrfs-native-push.timer') == active ]] || fail 'Timer became inactive'
[[ $(ssh -n mars 'systemctl is-enabled btrfs-native-push.timer') == enabled ]] || fail 'Timer became disabled'
[[ $(ssh -n mars 'sudo -n sha256sum /media/usb/@snapshots/.simple-agreed-parent.json' | awk '{print $1}') == "$old_source" ]] || fail 'Sender agreed-parent record changed'
[[ $(ssh -n backup 'sudo -n sha256sum /@data/mars-received/.replication-state/.simple-agreed-parent.json' | awk '{print $1}') == "$old_receiver" ]] || fail 'Receiver agreed-parent record changed'
[[ $(ssh -n mars 'sudo -n stat -c "%U:%G %a %n" /media/usb/@snapshots/.simple-agreed-parent.json /run/lock/btrfs-snapshot-manager.lock') == "$old_source_perms" ]] || fail 'Sender protected permissions changed'
[[ $(ssh -n backup 'sudo -n stat -c "%U:%G %a %n" /@data/mars-received/.replication-state/.simple-agreed-parent.json /@data/mars-received/.replication-state/writer.lock') == "$old_receiver_perms" ]] || fail 'Receiver protected permissions changed'
[[ $(ssh -n mars 'systemctl is-active btrfs-native-push-0041-candidate.service || true') != active ]] || fail 'Candidate service active'
echo "PASS: canonical service User=$user_after; loaded ExecStart=$exec_after"
echo 'PASS: 03:30 timer and both protected agreed-parent records unchanged'
if [[ "$mode" == --rollback ]]; then
 echo 'PASS: 0041 Step 11 rollback of canonical sender service completed; dedicated credentials retained'
else
 echo 'PASS: 0041 Step 11 cutover of canonical sender service completed; next scheduled-cycle evidence outstanding'
fi
