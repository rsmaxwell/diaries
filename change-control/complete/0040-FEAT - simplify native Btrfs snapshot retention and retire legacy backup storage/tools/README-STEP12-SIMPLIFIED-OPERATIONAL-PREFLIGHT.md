# 0040-FEAT — Step 12 controlled operational preflight (read-only)

**Status:** PREPARED, **not executed**. Run on 5 November 2026 or later; substitute actual run date in evidence filename. Source/inventory may have changed since the 2 November uploaded bundles.

**Scope:** inspect source checkout, installed commands, services/timers, filesystem identities, simplified/legacy state files, receiver pruning configuration, and intended SSH/sudo path. No transfer, bootstrap, pruning, reboot, cleanup, timer change or Ansible deployment is part of this preflight.

**Acceptance:** operator reviews and records results before authorising installation/activation. A failed or missing check is an unresolved prerequisite, not permission to reset state or re-run expensive restores.

## 1. Mango — source/config summary

**Terminal: existing SSH connection to `mango`**

```bash
cd /home/richard/playbooks
printf '%s\n' '--- Playbooks branch/revision ---'
git branch --show-current
git rev-parse HEAD
printf '%s\n' '--- Local changes in affected files ---'
git status --short -- roles/btrfs-replication roles/snapshots
printf '%s\n' '--- Candidate checksum ---'
sha256sum roles/btrfs-replication/files/btrfs-simplified-replication.py
printf '%s\n' '--- Opt-in defaults / service selection ---'
grep -nE '^btrfs_simplified_replication_(install|active)_enabled:|^btrfs_native_push_on_calendar:' roles/btrfs-replication/defaults/main.yaml
sed -n '1,35p' roles/btrfs-replication/templates/btrfs-native-push.service.j2
```

**Do not use `git reset`, `git clean`, or a blanket ZIP overwrite:** the Playbooks tree has significant existing local changes from the earlier design.

## 2. Mars — installed sender, timer and state (read-only)

**Terminal: Windows Cygwin (using SSH to `mars`)**

```bash
ssh mars 'printf "%s\n" "--- host, time, installed commands ---"; hostname; date -u; ls -l /usr/local/bin/btrfs-native-push /usr/local/bin/btrfs-simplified-replication 2>&1; sudo -n sha256sum /usr/local/bin/btrfs-native-push /usr/local/bin/btrfs-simplified-replication 2>&1; printf "%s\n" "--- service/timer ---"; systemctl cat btrfs-native-push.service btrfs-native-push.timer; systemctl is-enabled btrfs-native-push.timer; systemctl is-active btrfs-native-push.timer; printf "%s\n" "--- filesystem and parent files ---"; sudo -n btrfs filesystem show /media/usb; sudo -n ls -l /media/usb/@snapshots/.simple-agreed-parent.json /media/usb/@snapshots/.agreed-parent.json 2>&1; sudo -n cat /media/usb/@snapshots/.simple-agreed-parent.json 2>&1'
```

Only report current values; a missing simplified state file is normal before bootstrap and **must not** be created by inspection.

## 3. Backup — installed receiver, state and pruning (read-only)

**Terminal: Windows Cygwin (using SSH to `backup`)**

```bash
ssh backup 'printf "%s\n" "--- host, time, installed commands ---"; hostname; date -u; ls -l /usr/local/bin/btrfs-simplified-replication /usr/local/bin/btrfs-agreed-parent-receiver /usr/local/bin/btrfs-native-endpoint 2>&1; sudo -n sha256sum /usr/local/bin/btrfs-simplified-replication /usr/local/bin/btrfs-agreed-parent-receiver /usr/local/bin/btrfs-native-endpoint 2>&1; printf "%s\n" "--- filesystem and parent files ---"; sudo -n btrfs filesystem show /; sudo -n ls -l /@data/mars-received/.replication-state/.simple-agreed-parent.json /@data/mars-received/.replication-state/.agreed-parent.json 2>&1; sudo -n cat /@data/mars-received/.replication-state/.simple-agreed-parent.json 2>&1; printf "%s\n" "--- snapshot/prune timers ---"; systemctl list-timers --all --no-pager "*btrfs*" "*snapshot*"'
```

Verify that receiver pruning is disabled using the **actual Ansible inventory** and installed manager configuration; timer listing alone is insufficient. Do not enable it during this step.

## 4. Mango — Ansible install-only preview (non-destructive, after source review)

**Terminal: existing SSH connection to `mango`**

```bash
cd /home/richard/playbooks
ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --check --diff --vault-password-file ~/.vault_pass.txt -e '{"btrfs_native_push_schedule_enabled":true,"btrfs_simplified_replication_install_enabled":true,"btrfs_simplified_replication_active_enabled":false}'
```

Review the entire diff, including role tasks beyond the simplified binary. `--check` can still exercise role checks; do not run a non-check deployment unless the result is explicitly accepted. The explicit `schedule_enabled=true` is intended to retain the existing 03:30 timer, **not** to change its schedule.

## 5. Go/no-go

Record in `reports/`: both installed/source checksums and actual files, timer/ExecStart state, filesystem UUIDs, historical/current parent identity and holds, previous-native rollback readiness, receiver-prune disabled status, SSH/sudo reachability, and complete check/diff. **No automatic GO** follows from successful source or disposable tests alone. Receiver pruning needs separate operational approval.

The accepted source/disposable correctness evidence is recorded in `reports/STEP12-SIMPLIFIED-SOURCE-AND-REAL-BTRFS-ACCEPTANCE-20261105.md`. Do not rerun it unchanged.
