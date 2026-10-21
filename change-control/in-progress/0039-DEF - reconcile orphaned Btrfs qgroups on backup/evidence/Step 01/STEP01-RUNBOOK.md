# Step 01 — Read-only reconciliation runbook

**Terminal:** existing SSH terminal on `backup` (`richard@backup:~$`). **Classification:** all commands READ-ONLY; no deletion, rescan, quota change or snapshot change.

Run this consolidated bounded report (output suitable to paste back for review):

```bash
sudo python3 - <<'PY'
import re
import subprocess

def invoke(*args):
    result = subprocess.run(args, text=True, capture_output=True, check=False, timeout=120)
    if result.returncode:
        raise SystemExit(f'{args!r}: rc={result.returncode}, stderr={result.stderr[:500]!r}')
    return result.stdout

subvol_text = invoke('btrfs', 'subvolume', 'list', '/')
qgroup_text = invoke('btrfs', 'qgroup', 'show', '--raw', '/@snapshots')
subvol = {int(m.group(1)) for line in subvol_text.splitlines()
          if (m := re.match(r'^ID\s+(\d+)\s', line))}
qgroups = {}
other = 0
for line in qgroup_text.splitlines():
    fields = line.split()
    if len(fields) < 3:
        continue
    m = re.fullmatch(r'(\d+)/(\d+)', fields[0])
    if not m:
        continue
    level, number = map(int, m.groups())
    if level == 0:
        try:
            qgroups[number] = (int(fields[1]), int(fields[2]))
        except ValueError:
            raise SystemExit('Unexpected qgroup numeric format: ' + repr(line[:120]))
    else:
        other += 1

orphan = set(qgroups) - subvol
missing = subvol - set(qgroups)
zero_orphan = [i for i in orphan if qgroups[i] == (0, 0)]
nonzero_orphan = [i for i in orphan if qgroups[i] != (0, 0)]
print('Existing listed subvolumes:', len(subvol))
print('Level-0 qgroups:', len(qgroups), 'Higher-level qgroups:', other)
print('Orphan candidates:', len(orphan), 'zero:', len(zero_orphan), 'nonzero:', len(nonzero_orphan))
print('Listed subvolumes missing qgroups:', len(missing))
print('First 20 orphan candidate IDs:', sorted(orphan)[:20])
print('First 20 nonzero orphan candidate IDs:', sorted(nonzero_orphan)[:20])
print('First 20 missing IDs:', sorted(missing)[:20])
print('Top-level subvolume ID 5: not normally in subvolume list; check separately if present')
PYTHON

echo '=== Version and quota configuration (bounded) ==='
btrfs version
uname -r
sudo btrfs qgroup show --help 2>&1 | head -35

echo '=== Deleted subvolume status (bounded) ==='
sudo btrfs subvolume list -d / | head -30

echo '=== Diagnostic ==='
sudo btrfs-snapshot-manager status | grep -E '^(qgroups_status|snapshot_root|filesystem)='
```

**Interpretation cautions:** (1) This first set comparison is not a deletion list: qgroups may represent pending deletion or relationships beyond the listed subvolumes. (2) ID 5, the top-level subvolume, is treated separately. (3) `--raw` should display numeric bytes on installed Btrfs versions; if not, stop and share output instead of attempting a correction. (4) Use `head` only for short bounded supporting command output, never as evidence that the full pending-deletion list has been checked.

**Gate 1 decision:** Remains OPEN until the output is reviewed. No filesystem changes authorised.
