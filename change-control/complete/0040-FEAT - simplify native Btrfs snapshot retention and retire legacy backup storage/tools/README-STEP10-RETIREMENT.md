# 0040 Step 10 — One-off backup legacy retirement

`retire-backup-legacy.py` is **temporary change-control code**, not an Ansible role or a permanent installed receiver command. It never invokes native receiver pruning.

## Preconditions

- Only run on `backup` as root, after the exact approved 113-target manifest has been copied from `/home/richard/0040-step10-evidence/backup-retirement-approved-manifest.json` on `mango`.
- Original manifest SHA-256 must be `1d25d3095b36fec8ce95cbab062ece9e2d5da2c72431c47eef78af0bbdfc1e64`.
- `backup` native pruning stays disabled. No receiver replication operation may overlap the batch; manager and writer locks must be available. Prefer a maintenance interval outside the normal 03:30 UTC push.
- This tool does **not** remove the two legacy Snapper container subvolumes or snapshots under `/@data/mars-received`.
- The 113 entries exclude the two original pilot deletions already completed. Missing approved targets are accepted only when their parent directory has also been fully removed. It stops on any mismatch.

## Controlled rollout (one execution stage at a time)

From the **mango SSH terminal**, after applying this source package to the Windows Diaries repository, transfer the script to mango via your normal Beyond Compare workflow or a controlled copy. Do not run the production execution mode yet.

Then on **mango** (set `SCRIPT` to the actual location of the newly applied Diaries source or evidence copy):

```bash
SCRIPT=/home/richard/0040-step10-evidence/retire-backup-legacy.py
MANIFEST=/home/richard/0040-step10-evidence/backup-retirement-approved-manifest.json
python3 -m py_compile "$SCRIPT"
sha256sum "$MANIFEST"
ssh backup 'sudo install -d -m 0700 /root/0040-retirement'
ssh backup 'sudo install -m 0400 /dev/stdin /root/0040-retirement/approved-manifest.json' < "$MANIFEST"
ssh backup 'sudo install -m 0500 /dev/stdin /root/0040-retirement/retire-backup-legacy.py' < "$SCRIPT"
ssh backup 'sudo python3 /root/0040-retirement/retire-backup-legacy.py --manifest /root/0040-retirement/approved-manifest.json' \
    | tee /home/richard/0040-step10-evidence/backup-retirement-readonly-plan.log
```

Expected `PLAN approved=113 remaining=113 completed=0 mode=READ_ONLY ...` followed by `NO DELETION AUTHORISED`. The read-only rehearsal must pass before any execute invocation.

Once that output is reviewed and separately approved, **mango SSH terminal**:

```bash
ssh backup 'sudo python3 /root/0040-retirement/retire-backup-legacy.py --manifest /root/0040-retirement/approved-manifest.json --execute --max-delete 5' \
    | tee /home/richard/0040-step10-evidence/backup-retirement-first-five.log
```

**Important:** In production, add `set -o pipefail` only inside a subshell or shell script, not to the interactive shell; verify SSH and pipeline exit statuses. Never interpret a partial log as success. Check receiver recovery, native receiver inventory, original timestamped receipts and counts after each batch. Run the next bounded batch only after review. Tool is restartable after a fully completed deletion. If interrupted between Btrfs deletion and metadata cleanup, it *fails closed* and requires manual reconciliation.

### Known limitation

The tool checks recovery with `btrfs-snapshot-manager receiver-recovery-plan` before and after the locked operation, **not while it already holds those locks**; doing so would deadlock or fail due to the existing nonblocking lock protocol. All individual deletions hold both locks, acquired manager first then receiver writer. It stops on unexpected directory contents and does not use recursive deletion. The manifest is a one-time immutable reference, not authority to delete a modified identity.
