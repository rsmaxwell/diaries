# Step 12 — Permanent local-backup deployment correction (staged)

## Decision
Use the permanent `local-backup.yaml` and `roles/snapshots/` implementation; **no temporary stage playbook**. Source ZIP 20261020-155946 is the patch baseline.

## Previous acceptance evidence
`local-backup.yaml --tags snapshots --check --diff` reaches the role, but on first installation the simulated timer does not exist for a later `systemd` task, so check mode reports a false failure. The whole snapshot role also proposes updating the independent Diaries manifest verifier, unrelated to the legacy timer.

## Permanent changes
- `roles/local-backup/tasks/main.yaml`: tag the existing `include_role: snapshots` with `legacy-prune-units`.
- `roles/snapshots/tasks/main.yaml`: add the focused tag to role gate, unit templates and timer activation; `stat` the installed timer and skip **only the timer activation task in check mode when the unit is absent**. A normal run always manages it (enabled/started or disabled/stopped).
- Regression `verify-local-backup-legacy-unit-deploy.py` checks the path and safety invariants.

The existing systemd templates and role default settings remain unchanged: native prune hourly at :15, legacy daily 08:20 UTC, maximum one legacy candidate per execution, default disabled. Existing Snapper timer retirement and snapshot safety logic are unchanged.

## Controlled staging from mango
First (no mutations):

```sh
cd /home/richard/playbooks
python3 roles/snapshots/tests/verify-local-backup-legacy-unit-deploy.py
ansible-playbook local-backup.yaml --syntax-check --vault-password-file ~/.vault_pass.txt
ansible-playbook local-backup.yaml --limit mars --tags legacy-prune-units --check --diff --vault-password-file ~/.vault_pass.txt
```

Review that only the intended units are proposed; the new timer cannot be activated from the default `false` setting. Then deploy with **no extra `-e` overrides**:

```sh
ansible-playbook local-backup.yaml --limit mars --tags legacy-prune-units --vault-password-file ~/.vault_pass.txt
```

Repeat that command to verify idempotency. This focused tag deliberately excludes the independent manifest verifier. Full `local-backup.yaml` convergence is a separate, broader check: any source drift in that verifier must be examined and reconciled, not silently suppressed.

On mars:

```sh
sudo systemctl cat btrfs-legacy-prune.service btrfs-legacy-prune.timer
sudo systemctl is-enabled btrfs-legacy-prune.timer
sudo systemctl is-active btrfs-legacy-prune.timer
sudo systemctl cat btrfs-snapshot-prune.timer
sudo systemd-analyze verify /etc/systemd/system/btrfs-legacy-prune.service /etc/systemd/system/btrfs-legacy-prune.timer
sudo btrfs-snapshot-manager legacy-prune --legacy-map root=root --legacy-map @data=@data --max-delete 1
```

Expect timer disabled/inactive until separately authorised. **Do not run the legacy service manually** (it contains `--execute`). For permanent activation, set `btrfs_snapshot_unattended_legacy_prune_enabled: true` in the appropriate `mars` inventory configuration and run the same permanent playbook; re-run to verify idempotency. For rollback, set it to false and rerun. Confirm native timer, holds, receipts, and old Snapper timers before enabling.

## Acceptance
Source regressions passed in staging. Live check mode, live deployment, timer state, first unattended deletion and repeat-run idempotency **not yet accepted**. Step 12 remains OPEN.
