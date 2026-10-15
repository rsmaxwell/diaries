# 0035-FEAT Step 1 — observed host baseline and reconciliation

**Status: CLOSED — 2026-10-15 (read-only reconciliation gate).**

The updated `verification/0035-step1/capture-baseline.yaml` executed on `mango` against `pluto`, `mars` and `backup`. Source-contract regression reported PASS, and the play recap was `pluto ok=4`, `mars ok=6`, `backup ok=6`; all hosts `changed=0`, `failed=0`, `unreachable=0`. The complete operator-captured transcript is retained as `baseline-20261015-081000.txt` alongside this record. The separate earlier blocked attempt and timeout repair are part of the history, not a successful first run.

## Accepted observed baseline

| Subject | Actual observation | Reconciliation |
| --- | --- | --- |
| `pluto` filesystem | `/dev/mapper/ubuntu--vg-ubuntu--lv`, ext4, UUID `3b23e590-8faf-4a8d-ac0c-6426c559130a`; Diaries publication path on the same filesystem; no relevant Btrfs mounts | Consistent: no native Btrfs snapshots on `pluto` |
| `pluto` publication | `diaries-backup` symlink points to `.diaries-backup-generations/20261015-003023Z`; manifest `backupId=20261015-003023Z`, `logicalDataset=production`, `schemaVersion=2`; publish timer enabled, daily 00:30 UTC | Matches completed 0034 publication |
| `mars` filesystem | `/dev/sdb1` Btrfs mounted at `/media/usb`, filesystem UUID `72d1d8ea-900e-4fca-837f-1b1febec036c`; `@data` subvolume ID 260 / UUID `fc4585b5-1649-b94c-bcb6-a9253c9cf080`; `@snapshots` ID 20446 / UUID `0b89afc4-7dfa-024e-8459-e533e8bc5863` | Confirmed source identity and whole-backup-containing `@data` tree |
| `mars` timestamp sets | 53 complete paired `root,@data` timestamp sets, 0 incomplete; most recent at capture `20261015-080020Z`; source verification valid for production backup `20261015-003023Z` | Manager active and verified; no partial sets observed |
| `mars` protections | Held checkpoint `20261013-171228Z` includes both source UUIDs; replication-protected `@data` snapshot `20261015-030004Z` UUID `6f44e0e0-1968-6e4d-a3bd-9f77d71e9a47` | Held checkpoint preserved; protection matches receiver's newest receipt |
| `mars` schedules | `diaries-pull.timer` 01:30 UTC; `btrfs-snapshot-create.timer` hourly; prune at `*:15`; source-initiated `btrfs-native-push.timer` 03:30 UTC, all enabled; `richard` backup cron `45 1 * * *` (01:45 UTC); root backup cron `15 2 * * *` | Agrees with 0034 schedule change; retained root wrapper requires no Step 1 action |
| `backup` filesystem | `/dev/sda2` Btrfs at `/`, UUID `b915f967-7cb4-4c14-b11b-f52209637a22`; local `@data` ID 275 / UUID `8bbb95bf-664b-e344-82e6-09aa40dfec14`; `@snapshots` ID 55511 / UUID `0dc0ccef-c1a2-b74c-8f9c-e536fb85b269` | Confirmed separate receiver filesystem |
| `backup` receive | Eight accepted native receipt files and eight matching received subvolumes under `/@data/mars-received/@data/`; newest `20261015-030004Z` has `received_uuid=6f44e0e0-1968-6e4d-a3bd-9f77d71e9a47` | Latest native receive matches `mars` replication protection; historical `/@data/backup` remains separate |
| `backup` schedules | Native snapshot create/prune and legacy Snapper timers disabled; root and `richard` crontabs empty | Receiver stays install-only for local snapshot automation |
| Legacy snapshots | Snapper numeric snapshots still identifiable in raw Btrfs subvolume inventory on both hosts; Snapper create/boot/cleanup timers disabled on both | Historical snapshots preserved, no blanket deletion authorised |
| Quota-rescan | Independent capture reported `no rescan operation in progress` on both Btrfs hosts; an earlier operator check on `backup` reported an active rescan while Snapper blocked | Point-in-time observations differ; no inference that Snapper inventories are fully healthy |
| Current transfers | Process searches reported no independent active `rsync`, Btrfs send/receive or Diaries transfer process; their own capture shells appeared in the `ps` output | No active transfer demonstrated at capture time; snapshots may continue to be created by schedules |

## Exceptions explicitly carried forward

**E1 — Snapper inventory could not be completed (observation, not empty inventory).** Configuration discovery completed on both machines. Bounded `snapper -c @data list` timed out after 30 seconds on `mars`; both `@data` and `root` listings timed out after 30 seconds on `backup` (`exit_code=124`). `mars` `root` inventory returned only the current row. Preserve historic numeric snapshots; do not use a timed-out Snapper listing as proof of their absence. Follow-up diagnostic/controlled retirement belongs to later 0035 work, not Step 1.

**E2 — Receiver local manager verification path is stale/mismatched.** On `backup`, `btrfs-snapshot-manager status` reports `ERROR: verified Diaries dataset parent missing/unsafe: /@data/diaries-mars-replica/pluto`. Config points to `diaries-mars-replica/...`, while native received snapshots actually reside under `/@data/mars-received/@data/`. This affects the local manager/history verification configuration, **not** evidence that the generic native transport or existing receipts failed. Fix or explicitly disable/reconfigure this verification contract in a later separately tested 0035 step; do not redirect it blindly into an immutable received subtree.

**E3 — Historical storage retained.** `/@data/backup` on `backup` is the legacy rsync mirror and is not the native receive parent. Keep it untouched until separate explicit cleanup approval; retain numeric Snapper snapshots and checkpoint/replication holds.

## Closure decision

**Step 1 CLOSED as a read-only observation and reconciliation gate, with E1–E3 recorded for subsequent work.** This closes *inventory/reconciliation only*. It is **not** approval to prune historic snapshots, modify timers, change manager verification settings, start/stop replication, delete `/@data/backup`, or declare all Snapper inventory calls healthy. No filesystems or data were changed by the capture (`changed=0` on every host). Do not interpret the Ansible success recap as proof that all inventory subcommands succeeded: their bounded timeouts are explicitly preserved above.

## Original capture contract (historical)

# 0035-FEAT Step 1 — baseline reconciliation evidence

**Historical pre-run status: IMPLEMENTED / LIVE RECONCILIATION PENDING — 2026-10-15**

Step 1 is a read-only gate. The Playbooks implementation is:

```text
verification/0035-step1/capture-baseline.yaml
verification/0035-step1/verify-source-contract.py
verification/0035-step1/README.md
```

The capture inventories `pluto`, `mars` and `backup` without changing filesystems, snapshots, timers, cron, transfer state or data.

## Carry-forward facts to compare against live capture

These are prior accepted 0034 observations and are **not substitutes for current Step 1 evidence**:

- `pluto` was treated as non-Btrfs/ext4 for the production Diaries publication path.
- the completed unattended production chain recorded schema-2 publication `20261015-003023Z` on `pluto` and a verified `mars` timestamp snapshot / accepted off-site receive `20261015-030004Z`.
- `mars` uses the Btrfs tree rooted at `/media/usb`, with whole-backup data under `/media/usb/@data/backup` and managed timestamp snapshots under `/media/usb/@snapshots`.
- native off-site replication now runs source-initiated from `mars` to the isolated receiver tree on `backup`; the older `/@data/backup` rsync mirror is retained as historical data and is not a native Btrfs receive baseline.
- the `mars` normal-user backup cron was moved to **01:45 UTC**; the 0034 close-out recorded the old remote-rsync off-site schedule disabled before native push scheduling.
- checkpoint `20261013-171228Z` was intentionally held. Existing replication-parent protections and historical Snapper data were to remain in place until separately authorised.

## Evidence still required

Run on `mango`:

```bash
cd ~/playbooks
python3 verification/0035-step1/verify-source-contract.py
ansible-playbook verification/0035-step1/capture-baseline.yaml --ask-vault-pass
```

Retain the Ansible output and reconcile:

1. mount devices/filesystem UUIDs and filesystem types;
2. `root`/`@data` subvolume IDs and UUID lineage where applicable;
3. `@snapshots` location and read-only timestamp snapshot inventory;
4. Snapper configurations, numeric snapshots and timer state;
5. current cron/systemd schedules on all relevant hosts;
6. `mars` checkpoint/replication protection state;
7. `backup` accepted receive receipts and received UUIDs;
8. historical `/@data/backup` classification and preservation; and
9. absence/presence of an active transfer at capture time.

**Closure gate:** no pre-existing snapshot or data is overwritten or deleted, and any difference from the 0034 carry-forward facts is understood and recorded before proceeding to Step 2.
