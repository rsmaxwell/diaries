# 0034-FEAT — Step 1 formal close-out

**Date:** 2026-10-08  
**Status:** COMPLETE — evidence accepted  
**Step:** Freeze the 0033 production backup contract and current storage baseline

## Decision

All Step-1 acceptance criteria are met by the supplied source regression and read-only production evidence. **Step 1 is formally closed; Step 2 may begin.** This closes only Step 1, not 0034-FEAT.

## Source contract evidence

`RUNTIME-WINDOWS-CONTRACT-REGRESSION.txt` records the five successful checks:

1. 0033 schema-2 media contract — PASS.
2. 0033 production backup semantics — PASS.
3. 0033 operational script classification — PASS.
4. 0034 compatibility promise — PASS.
5. 0034 Step 1 frozen 0033 contract — PASS.

The frozen schema-2 backup directory structure, completion markers, UTC IDs, `.partial` semantics, precise SHA-256/path/size validation and restore compatibility remain the regression boundary for 0034.

## Current production baseline

The read-only `pluto` run captured **2026-10-08T07:51:31Z** and ended with `STEP-1 BASELINE CAPTURE PASSED`. Observations:

| Item | Baseline |
| --- | --- |
| Host | `pluto` |
| Repository | `/home/richard/projects/diaries/data/dataset-backups/production` |
| Restore state | `/home/richard/projects/diaries/data/dataset-restores/production` |
| Underlying mount | `/dev/mapper/ubuntu--vg-ubuntu--lv` on `/` |
| Filesystem | **ext4**, confirmed by `findmnt` / `df -hT` |
| Space | 67G total; 41G used; 23G available; 65% used |
| Completed media | `20261007-145013Z` — schema-2 valid, `production`, 89 Files |
| Non-restorable workspace | `.20261007-143438Z.partial` — retained untouched |
| Production DB | Docker volume `diaries-db-data` / database `diaries` |
| Mutable Files selector | `files` (`diaries_nas-photo` Docker volume) |
| Writer | Responder running at preflight |
| Staging | `excluded-benign (1 entries)` |
| Preflight | PASS; no writer stopped and no workspace created |

`stat -f` formats this ext4 filesystem type as `ext2/ext3`; `findmnt` and `df -hT` report `ext4`. This is not conflicting evidence and **does not** establish Btrfs readiness. The current ext4 repository is a frozen starting point only.

The raw host transcript also shows an initial `/tmp` not-found error before the script was placed at the referenced location. A subsequent execution succeeded and captured the complete baseline. Both are preserved without alteration.

Deployed SHA-256s for the seven production complete-dataset scripts are preserved in `RUNTIME-PRODUCTION-STORAGE-BASELINE.txt` for later comparison.

## Change / safety boundary

No new backup, production restore, service restart, filesystem mount alteration, Btrfs operation, or repository migration was performed as part of the accepted capture. There are **no application image changes and no deployment requirement** for this documentation-only close-out.

The existing completed backup and historical `.partial` workspace must not be rewritten or cleaned up as an incidental part of 0034.

## Step 2 hand-off

Step 2 can now establish an explicit Playbooks-managed **production complete-backup repository root** while keeping the mutable Files root and restore state root distinct. The future Btrfs destination and enablement policy are **not** inferred from the ext4 baseline. Do not implement reflink seeding or alter schema-2 media semantics during the Step-2 configuration freeze.

**Acceptance:** PASS / Step 1 CLOSED / 0034-FEAT remains IN PROGRESS.
