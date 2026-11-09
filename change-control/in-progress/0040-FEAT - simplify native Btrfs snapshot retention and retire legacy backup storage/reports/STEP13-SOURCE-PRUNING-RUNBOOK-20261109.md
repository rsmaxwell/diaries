# 0040-FEAT — Step 13 source snapshot-pruning operating runbook

**Updated:** 9 November 2026; **evidence:** `reports/STEP13-BOUNDED-SOURCE-PRUNING-OPERATIONAL-ACCEPTANCE-20261109.md`. This records the accepted operating configuration; it is not authorisation to run destructive maintenance manually.

## Operating schedules and role boundaries

| Host | Job | UTC schedule | Owner / protection |
|---|---|---|---|
| `mars` | Hourly source snapshot creation | `:00` every hour | Source snapshots are read-only `@data` sets. |
| `mars` | Bounded source snapshot pruning | `:45` every hour | `/usr/local/sbin/btrfs-snapshot-manager` with `prune --max-delete 10`; shared manager lock, retention buckets, agreed-parent and checkpoint holds. |
| `mars` | Native incremental sender | 03:30 daily | `btrfs-native-push.timer`, simplified sender status/parent verification. |
| `backup` | Receiver-only retention | 04:15 daily | `btrfs-receiver-simple-prune.timer`; independent received-parent/hold safeguards, 10 max per run. |

Retention remains 48 hourly, 14 daily, 12 weekly, 24 monthly, 5 yearly, minimum age 30 minutes. `mars` source `@data` is `/media/usb/@data`, with source snapshots under `/media/usb/@snapshots/@data/`. `backup` retains received snapshots under `/@data/mars-received/@data/` and immutable historical receipts/state under `/@data/mars-received/.replication-state/`.

**Source of configuration:** Ansible inventory on `mango`, `/etc/ansible/host_vars/mars/local-backup.yaml`, currently contains:

```yaml
btrfs_snapshot_activation_enabled: true
btrfs_snapshot_prune_activation_enabled: true
btrfs_snapshot_prune_on_calendar: "*-*-* *:45:00"
```

Playbooks source `roles/snapshots/defaults/main.yaml` (accepted commit `6ccbf73`) provides `btrfs_snapshot_prune_max_delete: 10`. `ansible-inventory --host mars` does *not* expose role defaults; verify the generated service command and source defaults rather than requiring that key in inventory JSON.

## Read-only checks

**SSH terminal to `mango` as `richard`:**

```bash
ssh mars 'systemctl list-timers --all --no-pager btrfs-snapshot-create.timer btrfs-snapshot-prune.timer btrfs-native-push.timer'
ssh mars 'systemctl cat btrfs-snapshot-prune.service btrfs-snapshot-prune.timer'
ssh mars 'systemctl show btrfs-snapshot-prune.service -p ActiveState -p Result -p ExecMainStatus -p ExecMainStartTimestamp -p ExecMainExitTimestamp'
ssh mars 'sudo -n journalctl -u btrfs-snapshot-prune.service -n 50 --utc --no-pager'
ssh mars 'sudo -n /usr/local/sbin/btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json status'
ssh mars 'sudo -n /usr/local/sbin/btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json prune --dry-run --max-delete 10'
ssh mars 'sudo -n /usr/local/bin/btrfs-simplified-replication sender status'
ssh backup 'sudo -n /usr/local/bin/btrfs-simplified-replication receiver status'
```

During an active prune, `systemctl show` may have `ActiveState=activating` and `ExecMainExitTimestamp` unset; the `status` command may show temporary counts of complete vs managed snapshots. **Accept the execution only after** `Result=success`, exit status 0 and a journal `Deleted N complete timestamp sets` where `0 <= N <= 10`, followed by a consistent snapshot inventory and parent verification.

A `sender status` response `DEFERRED: local snapshot-manager lock busy` is not JSON or a parent mismatch; do not pipe it directly into an unconditional JSON parser. A failure `ERROR: another operation holds /run/lock/btrfs-snapshot-manager.lock` is an intentionally fail-closed lock collision. Correlate creation/prune/replication start and exit times before moving schedules or changing retry behaviour.

## Pause and resume

**Immediate schedule pause, SSH terminal to `mango` as `richard`:**

```bash
ssh mars 'sudo -n systemctl disable --now btrfs-snapshot-prune.timer'
```

This prevents future timer activations but does not necessarily terminate an already executing pruning service. **Persistent pause:** edit `/etc/ansible/host_vars/mars/local-backup.yaml` on `mango`, set `btrfs_snapshot_prune_activation_enabled: false`, then run:

```bash
cd /home/richard/playbooks
ansible-playbook local-backup.yaml --limit mars --tags snapshots --vault-password-file ~/.vault_pass.txt
```

After verifying the current parent/holds, cap and Ansible `--check --diff`, resume by restoring `btrfs_snapshot_prune_activation_enabled: true` in the same inventory file and reapplying the tagged snapshots role. `Persistent=true` may cause a catch-up prune immediately on activation; do not assume the next run will wait for `:45`. **Do not remove lock files, unpin parents, release holds or invoke the uncapped source `prune`** as a workaround.

## Retention / qgroup warnings

The first normal `:45` run completed 9 November 08:45:39–08:51:53 with 10 deletions and 146/146 complete/managed sets; zero incomplete. The same verification reported **606 stale qgroups**, `qgroups_under_deletion=0`, and `qgroups_status=warning`. Tracking, prevention and any approved maintenance belong to **0039-DEF**. The warning is not proof of snapshot corruption or restoration failure, nor evidence of a completed qgroup fix.

## Evidence and rollback ownership

Raw terminal logs and acceptance are preserved under the 0040 feature `evidence/Step 13/` and `reports/` in the **Windows Diaries Git repository**, with execution copy on `mango`. Keep historical failure logs. Reusable Ansible roles and tests belong to the **Playbooks** Git repository on `mango`; actual `/etc/ansible` host vars are managed inventory, not in the Diaries source ZIP. Step 12 retirement rollback archives are retained separately under `evidence/Step 12/rollback/`; do not casually redeploy obsolete legacy binaries or make receiver/parent changes under a source-pruning rollback.
