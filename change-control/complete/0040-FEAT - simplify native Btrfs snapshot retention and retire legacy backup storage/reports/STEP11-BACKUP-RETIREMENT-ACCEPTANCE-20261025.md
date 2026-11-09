# 0040-FEAT Step 11 — Backup Snapper retirement acceptance

**Date:** 25 October 2026  
**Scope:** `backup` only  
**Decision:** **ACCEPTED for backup**; overall Step 11 remains **OPEN** pending `mars` scope and remaining acceptance criteria.

## Controlled destructive retirement

The previously frozen 113-entry UUID allowlist was executed in seven bounded batches, all exiting successfully:

| Batch | Deleted | Approved remaining |
| --- | ---: | ---: |
| 01 | 5 | 108 |
| 02 | 20 | 88 |
| 03 | 20 | 68 |
| 04 | 20 | 48 |
| 05 | 20 | 28 |
| 06 | 20 | 8 |
| 07 | 8 | 0 |

The read-only final plan reported `approved=113 remaining=0 completed=113`. Including the **two earlier individually approved** pilot deletions, the full original numerical legacy population retired was **115**. Each batch has its original `DELETE-BEGIN`/`DELETE-COMPLETE` log on `mango`.

## Unexpected APT-created root snapshot and cleanup

When `apt-get remove snapper` ran, Snapper's still-installed APT pre-invoke hook triggered `snapper create -d apt -c number -t pre -p` at **2026-10-25 11:57:13 UTC**, creating `/.snapshots/1/snapshot` (Btrfs ID **55873**, UUID `c8599199-bb4f-ed4d-8cc6-168d168f52f2`). Its `info.xml` classified it as a pre-APT snapshot. This was a **new** snapshot, not an overlooked original manifest entry. Disabling `snapperd.service` had not prevented activation by the APT hook. This behaviour was investigated using the journal and exact snapshot metadata before cleanup.

The `snapper` package was removed and then purged; purge removed `/etc/apt/apt.conf.d/80snapper` without removing the three packages APT had proposed only for a possible later `autoremove` (which was **not** run). With the hook absent and the executable unavailable, the added snapshot and its metadata directory were removed using exact UUID/ID, directory-content and actual mount-table guards. Two empty legacy Snapper container subvolumes were then deleted: `/.snapshots` (ID **307**, UUID `621c8df8-992f-8143-b427-6624d273e720`) and `/@data/.snapshots` (ID **309**, UUID `e8690a2f-a2e9-2d4f-930b-314a9d8b2b90`). Output: `LEGACY-BTRFS-CLEANUP-COMPLETE deleted_subvolumes=3` and pipeline exit statuses `0 0`.

Four remaining `/etc/snapper` configuration files were individually removed. The cleanup script exited nonzero trying to remove the top-level directory, but a later independent check confirmed **`/etc/snapper` absent**; do not misrepresent the initial command as wholly successful.

## Final evidence and safety

- No legacy Snapper subvolumes remained in `btrfs subvolume list -u /`.
- Native receiver inventory: `snapshots=21`, `problems=0`, directory `/@data/mars-received/@data`.
- Receiver recovery: `CLEAN`; no receiver-pruning activation was performed as part of this retirement.
- Snapper executable, APT hook and `/etc/snapper` were confirmed absent.
- **116** numerical Snapper snapshot subvolumes deleted in total (115 original + one APT-created); plus **2** container subvolumes.
- `backup` technical Snapper retirement accepted. Not evidence of `mars` retirement, new incremental success after this event, or enabled receiver pruning.

## Raw evidence (mango)

Directory `/home/richard/0040-step10-evidence/` holds:

- `backup-retirement-batch01.txt` through `backup-retirement-batch07.txt`
- `backup-retirement-final-plan.txt`, `backup-retirement-final-receiver.txt`, `backup-retirement-final-subvolumes.txt`
- `backup-retirement-uninstall.txt`, `backup-retirement-purge.txt`, `backup-retirement-final-cleanup.txt`, `backup-retirement-final-verification.txt`
- `backup-retirement-config-cleanup.txt`, `backup-retirement-config-residue.txt`, `backup-retirement-step10-summary.txt`
- The approved 113-target manifest and earlier baseline/validation outputs.

**Evidence preservation:** The named outputs are on `mango`, not embedded in this documentation-only package. Transfer/archive the logs through the already accepted evidence preservation workflow before deleting staging directories; retain manifest/checksum and operator authorisation. Avoid mixing temporary evidence into production roles.

## Outstanding gates

Keep overall **Step 11 OPEN** until `mars` root/legacy retirement and any other planned destructive targets have completed under separately approved identities and holds. Keep **Step 12 OPEN**: receiver-side pruning remains disabled pending its own cross-host parent-safety and controlled activation gate. **Step 13 and feature closure also remain OPEN.** No repeat full restore is proposed on this evidence alone.


## Later reconciliation (26 October 2026)

The separate `mars` root historical population of 63 has now been retired and verified, and its native replication schedule restored. See `STEP11-MARS-ROOT-RETIREMENT-ACCEPTANCE-20261026.md`. This does not alter the 25 October backup-specific acceptance or activate receiver pruning. The **overall** Step 11 remains OPEN until remaining legacy targets and evidence archiving are reconciled.
