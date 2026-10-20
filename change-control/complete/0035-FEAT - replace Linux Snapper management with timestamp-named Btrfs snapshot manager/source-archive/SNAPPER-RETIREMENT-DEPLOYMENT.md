# 0035-FEAT — isolated Snapper timer retirement

Use `snapper-retirement.yaml` to **only** disable and stop installed
`snapper-timeline.timer`, `snapper-boot.timer` and `snapper-cleanup.timer`
on `mars` and `backup`. This playbook does not load the `local-backup`,
`remote-backup` or `snapshots` roles and does not alter Btrfs snapshot manager
code/configuration, native replication, Diaries pull, or any stored snapshots.

From mango (`~/playbooks`):

```sh
python3 roles/snapshots/tests/verify-snapper-retirement.py
python3 roles/snapshots/tests/verify-snapper-retirement-entrypoint.py
ansible-playbook snapper-retirement.yaml --check --diff --vault-password-file ~/.vault_pass.txt
ansible-playbook snapper-retirement.yaml --vault-password-file ~/.vault_pass.txt
ansible-playbook snapper-retirement.yaml --vault-password-file ~/.vault_pass.txt  # idempotency
```

`systemctl list-unit-files` discovery runs read-only in check mode. Missing timer
units are skipped. The play targets only `mars:backup`; it is safe to rerun.
Ansible `--check` may report predicted changes when a timer is enabled.

Verify on each host:

```sh
for t in snapper-timeline.timer snapper-boot.timer snapper-cleanup.timer; do
  systemctl is-enabled "$t" || true
  systemctl is-active "$t" || true
done
systemctl list-timers --all | grep -Ei 'snapper|btrfs|diaries' || true
```

Do not delete historical numbered snapshots until separate recovery and
retention acceptance. This is an additive source-level change to the 0035
retirement overlay; apply that overlay before this ZIP.
