# 0048-FEAT — Step 1 preliminary read-only baseline (12 November 2026)

**State:** Step 1 **OPEN**, initial evidence assembled. No deployed files, permissions, ACLs, snapshots, inventory, sudoers or Git source were modified by this review. This report is not formal Step 1 acceptance.

## Evidence and provenance

- `evidence/Step 1/raw-logs/windows-diaries-revisions-and-closures-20261112-200417.txt` — authoritative Windows parent `main` at `00688a4a1d816baa240db7fecafab47e5b97bfba`, no status output, submodule pins, 0046/0047 complete directories and 0048 plan present.
- `evidence/Step 1/raw-logs/mango-controller-and-source-modes-20261112-200502.txt` — controller `main` at `f6ba7fec7752f4bbfa1535958500bde9dea3ea84` with pinned inventory `ebcce026723db37b9b53b76ba21903a351d48466` and Playbooks `df68a0e3bc57bae29a76f46a58c30835126d7f20`, no status output; source modes, source-mode contract, and Ansible installation task definitions.
- `evidence/Step 1/raw-logs/mars-installed-permissions-and-hashes-20261112-200655.txt` — successful read-only installed-mode/hash inspection, initiated from `mango` via SSH; it ended with `PASS`.
- `evidence/Step 1/raw-logs/mars-inspection-ssh-failure-20261112-200554.txt` — prior failed attempt from `mars` to SSH back into itself. This did not inspect permissions and was superseded by the successful `mango`-originated check. Preserved to avoid losing the failure history.

The latest source bundles supplied for this review were `diaries-sources-20261112-194755.zip` and `playbook-sources-20261112-193409.zip`. They may predate subsequent working-copy changes; the terminal evidence is authoritative for the 20:04–20:06 inspections.

## Prerequisites

0046-FEAT and 0047-FEAT appear under `change-control/complete/` in the Windows repository. Their closure reports, reviewed from the source bundle, record formal acceptance. Their existing acceptance/technical evidence is reused, not repeated. The separate 0046 post-closure documentation reconciliation has not been independently verified as published by this package.

## Observed 14-entry comparison

| Class | Historical 0047 contract | `mango` source observation | `mars` installed observation | Result |
|---|---|---|---|---|
| Five synchronized directory sources | `0750` | **`0775`** (all five) | **`0750`** for the five corresponding installed destinations | MISMATCH between current source and installed state |
| Nine include/exclude filter files | `0664`, with SHA-256 per path | `0664` | `0664`; all nine hashes match the published contract | Historical content and modes retained |

The source contract is `playbooks/roles/backup-collection/source-modes.json`, frozen from 0047. The report does **not** assert that its historical permissions are required for correct operation. The current `mango` checkout's directory modes fail the 0047 source-mode preflight and must not be treated as safe to deploy unchanged.

## Source-derived consumer and deployment analysis

- User backup includes/excludes: the user backup `home/backup.sh.j2` invokes `rsync` with `--exclude-from=excludes-1`, `--include-from=includes` and `--exclude-from=excludes-2`. The regular user running that job needs **read** access to these three files and **traverse** access to their parent. No writer requiring `0664` has yet been identified.
- Machine backup includes/excludes: the root `home/backup.sh.j2` similarly reads its three filters. The root `remote/backup.sh.j2` has three matching filter inputs but is conditional/legacy: the machine wrapper invokes remote push only when `legacy_remote_rsync_push_enabled` is true; active source defaults alone cannot prove current deployed toggle. No established requirement for group-write has been identified.
- User installation: `install_user_scripts.yaml` creates selected target directories with explicit mode `0750`, then `ansible.posix.synchronize` uses `archive: true` and `--omit-dir-times`. Archive-mode rsync preserves source directory permissions, so later synchronization can undo the earlier directory mode and repeated runs may oscillate.
- Machine installation: `install_machine_scripts.yaml` creates directories without an explicit `mode`, then does archive-mode synchronization. It excludes `diaries-pull.py` from the generic root synchronization. Both install task files template backup launchers separately at `0744`.
- Installed root backup tree: the inspected paths under `/root/scripts/backup` are owned by `richard:richard`; `/root/scripts/backup/cron` was observed at `0775`, whereas the three audited root subdirectories and root backup root were `0750`. The security consequences require checking `/root` and `/root/scripts` traversal and ACLs rather than assuming an access exposure.
- The source checkout includes `roles/backup-collection/files/backup-machine/diaries-pull.py` with `0775` in the observed working tree. It is explicitly excluded from generic root synchronization and is installed through a different opt-in task; do not conflate it with the nine mode-contract filters or templated launchers.

**No 0048 privilege-management change:** retain `richard`'s `sudo` group membership and the existing sudoers rules, as instructed. Successful `sudo -n` checks on `mars` were reported separately; the failed `sudo -v` attempt does not require remediation under this feature.

## Remaining Step 1 work

1. Capture and evaluate exact ACLs, parent-directory traversal, ownership and relevant user/group identity for all 14 entries, plus the deployed `/root` and `/home/richard` parent chains. Run `tools/collect-step1-acls.sh` as a read-only non-interactive Bash script **on mango**, streaming it from Windows if practical. It prints metadata only and does not read filter contents or Vault values.
2. Verify effective post-0046 Ansible inventory/config paths and current parent/submodule revisions at collection time (the collector performs this). Check for source and installed symlinks.
3. Complete the per-path permission-consumer matrix and security justification. Record unresolved access requirements rather than assuming `0644`/`0755` is safe.
4. Do not run the backup-collection playbook yet. Step 2 must first verify fresh-checkout modes and repeated create-directory + archive-mode sync stability in a disposable target.

**Decision:** keep Step 1 **OPEN**; no source-mode restoration, synchronization, permission change, or deployment is authorised by this report.
