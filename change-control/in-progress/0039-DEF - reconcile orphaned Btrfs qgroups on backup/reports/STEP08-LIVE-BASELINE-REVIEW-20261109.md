# 0039-DEF — Step 8 live host baseline review (9 November 2026)

**Status:** Baseline acquisition PASSED on both hosts. Step 8 remains OPEN for acceptance of recurrence diagnosis; Step 9 remains OPEN pending corrected source regression and installed dry runs. No qgroup mutation or production installation has been executed by this review.

## Provenance

- Windows Diaries repository: branch `main`, HEAD `bca29dbb98d47afaf24642c0c4db09c2e5f07dcb`, modified 0039 documentation and untracked 0039 evidence/tools (user-run log `note(20261109-135244).txt`).
- `mango` Playbooks repository: branch `main`, HEAD `e0da797310ab452ddc61e7368c50a444fe881e41`, 11 modified/untracked qgroup-maintenance files (user-run log `note(20261109-133915).txt`).
- Ansible corrected `--check --diff` preview PASSED on `mars` and `backup` (user-run log `note(20261109-134214).txt`); this is not a deployment.
- Original full read-only evidence resides in `evidence/Step 08/mars-baseline-20261109-135149Z.txt` and `evidence/Step 08/backup-baseline-20261109-135152Z.txt` **in the Windows Diaries working copy**. Do not overwrite or duplicate those inventories.

## Verified findings

| Finding | mars | backup |
| --- | --- | --- |
| Kernel | 6.8.0-147-generic | 6.8.0-147-generic |
| btrfs-progs | v6.6.3 | v6.6.3 |
| Filesystem | `/media/usb` | `/` |
| Native `qgroup clear-stale` | Available | Available |
| Stale `0/*` qgroups in 13:51 UTC baseline | **656** | **0** |
| `btrfs-clear-stale-qgroups.timer` | Not installed | Enabled and active |
| Last daily cleanup | Not installed | 2026-11-09 05:30 UTC, success, 0 stale |
| `/etc/btrfs-stale-qgroups.json` | Not yet installed | Not yet installed |
| Snapshot manager mode | Omitted, conventionally source | `receiver` |
| Snapshot manager lock | `/run/lock/btrfs-snapshot-manager.lock` | Same |
| Writer lock path | `/media/usb/@data/backup/.btrfs-snapshot-writer.lock` | `/@data/mars-received/.replication-state/writer.lock` |

The observed accumulation on `mars` since earlier cleanup substantiates recurrence; the precise causal mechanism (which snapshot deletion/prune path creates persistent qgroups) remains to be established through existing operation logs or subsequent bounded observations. The collected baseline does not establish a kernel bug.

## Important source-contract correction

The initial shared script incorrectly expects a four-column header `qgroupid rfer excl path`. **Both hosts actually emit** `Qgroupid Referenced Exclusive Path`. The original 14 mock tests did not exercise the real header; the 9 November parser-correction ZIP adds regression tests based on this observed format, while retaining the tested compact format and refusing unsupported headings. Run the source tests again on `mango` after applying that package. This issue must be corrected before live dry-run or deployment.

The source snapshot-manager JSON omits `mode`, which the code already interprets as `source` using `config.get('mode', 'source')`; **this is not a defect**. The receiver explicitly declares `mode: receiver`.

## Timer and installation safety

`backup` already runs a successful 05:30 UTC cleanup timer. A real Ansible installation with `btrfs_stale_qgroup_maintenance_install_enabled=true` and `btrfs_stale_qgroup_maintenance_enabled=false` would **disable its existing automation**. Preserve that timer at any replacement deployment by using the explicitly agreed activation value `true` for both hosts, after reviewing dry-run and locks; do not run the earlier default-off installation example against backup in live mode. Preview/inspection is safe with check mode.

The shared design's 2,000 stale limit currently encompasses mars's 656 stale qgroups. This does **not** authorise executing cleanup before host-level dry-run/acceptance; the limit is a guard, not a proof of safety. Treat the scheduled service (when enabled) as mutating quota metadata. No snapshot/subvolume deletion, quota rescan, replication-state change, OS upgrade, or full restore is in scope.

## Next substantial action

1. Apply the two-file Playbooks parser correction on `mango` using Beyond Compare 4; confirm the local Git diff and re-run source unit tests.
2. Verify corrected code against the captured Btrfs qgroup inventories; the isolated offline replay passes with **656 `mars` and zero `backup` stale entries**.
3. Use Ansible check mode with **both activation flags true** to preview retention of the active `backup` timer and creation/activation on `mars`; review diff and any unrelated changes.
4. After accepting the corrected package, coordinate real installation on the hosts, run dry-run checks of the installed executable under the existing locks, then activate automatic cleanup through normal Playbooks deployment. Preserve the already working `backup` schedule.
5. Gather post-activation logs across normal snapshot/replication cycles before Step 11/closure. No repeat full restore is required solely by this source correction.
