# 0039-DEF Stage C cleanup helper (2026-10-21)

This is an **operator-run source helper**, not a deployed service. Only run on `backup` after reviewing the diff and installed source. It has no Ansible deployment side effects.

## Assumptions and limits

- `backup` Btrfs root UUID `b915f967-7cb4-4c14-b11b-f52209637a22`, 133 live subvolumes, 134 active qgroups including ID 5.
- Source/received protection IDs/UUIDs are pinned to the October 21 evidence. A future legitimate retention change may cause this helper to refuse to proceed.
- Only unmatched level-0 zero-accounting, zero-parent/child qgroups with `none/none` or `1.00TiB/none` limits are considered. The helper does **not** claim zero-accounting alone proves safety.
- Uses the same advisory `fcntl.flock` as `/usr/local/bin/btrfs-native-push-receiver`. It will not prevent an unrelated uncooperative root process from modifying Btrfs. Checks detect unexpected changes at 25-ID boundaries and after the batch.
- A `--batch-size` of 1 through 1000 is supported. One invocation makes at most one batch. No automatic recurring deletion.
- Journal file is created on `backup`, flushed and synced for each event. Preserve it under defect `evidence/Step 03/reconciliation/backup` via `ssh backup 'sudo cat /home/richard/0039-qgroup-cleanup/<journal>.jsonl'` **after** completion. This keeps runtime writes independent of Windows SSH/network connectivity.
- An unfinished/failed JSONL journal in the same runtime directory prevents a subsequent apply. Inspect and reconcile manually; do not rename or remove evidence to bypass a failure.
- No quota rescans, snapshot deletion or configuration changes are performed. Qgroup destruction is not reliably reversible.
- **Dry-run first.** Verify logs and permissions, and separately authorise the first 1,000-operation batch. No Stage C bulk commands are included in this ZIP.

## Development regression (Cygwin / Windows checkout)

```sh
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
DIR='change-control/in-progress/0039-DEF - reconcile orphaned Btrfs qgroups on backup/tools'
python3 -m py_compile "$DIR/cleanup-qgroups.py"
python3 "$DIR/test-cleanup-qgroups.py"
```

## Production preflight (backup SSH; **read-only**)

Copy the reviewed script into a controlled, known location via the existing operational deployment process before invoking; do not paste or execute directly from this ZIP. Then use:

```sh
sudo python3 /path/to/reviewed/cleanup-qgroups.py --dry-run --batch-size 1000
```

After explicit approval of a production batch and confirming preservation of prior evidence, `--apply` uses the same script with `--batch-size 1000`. Runtime journal default is `/home/richard/0039-qgroup-cleanup/`.
