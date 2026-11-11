# 0045-FEAT — Step 2 integrated source refactor candidate (11 November 2026)

**State:** Step 1 formally CLOSED in Diaries commit `731c6a3`; Step 2 CODE PREPARED, not yet deployed or accepted.

**Source freeze:** Playbooks main `7dfa93fef6d975aa82f5f4cfdf54497b106e7645` (from 11:19 source bundle and user Git readback). Definitive installed-state baseline `evidence/Step 1/baseline-20261111-111819Z/`.

## Proposed Playbooks changes

- Split original 24 `snapshots` tasks into 8 statically imported phase files and 36 native `btrfs-replication` tasks into 9 phase files. Static imports use no new conditions or tags. Original per-task conditions, privileges, tags, arguments, notifications, registers and ordering are retained exactly.
- Add `backup-collection.yaml` and `scripts/backup-collection.sh` with the same full `local-backup` role and identical check/apply behaviour; update current operator documentation.
- Keep `btrfs-replication.yaml` as the only native endpoint entry point; preserve `roles/btrfs-replication/tasks/main.yaml` behaviour for the `snapshots.yaml` generic path, so receiver generic snapshots still fail closed. Document the distinction.
- Keep `local-backup` role and its existing machine/user backup installation unchanged. **Never remove `/root/scripts/backup/remote/` on mars** as a side effect of operator-level retirement.
- Candidate retirement paths (not included in add/update ZIP, must be explicitly deleted after caller audit): `local-backup.yaml`, `scripts/local-backup.sh`, `remote-backup.yaml`, `scripts/remote-backup.sh`. On receiver use `btrfs-replication.yaml --limit backup` instead. Historical verification references are preserved unchanged.
- Do not modify inventory or commit live `/etc/ansible` state. 0046 remains deferred.

## Offline verification performed on generated package

- Parsed every new YAML task file using PyYAML.
- Compared flattened ordered tasks to original source by canonical SHA-256, ensuring content/conditions/tags/owner/mode preserved.
- Verified entry-point role dispatch and new launcher source, ZIP paths and ZIP CRC.
- Did **not** run Ansible syntax/check/apply (Ansible is not installed in this preparation environment), nor inspect external caller jobs on `mango`, `pluto` or elsewhere.

## Next acceptance requirements

1. Review the ZIP and deletion candidates with Beyond Compare 4. Before retirement, inspect any external automation / timers / Jenkins / user crontabs calling old names. If callers exist, migrate them without changing the operational task schedule.
2. Verify clean `mango` revision/status and apply change package to `/home/richard/playbooks`. Run `ansible-playbook --syntax-check` for all changed entry points, playbook `--list-tasks` and `--list-tags` as relevant, and the permanent replication tests. Run the feature-specific source-equivalence test against applied Playbooks.
3. Only after source review and test acceptance, apply normal Ansible deployments with explicit authorisation, then compare installed v2 manifests against Step 1 and confirm timer/security/holds remain unchanged; no manual replication or restoration.
4. Do not mark Step 2 CLOSED before the source diff and removed-entrypoint audit are accepted; Step 3 remains OPEN until deployment equivalence accepted.
