# Step 02 — Diagnostic findings and upgrade preflight (IN PROGRESS)

Date: 2026-10-21. All commands in cited captures were read-only. No deployment, reboot, cleanup, quota rescan, disable/re-enable, snapshot deletion, or scheduler mutation was performed for 0039-DEF.

## Cross-host qgroup evidence
| Item | `mars` | `backup` |
|---|---:|---:|
| Listed subvolumes plus root ID 5 (matching qgroups) | 146 | 134 |
| Unmatched level-0 qgroups | **39** | **29,437** |
| Unmatched with quota limits | 21 | 13,962 |
| Unmatched with nonzero referenced/exclusive bytes | 0 | 0 |
| Parent/child relationships | 0 (corrected by raw column examination) | 0 |
| Pending deleted subvolumes | none reported | none reported |
| Rescan in progress | No | No |

Evidence: `note(20261021-081914).txt`, `note(20261021-083102).txt`, `note(20261021-083733).txt`. The initial script reported `orphan_with_relationship: 39` on `mars`, **incorrectly** interpreting columns: actual headings include separate `Parent`, `Child` and `Path`, with `- - <stale>` and no relationships. The tool itself explicitly marks all 39 as `<stale>`. The exact origin of the `backup` accumulation is not yet attributed.

**Operator-supplied historical context:** stale/orphaned qgroups on `mars` were previously cleaned to zero after implementing the snapshot-manager diagnostic; the count has steadily risen. Treat this recurrence as a core defect requirement. Locate the original cleanup/diagnostic acceptance evidence if needed before asserting dates or commands.

## Source lifecycle observations (not root-cause proof)
- `note(20261021-082208).txt`: `roles/btrfs/files/initialise_btrfs_subvolume.py` calls `btrfs qgroup limit`; snapshot-manager native deletion uses `btrfs subvolume delete`.
- `note(20261021-082626).txt`: legacy deletion and prune delegate to `snapper delete`; older `remove_btrfs_subvolume.py` disables quotas before deleting, with no restoration in shown code. The active use of that helper is not established.
- `note(20261021-082841).txt`: no YAML/shell references to the older removal helper in the searched scope; this does not prove it was never manually executed.
- Snapshot-manager parser checks for a `Qgroupid` header and scans `<stale>`/`<under deletion>` markers in its default `btrfs qgroup show` output; does not independently compare surviving subvolume IDs. Actual format/version needs regression fixtures.

## OS, package and reboot preflight
| Check | `mars` | `backup` |
|---|---|---|
| Ubuntu | 24.04.4 LTS | 22.04.5 LTS |
| Running kernel | 6.8.0-138-generic | 5.15.0-164-generic |
| `btrfs-progs` installed / repository candidate | 6.6.3-1.1build2 / same | 5.16.2-1 / same |
| `linux-generic` metapackage | 6.8.0-147.147 installed/candidate | 5.15.0.198.171 installed/candidate |
| HWE package query | 24.04 HWE 7.0.0-38.38~24.04.4 candidate, not installed | queried `linux-generic-hwe-24.04` not available for 22.04; not an error |
| Restart-required flag | `*** System restart required ***` | `*** System restart required ***` |
| Held packages | none reported | none reported |
| Root filesystem | `/dev/mapper/ubuntu--vg-ubuntu--lv`, ext4 | `/dev/sda2`, Btrfs top level ID 5 |

Evidence: `note(20261021-084109).txt` (`mars`), `note(20261021-084146).txt` (`backup`), `note(20261021-090459).txt` (`mars`), `note(20261021-090531).txt` (`backup`).

`mars` has installed `linux-image-6.8.0-147-generic` but is booted on 6.8.0-138; newer installed images 139/142/146 also appear in its captured list. `backup` is booted on 5.15.0-164 and has a newer `linux-generic` metapackage; **its displayed installed-image list is lexicographically truncated via `tail -n 12` and does not prove which newer images are installed**. Confirm numerically before a reboot plan. Neither host has been rebooted.

## Analysis and remaining questions
- Is stale generation associated with Snapper legacy prune, native snapshot pruning, replication receive/delete, qgroup limits, or a kernel lifecycle deficiency? Correlate count/ID deltas with naturally occurring events; do not manually trigger deletion merely to test.
- On `backup`, why do 13,962 orphan records retain limits? Are limits retained after older snapshots are removed? Exact creation history unknown.
- Compare current installed snapshot-manager status behaviour with real `-pcre` output; distinguish parser-only failure from qgroup health.
- Proposed platform refresh: retain supported distribution packages; consider `backup` 22.04→24.04 as its own controlled maintenance operation, with provider console access, rollback plan and preserved bootable kernel. Avoid combining with mass cleanup. `mars` HWE optional, not yet justified.
- Decide if counting/clearing stale qgroups should be separate from performance/memory evaluation, and define no-go criteria for high filesystem utilisation.

**Gate:** Step 02 stays IN PROGRESS. Root cause and prevention are unproven. **No remediation authorised.**

## Exact deletion-to-stale-qgroup correlation (2026-10-21; newly accepted evidence)

**Primary source:** `note(20261021-092113).txt` (mars systemd journals and manager status). These observations are from existing activity, without manual invocation of deletion.

| Journal event (UTC) | Deletion mechanism | Snapper ID | Deleted Btrfs subvolume ID | Subsequent qgroup inventory |
|---|---|---:|---:|---|
| 2026-10-20 15:41:54 | `snapper -c @data delete` via legacy-prune | 19629 | 20189 | `0/20189`, `3.64TiB` limit, `<stale>` |
| 2026-10-20 15:43:13 | `snapper -c @data delete` via legacy-prune | 19677 | 20237 | `0/20237`, `3.64TiB` limit, `<stale>` |
| 2026-10-21 08:20:42 | `snapper -c @data delete` via legacy-prune | 19701 | 20261 | `0/20261`, `3.64TiB` limit, `<stale>` |

The three subvolume IDs appear **exactly** in the raw `btrfs qgroup show -pcre /media/usb` `<stale>` output (`note(20261021-083733).txt`, reconfirmed in `note(20261021-092525).txt`). Thus completed legacy deletion can leave a visible stale level-0 qgroup with a quota limit. This does **not** yet prove why the qgroup persists, whether its persistence is expected, or whether the application must remove it.

In the native prune journal, hourly operations typically delete two snapshots (`@data` and `root`) per complete set, with accepted holds and replication pins. The journal shows no reported execution failures or incomplete sets. `mars` status reported `complete_timestamp_sets=60`, `incomplete_timestamp_sets=0` and valid Diaries verification at capture. No deleted subvolumes were pending in the read-only query.

**Follow-on read-only inventory:** `note(20261021-092525).txt` enumerates **41** `<stale>` qgroups, up from the previous **39**; the new IDs are `0/20917` (no quota limit) and `0/20918` (`3.64TiB` max-referenced limit). All listed rows have max-exclusive `none`. `btrfs-snapshot-manager status` agrees: `qgroups_total=187`, `qgroups_stale=41`, `qgroups_under_deletion=0`, yet returns `qgroups_status=ok` because of the present warning threshold (100). The count increase is directly observed; assigning the two new IDs to a specific native-prune operation requires additional event/ID correlation.

The same capture counts **156** journal lines starting `DELETE ` from native prune since 2026-10-18, and **3** `LEGACY PRUNE DELETE` journal lines in that interval. **156 counts deletion lines, not complete snapshot sets or independently verified successful deletions**; the two sources are generally deleted per complete set. The `grep -c` values do not establish a one-to-one qgroup-generation rate or distinguish received/other operations.

**Step 02 interpretation:** Exact legacy deletion-to-stale-ID correlation accepted. Native deletion causality and the persistent- qgroup mechanism remain open. Do not initiate experimental deletions, mass qgroup destroys, quota changes, OS upgrades or service restarts under this gate.
