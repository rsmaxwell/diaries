# Step 1 — Existing evidence review (20 October 2026)

**Evidence source:** previously uploaded `backup` and `mango` terminal logs, not newly executed checks.

- `backup`: `sudo btrfs-snapshot-manager status` failed due to `/@data/diaries-mars-replica/pluto`.
- `backup`: manager JSON confirmed obsolete writer lock and verified-dataset/marker paths, `required: true`.
- `backup`: received Btrfs subvolumes under `/@data/mars-received/@data`; 14 timestamped entries visible in filtered list, most recent `20261020-030026Z`; replication state directory present.
- `mango`: role chain `remote-backup.yaml` → `remote-backup` → `snapshots` confirmed.
- `mango`: inventory grep saw `/` and `/@data` with no `btrfs_snapshot_*` variables; current role defaults inactive/verification off.
- `mango`: Ansible check diff 22 ok / 5 changed / 0 failed; manager, history, manifest verifier, JSON and new legacy-prune unit file install tasks. Timers not enabled by plan.

## Additional operator baseline and final closure decision

On 20 October 2026 the operator subsequently recorded:

- Installed SHA-256: JSON `eec8a849cacbc9ee5d27334ac8511065fc0cafc31cabb9ba45a184c8e577c7e6`; manager `b1ff38c4fdfacabc6f394d3f35de95b90c2061bf84b1721a7e0c0da1e88c6a99`; history `1b40c70be484b0268fb2ba1c9558b98ec150651e37e6535aa030158c437be206`; verifier `6878a61aeaf4abfe561d9be2c883bb12fb2d67b72b5b7ec0b9420c018fad6cc3`.
- `backup`: native `btrfs-snapshot-create.timer` and `btrfs-snapshot-prune.timer` both disabled/inactive; `btrfs-legacy-prune.timer` not installed and inactive; 14 received subvolumes, newest `20261020-030026Z`; receipt directory `drwx------ richard:richard`. A cryptographic receipt-to-snapshot match has **not** been run; reserve for Step 6.
- `mango`: Playbooks HEAD `6a80d4f4160574b243a3d1e73e2f8b0fac767846` with uncommitted edits in playbook targets and `scripts/{diaries,local-backup,remote-backup}.sh`. `git diff --check` found carriage returns/trailing whitespace and superfluous EOF blank lines. These are known deviations, not acceptance of clean source.
- Original `/etc/ansible/hosts` had two `local_backup` definitions; operator supplied corrected file containing one `local_backup` (mars) and one `remote_backup` (backup). Final live checks: `local-backup.yaml --list-hosts` lists **mars only**; `remote-backup.yaml --list-hosts` lists **backup only**; no duplicate-key warnings; remote playbook `--syntax-check` PASS.
- Earlier Ansible dry run was `ok=22 changed=5 failed=0`; it has **not** been applied.

**Step 1 formal decision: CLOSED, 20 October 2026.** Accepted evidence is sufficient to bound Step 2 without another full restore or transfer. Open matters: whitespace, check-only shell wrappers, current uncommitted source changes, deeper replication identity validation, final dry-run scope, backup rollback and real deployment. These must not silently be marked complete.

