#!/usr/bin/env bash
# 0041-FEAT Step 7: additive service-identity provisioning on mango.
# Run ONLY using the feature's Windows/Cygwin launcher. Do not run this
# interactively: its fail-fast mode is scoped to this non-interactive process.
# This script does NOT change the existing replication service/timer, execute
# a Btrfs send/receive, or change richard's SSH or sudo permissions.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
on_exit() {
  result=$?
  if (( result != 0 )); then
    printf 'FAIL: 0041 Step 7 aborted (exit %s); additive changes may have been applied.\n' "$result" >&2
    printf '       Existing 03:30 service/timer was NOT intentionally switched.\n' >&2
  fi
}
trap on_exit EXIT

printf '0041 STEP 7 ADDITIVE PROVISIONING: %s on %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(hostname)"
[[ $(hostname -s) == mango ]] || fail 'Must execute on mango'

cd /home/richard/ansible-controller
[[ $(git rev-parse HEAD) == 83cba342d9ffe7da51a97bda9231f32d02beb2e3 ]] || fail 'Controller revision changed; review required'
[[ $(git -C inventory rev-parse HEAD) == ebcce026723db37b9b53b76ba21903a351d48466 ]] || fail 'Inventory revision changed; review required'
[[ $(git -C playbooks rev-parse HEAD) == c5109340a2fe13296a2343c682e1079d1a212c8d ]] || fail 'Playbooks revision changed; review required'
git submodule status

cd playbooks
[[ -z $(git diff --cached --name-only) ]] || fail 'Unexpected staged Playbooks changes'
git diff --check
if git status --porcelain --untracked-files=all | sed -E 's/^...//' | grep -Ev '^roles/btrfs-replication/'; then
  fail 'Changes exist outside the reviewed Btrfs replication role'
fi

printf '\n=== Verify the exact previously tested candidate source files ===\n'
sha256sum -c <<'EXPECTED_CANDIDATE'
7c149eccdb08c296fa9b4fc8fd645af66cca602ce61087a2bf4d341ba9a0a7d2  roles/btrfs-replication/README-0041-DEDICATED-IDENTITIES.md
e3d9da73987e33cc320856604daf2267610bdb6d160bee411220ba32cc0207a9  roles/btrfs-replication/defaults/main.yaml
689f7ba5bc067859f745704c7b2e298814a7fe71918d058747542931ef6c68bc  roles/btrfs-replication/files/btrfs-replication-receiver-gate-0041.py
334cc199ef36465dae2d8c817b676fc47e534807f7a0358a231190dd4d22e76a  roles/btrfs-replication/files/btrfs-replication-sender-cycle-0041.sh
8f1f602a8f695e01df984ce58d2de9d6d841799d0b9ab843f1ed91b59c35706f  roles/btrfs-replication/files/btrfs-replication-ssh-dispatch-0041.py
01bc877c52ef1051f2f00d4058d740c53af34e1c4cb2545a3e066a6530787a20  roles/btrfs-replication/files/btrfs-simplified-replication.py
953a19d920a2e24fd0fef955ceb299693ec19ed963f17c65cec3da1acccba031  roles/btrfs-replication/tasks/native.yaml
2cd59d2554a42584815deccf16d63265dc55b70c56a01b8361b442049fab2217  roles/btrfs-replication/tasks/service-identities-0041.yaml
1758ed6ce0f0aac709f8df4b7bd101122a99e9b99340ab46d95d6482f94c688a  roles/btrfs-replication/templates/btrfs-0041-service-sudoers.j2
760c27335a1a3c297afd7a8a009cb5699f4cfbea21ddeb05bdcdc74522b87e10  roles/btrfs-replication/templates/btrfs-native-push-0041.service.j2
4e09357dc0f2179a14b211548646998bb12cc8fe303eeae70564e987ea24863a  roles/btrfs-replication/tests/verify-0041-restricted-identity.py
EXPECTED_CANDIDATE

printf '\n=== Verify receiver host key before installing SSH credentials ===\n'
# Crucial: all nested SSH calls use -n. Otherwise they may consume the
# enclosing `ssh mango 'bash -s' < script` stream and cause a false PASS.
expected=$(ssh -n -o BatchMode=yes backup 'sudo -n ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub' | awk '{print $2}')
observed=$(ssh -n -o BatchMode=yes mars 'ssh-keyscan -T 10 -p 39263 -t ed25519 10.254.22.1 2>/dev/null' | ssh-keygen -lf - | awk '{print $2}')
printf 'Receiver ED25519 fingerprint: %s\n' "$expected"
printf 'Port 39263 ED25519 key:    %s\n' "$observed"
[[ $expected == SHA256:* && $expected == "$observed" ]] || fail 'Receiver SSH host key mismatch or missing'
printf 'PASS: receiver SSH host key matched\n'

printf '\n=== Capture active service, timer and protected-state metadata ===\n'
legacy_service_before=$(ssh -n -o BatchMode=yes mars 'systemctl cat btrfs-native-push.service')
legacy_timer_before=$(ssh -n -o BatchMode=yes mars 'systemctl cat btrfs-native-push.timer')
legacy_timer_enabled_before=$(ssh -n -o BatchMode=yes mars 'systemctl is-enabled btrfs-native-push.timer')
legacy_timer_active_before=$(ssh -n -o BatchMode=yes mars 'systemctl is-active btrfs-native-push.timer')
[[ $legacy_service_before == *'User=root'* ]] || fail 'Existing replication service is not root-owned as reviewed'
[[ $legacy_service_before == *'ExecStart=/usr/local/bin/btrfs-simplified-replication sender cycle'* ]] || fail 'Existing sender command differs from reviewed source'
[[ $legacy_timer_enabled_before == enabled && $legacy_timer_active_before == active ]] || fail 'Existing 03:30 timer is not active and enabled'
source_state_before=$(ssh -n -o BatchMode=yes mars 'sudo -n stat -c "%U:%G %a %n" /media/usb/@snapshots/.simple-agreed-parent.json /media/usb/@snapshots/.replication-protection.json /run/lock/btrfs-snapshot-manager.lock')
receiver_state_before=$(ssh -n -o BatchMode=yes backup 'sudo -n stat -c "%U:%G %a %n" /@data/mars-received/.replication-state /@data/mars-received/.replication-state/.simple-agreed-parent.json /@data/mars-received/.replication-state/writer.lock')
printf '%s\n' "$source_state_before" "$receiver_state_before"

printf '\n=== Apply additive identity provisioning only ===\n'
cd /home/richard/ansible-controller
source ./enter.sh
cd /home/richard/ansible-controller/playbooks
ansible-playbook btrfs-replication.yaml \
  --limit 'mars,backup' --tags btrfs-0041-provision \
  -e btrfs_0041_additive_enabled=true \
  --vault-password-file "$HOME/.vault_pass.txt" </dev/null

printf '\n=== Verify accounts and root-managed boundaries ===\n'
ssh -n -o BatchMode=yes mars 'getent passwd btrfs-send && id btrfs-send && sudo -n visudo -cf /etc/sudoers.d/btrfs-0041-service && sudo -n stat -c "%U:%G %a %n" /var/lib/btrfs-send/.ssh/id_ed25519 /usr/local/libexec/btrfs-replication-sender-cycle-0041 /etc/btrfs-replication-0041/known_hosts'
ssh -n -o BatchMode=yes backup 'getent passwd btrfs-receive && id btrfs-receive && sudo -n visudo -cf /etc/sudoers.d/btrfs-0041-service && sudo -n /usr/sbin/sshd -t && sudo -n stat -c "%U:%G %a %n" /var/lib/btrfs-receive/.ssh/authorized_keys /usr/local/libexec/btrfs-replication-receiver-gate-0041 /usr/local/libexec/btrfs-replication-ssh-dispatch-0041'

printf '\n=== Read-only dedicated transport test (NO Btrfs transfer) ===\n'
status_json=$(ssh -n -o BatchMode=yes mars 'sudo -n env BTRFS_REPLICATION_IDENTITY_MODE=dedicated /usr/local/bin/btrfs-simplified-replication sender status')
printf '%s\n' "$status_json"
printf '%s\n' "$status_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["receiver_parent_verified"] is True, "Unverified receiver parent"; assert "preflight" in d, "Missing preflight"; print("PASS: dedicated SSH status and receiver identity verified")'

printf '\n=== Assert original production service/timer and protected metadata unchanged ===\n'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl cat btrfs-native-push.service') == "$legacy_service_before" ]] || fail 'Production service definition changed'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl cat btrfs-native-push.timer') == "$legacy_timer_before" ]] || fail 'Production timer definition changed'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-enabled btrfs-native-push.timer') == "$legacy_timer_enabled_before" ]] || fail 'Production timer enabled status changed'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-active btrfs-native-push.timer') == "$legacy_timer_active_before" ]] || fail 'Production timer active status changed'
[[ $(ssh -n -o BatchMode=yes mars 'sudo -n stat -c "%U:%G %a %n" /media/usb/@snapshots/.simple-agreed-parent.json /media/usb/@snapshots/.replication-protection.json /run/lock/btrfs-snapshot-manager.lock') == "$source_state_before" ]] || fail 'Protected sender-state metadata changed'
[[ $(ssh -n -o BatchMode=yes backup 'sudo -n stat -c "%U:%G %a %n" /@data/mars-received/.replication-state /@data/mars-received/.replication-state/.simple-agreed-parent.json /@data/mars-received/.replication-state/writer.lock') == "$receiver_state_before" ]] || fail 'Protected receiver-state metadata changed'
ssh -n -o BatchMode=yes mars 'test -f /etc/systemd/system/btrfs-native-push-0041-candidate.service'
printf 'PASS: production service and 03:30 timer unchanged; candidate unit staged only\n'

printf '\nPASS: 0041 additive provisioning and dedicated-status check verified\n'
