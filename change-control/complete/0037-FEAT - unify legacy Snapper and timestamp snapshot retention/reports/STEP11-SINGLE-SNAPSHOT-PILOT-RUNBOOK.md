# 0037-FEAT Step 11 — Controlled pilot procedure (preparation only)

**Status: PREPARED; NOT EXECUTED.** The operator has approved only `mars` / source `@data` / Snapper config `@data` / ID `19605`. No scheduled or batch legacy deletion is approved.

## Stage A — fresh checks in existing `mars` SSH terminal (read-only)

```bash
hostname
sudo btrfs-snapshot-manager status
sudo btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data
sudo snapper --csvout --iso -c @data list
sudo btrfs subvolume show /media/usb/@data/.snapshots/19605/snapshot
sudo btrfs property get -ts /media/usb/@data/.snapshots/19605/snapshot ro
systemctl list-timers --all --no-pager | grep -E 'snapshot|snapper|diaries' || true
ps -eo pid,stat,args | grep -E '[b]trfs (send|receive)|[s]napper|[b]trfs-snapshot-manager|[d]iaries.*(push|pull)' || true
```

Require the preflight reviewed identity (2026-09-28 00:00:38 UTC, subvolume ID 20165, UUID 489332dc-3b48-eb40-b59a-d9bd86cc9915) and an unchanged `WOULD-DELETE` decision. Check checkpoint holds, replication-pin state and the current receiver status; capture output to feature-local evidence. If anything differs, **STOP**.

## Stage B — approval construction and execution gate (not authorised by this runbook alone)

The implementation requires a root-owned, non-symlink, non-group/world-writable JSON file. The documented schema is shown **disabled** for review:

```json
{
  "enabled": false,
  "allow_delete": false,
  "host": "mars",
  "source": "@data",
  "snapper_config": "@data",
  "snapshot_id": 19605
}
```

Only after satisfactory *same-session* checks and a deliberate go/no-go decision for Step 11 should an operator create a root-owned approval in a protected temporary location on `mars` and enable the two booleans. The approved manager command has the following argument shape; it is intentionally **not** supplied as an immediately runnable deletion command here:

`sudo btrfs-snapshot-manager legacy-delete --approval-file PATH --source @data --snapper-config @data --snapshot-id 19605 --execute`

That command is destructive. Avoid shell history accidents: do not run it until Step 11's pre-execution evidence is reviewed. Record the approval path and its ownership/mode, the full manager output and exit status; deactivate/remove the approval regardless of success or failure. The manager re-runs the candidate plan twice before invoking Snapper, but the two inspections do not substitute for operator checks of unrelated recovery/replication paths.

## Stage C — required postconditions

- Confirm `snapper -c @data list` no longer reports `19605` and no other legacy ID has vanished unexpectedly.
- Capture fresh manager `legacy-plan --json`, native `status`/`list`/dry-run, checkpoint holds, replication pin state and receiver receipt observations.
- Verify no failed native snapshot service or newly affected off-site path; stop and investigate unexpected state.
- Preserve outputs under `evidence/Step 11/`; close the pilot only on complete evidence. No second ID is automatically authorised.

## Operational bounds

Step 10's approval is an **authorisation to undertake one carefully gated pilot**, not proof that deleted data can be restored. Deleting a legacy Snapper snapshot cannot be undone merely by restoring the manager executable. If fresh recovery evidence is insufficient or a protection is uncertain, defer execution.
