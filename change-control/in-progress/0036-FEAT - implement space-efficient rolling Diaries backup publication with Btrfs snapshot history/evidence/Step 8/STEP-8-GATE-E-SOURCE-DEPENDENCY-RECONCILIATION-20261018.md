# Gate E — source dependency reconciliation (18 October 2026)

**Status: REVIEWED; retirement changes NOT YET DEPLOYED; Gate E remains OPEN.**

## Source evidence

Sources reviewed: `diaries-sources-20261018-083842.zip` and `playbook-sources-20261018-083411.zip`, treated as authoritative snapshots for this analysis. Runtime inventory was collected separately. These source archives do not include live host-variable/vault values, so effective deployment migration cannot be inferred from them.

- `roles/diaries/templates/etc/systemd/system/diaries-complete-backup-publish.service.j2` retains *two* branches: `fixed-capture-preflight` + `fixed-capture` selected by `diaries_0036_fixed_capture_enabled`, or legacy `publish-preflight` + `publish`. The live `pluto` service was separately verified to use the fixed branch. **Removing the legacy branch before validating all host inventories risks changing non-production or rollback behavior.**
- `roles/diaries/defaults/main.yaml`, `roles/diaries/tasks/main.yaml`, `roles/diaries/tasks/0036-host-nas-mount.yaml`, and `roles/diaries/templates/0036-nas-credentials.j2` use `diaries_0036_*` variable names and a deployed credential path `/etc/diaries/0036-nas-credentials`. Any rename requires a compatible inventory/vault migration, fstab/mount check, and no-log secret handling.
- `roles/diaries/files/sync/scripts/fixed-dataset-capture.py` reads `DIARIES_0036_HOST_FILES_ROOT`, `DIARIES_0036_HOST_MOUNT_ROOT`, and `DIARIES_0036_HOST_FILES_IDENTITY`. `production-complete-dataset.py` reads `DIARIES_0036_FIXED_CAPTURE_ENABLED` and `DIARIES_0036_ROLLING_ENABLED`. Renaming only Ansible settings would *not* update these runtime environment variables.
- The fixed receiver guard and `--fixed-destination` path are required for accepted 0036 behavior. Maintain their current invocation until explicit cutover verification.
- Preserve both `.pre-0036-rollback` aliases and four observed generations on each producer/receiver. **Their removal requires separate express approval**; no deletion is included here.
- The preexisting 0034/0035 historical restore and off-site lineage safeguards must remain intact. Do not remove old script commands merely because the active service does not call them.

## Safe staged retirement sequence

1. Commit this reconciliation evidence and run the included **read-only** Playbooks/Diaries source audit against the actual working copies. Record source revisions and differences.
2. On `mango`, determine effective host variables and vault dependencies for `pluto`, `mars`, `backup` without exposing secrets. Capture the current rendered service, deployed `.env` key *names* (never secret values), NAS mount/fstab and receiver wrapper. Check other target hosts before removing the legacy template branch.
3. Implement *compatibility-first* stable-name migration across Ansible defaults, inventory, vault, runtime `.env`, credential path, capture/receiver code, tests and documentation. Preserve compatibility with existing configuration during a staged rollout; reject ambiguous conflicting values. No automatic branch flip.
4. Test source regressions, render Ansible templates on `mango`, run check-mode preflight with secrets redacted, then deploy one host at a time. Verify service command lines, mount, guard and schedules; confirm no unintended timer restart.
5. With deployment evidence accepted, separately seek approval for retiring obsolete publisher execution and (independently) deletion of legacy generations. Preserve checkpoint holds, receipts and native replication parents.
6. Record deployed commit hashes and close Gate E and 0036 only after all approved acceptance criteria pass.

## Execution guidance

From `mango`, after installing `playbooks/verification/0036-gate-e/audit-source-dependencies.sh`:

```bash
bash ~/playbooks/verification/0036-gate-e/audit-source-dependencies.sh \
  ~/playbooks /path/to/diaries > ~/0036-gate-e-source-audit.txt
```

`/path/to/diaries` must identify an accessible Diaries working tree; the Windows working tree is not automatically accessible from `mango`. Alternatively, run the audit where both working trees are present. The script only lists source references; it does not inspect live deployments or alter anything.

**Decision:** No production cleanup/deletion authorised by this source review alone. Historical Snapper retirement remains outside Gate E.
