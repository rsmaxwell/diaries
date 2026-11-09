# 0040-FEAT — Mars one-time legacy Snapper retirement (NOT APPROVED FOR EXECUTION)

This tool is **mars-only** and targets only the 17 UUID-and-subvolume-ID pinned numeric snapshots in `/media/usb/@data/.snapshots`. It does not retire the native `@snapshots/root` collection or any native `@data` timestamp sets. The 14 legacy GFS/anchor KEEP selections include historical points earlier than the native history; their loss requires a separate, explicit recovery-history acceptance decision.

Evidence anchor (on mango): `/home/richard/0040-step10-evidence/mars-retirement-approved-manifest.json`, SHA256 `643c3dff637be45da4188f9991a2bddb27a8bb894d474aebd2318c5ebfa412b4`. The manifest deliberately remains on `mango`; no production transfer is part of this stage.

Run local regression using **Windows Cygwin terminal** (Diaries repository):

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
python3 'change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/tests/retire-mars-legacy-test.py'
```

This script defaults to read-only and requires an explicit `--execute`, a root-owned, non-symlink approval document with `allow_delete=true` AND `accept_legacy_history_loss=true`, and checks the exact manifest digest. The approval must explicitly specify host `mars` and matching digest. **Do not create an approval file or run execute until the historical recovery loss, operational cutover and production protections are accepted.**

Safety controls: exact UUID and numeric subvolume ID matching, read-only Snapper metadata verification, refuses unexpected numeric snapshots, locked against native manager and daily legacy-prune, checksums checkpoint and replication protection metadata, bounded batches up to three, resumable only if missing metadata directories have disappeared. Does not remove Snapper or its timer/configuration or the `.snapshots` container. Does not alter native snapshot manager, receiver retention, or qgroups.

Limitations: The snapshot-manager exclusive lock coordinates with all manager operations but not arbitrary unrelated root processes; time-of-check risks from external changes are reduced by immediate UUID/ID rechecks, but not completely eliminated. Retirement requires an approved operational maintenance window; the daily legacy-prune timer should be disabled through reviewed Playbooks changes before approved execution to prevent untracked independent deletion between bounded batches. Do not confuse a passing dry-run with deletion approval.
