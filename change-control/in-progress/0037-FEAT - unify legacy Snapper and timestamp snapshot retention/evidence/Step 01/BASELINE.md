# Step 1 — Baseline and scope freeze (closed 2026-10-19)

Date: 2026-10-19. Sources: `playbook-sources-20261019-073838.zip` and the approved 0037-FEAT change-control package. Read-only source inspection, **not** live-host verification.

## In-scope systems

- `mars`: source-side snapshot management, legacy Snapper inventory/configurations, native timestamp sets, scheduler state, replication pins and checkpoint holds. No deletion or timer changes authorised by Step 1.
- `backup`: receiver boundary, received snapshots and replication lineage; **excluded** from any combined local-retention deletion policy. Baseline capture only.
- `mango`: operator/controller, source and captured evidence workspace, not a target for snapshot deletion.
- `pluto`: upstream Diaries data source; no application or database alteration in 0037 Step 1.

## Proven from Playbooks source (not a claim about live runtime)

- Native sources are configured as paired `root` and `@data` (role defaults), and timestamp naming is `YYYYMMDD-HHmmssZ` (UTC).
- Default GFS windows: 48 hourly, 14 daily, 12 weekly, 24 monthly, 5 yearly; minimum age 30 minutes. Host-specific overrides and rendered runtime config still need verification.
- Native pruning evaluates *complete timestamp sets*, refuses incomplete sets, and consults replication-protection pins and checkpoint holds before selecting deletions.
- Existing legacy Snapper snapshots do not enter native `retention_keep_set`; the native manager does not read/remove numbered `.snapshots/<number>` entries.
- The local-backup and remote-backup role call sites set `btrfs_snapshot_retire_legacy_snapper_timers: true`. The retirement task disables `snapper-timeline.timer`, `snapper-boot.timer`, `snapper-cleanup.timer` where installed, but does not delete Snapper snapshots/configs. This is deployment intent, not proof of service runtime state.
- Snapshot creation/pruning role defaults are hourly at `:00` and `:15` respectively; verify actual installed timers before relying upon these defaults.
- Template enables mandatory replication protection and checkpoint holds when `inventory_hostname == "mars"`. Check actual configuration and state on `mars` without exposing secret material.
- `backup` is configured with a timestamp manager too, but received `mars -> backup` snapshots remain outside this feature's combined deletion logic.

## Live evidence and reconciliation (2026-10-19)

- `mars-capture.txt` (105 lines) confirms Btrfs at `/media/usb`, configured `root`/`@data`, native snapshot create/prune timers enabled, legacy Snapper timers disabled. The native inventory reported 57 complete timestamp sets at the second capture; no native deletions were proposed in its dry-run. Earlier capture reported 58 sets and one dry-run candidate: these are observations at different times, not a frozen immutable population.
- Direct `snapper -c root list` and `snapper -c @data list` terminal evidence (`note(20261019-074424).txt`, shared in the feature conversation) identifies **0 numbered legacy root snapshots and 25 numbered legacy @data snapshots**, from 2024-05-26 through 2026-10-09. This direct inventory is not embedded in the bundle; retain a reference to the operator capture and re-run before any deletion planning.
- `backup-capture.txt` (43 lines) confirms Btrfs `/dev/sda2` (UUID `b915f967-7cb4-4c14-b11b-f52209637a22`) and both native and Snapper timers disabled. Its native manager inspection fails closed: `verified Diaries dataset parent missing/unsafe: /@data/diaries-mars-replica/pluto`.
- Follow-up read-only `findmnt`, `find`, `ls`, and `btrfs subvolume list /` output (terminal notes `note(20261019-075544).txt`, `note(20261019-075616).txt`, `note(20261019-075711).txt`, `note(20261019-075736).txt`) establishes the extant receiver under `/@data/mars-received/@data/` with **13 received timestamp-named @data subvolumes** spanning 2026-10-09 to 2026-10-19, plus `/@data/mars-received/.replication-state/`.
- The obsolete/inapplicable `/@data/diaries-mars-replica/pluto` validation path is a **documented unresolved diagnostic configuration discrepancy**, **not** evidence of replica loss and **not** a verified-good receiver-manager status. No attempt was made to create/move directories, alter configuration, or delete snapshots.

## Scope and safety invariants

The unified retention feature operates on local `mars` snapshot history only. `backup` received snapshot lifecycle and replication parent/receipt handling are explicitly excluded. Legacy snapshots are never assumed equivalent to coordinated native `root`+`@data` sets. All changes and deletions remain prohibited in Step 1; later steps require dry-run, revalidation, and explicit approval.

## Step 1 formal decision

**CLOSED — 2026-10-19 (baseline and scope freeze only).** The live-host baseline and relevant legacy populations have been established sufficiently for retention model design. Receiver diagnostic-path discrepancy recorded as a limitation to revisit during Step 9 deployment/receiver-boundary validation, without authorising correction or deletion. No quantitative transfer/restore assurance or receiver-manager successful invocation is asserted by this closure. No production mutation performed.
