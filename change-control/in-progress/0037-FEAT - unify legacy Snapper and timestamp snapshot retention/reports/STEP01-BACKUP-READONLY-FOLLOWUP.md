# Read-only follow-up for backup receiver validation

From Cygwin, while inside 0037-FEAT, capture stdout/stderr into `evidence/Step 01/backup-receiver-followup.txt`:

```bash
ssh richard@backup 'sudo bash -s' > 'evidence/Step 01/backup-receiver-followup.txt' 2>&1 <<'REMOTE'
set -u
hostname -f
date -u --iso-8601=seconds
findmnt -t btrfs -o TARGET,SOURCE,FSTYPE,OPTIONS
for p in /@data /@data/diaries-mars-replica /@data/diaries-mars-replica/pluto; do
  echo "--- $p ---"
  if test -e "$p"; then stat -c '%n %F %a %U:%G' "$p"; else echo 'MISSING'; fi
done
btrfs subvolume list -o / 2>&1 | grep -E 'diaries-mars-replica|diaries-backup|snapshots' | head -n 100 || true
REMOTE
```

Do not create directories, delete snapshots, or modify the manager configuration. Inspect the output for sensitive path naming before committing; prefer keeping raw output ignored under feature evidence.
