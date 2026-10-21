# Step 11 — Controlled execution of approved snapshot 19605

**Decision:** Conditional execution GO for the *single* approved ID `19605` on `mars`, Snapper config and source `@data`. Commands below are destructive at the explicit `legacy-delete --execute` step. Do not run on `backup` or `mango`. No deletion was carried out when this document was created.

## A. In the existing `mars` SSH terminal: last-minute read-only checks

Choose a quiet interval clear of native create/prune and replication jobs. Do not proceed during a scheduled run. Run:

```bash
hostname
sudo sha256sum /usr/local/sbin/btrfs-snapshot-manager
sudo btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data
sudo snapper --csvout --iso -c @data list
sudo btrfs subvolume show /media/usb/@data/.snapshots/19605/snapshot
sudo btrfs property get -ts /media/usb/@data/.snapshots/19605/snapshot ro
sudo btrfs-snapshot-manager status
sudo btrfs-snapshot-manager prune --dry-run
sudo btrfs-snapshot-manager hold-list
systemctl list-timers --all --no-pager | grep -E 'snapper|btrfs-snapshot|diaries' || true
ps -eo pid,ppid,stat,etime,args | grep -E '[s]napper|[b]trfs (send|receive)|[b]trfs-snapshot-manager|[d]iaries.*(push|pull)' || true
```

Compare exact candidate **ID 19605**, **UUID `489332dc-3b48-eb40-b59a-d9bd86cc9915`**, **subvolume ID `20165`**, **creation `2026-09-28 00:00:38 UTC`**, **`ro=true`**, **`WOULD-DELETE`**, expected native holds and replication pin. Verify `backup` still carries `20261020-030026Z` and matching receipt, or a later validated successor, before proceeding. If *anything* is unexpected, **STOP; NO-GO**. Do not disable native timers as a workaround.

Manager checksum expected: `3eb8717fdb06410943a2e9513dfc5f3e8b6892021bac0d741b58e2524bdff671`. Note executable can be a wrapper/symlink; identify the installed underlying Python manager before comparing checksum. No second snapshot is approved.

## B. Explicit single-ID execution (only after A passes)

The following is meant to be **run manually in your `mars` SSH terminal**. It creates a short-lived, root-owned approval file, invokes the manager once, and removes the approval file even on failure. It does not use `snapper delete` directly.

```bash
sudo bash -euo pipefail <<'ROOT'
approval=$(mktemp /root/legacy-19605-approval.XXXXXXXX.json)
trap 'rm -f -- "$approval"' EXIT
chmod 600 "$approval"
cat > "$approval" <<'JSON'
{"enabled":true,"allow_delete":true,"host":"mars","source":"@data","snapper_config":"@data","snapshot_id":19605}
JSON
printf 'Approval file permissions: '
stat -c '%U %a %n' "$approval"
printf 'Executing one approved legacy-delete ID 19605 on mars.
'
btrfs-snapshot-manager legacy-delete   --approval-file "$approval"   --source @data --snapper-config @data --snapshot-id 19605 --execute
ROOT
```

**Expected success:** manager emits `LEGACY DELETE approved ... id=19605` followed by `LEGACY DELETE completed ... id=19605` and exit code zero. Non-zero, missing output or unexpected action means stop and preserve diagnostics. The manager acquires its native lock, validates the approval file, and performs two fresh retention checks before calling Snapper.

## C. Postconditions (before Step 11 closure)

```bash
sudo snapper --csvout --iso -c @data list
sudo btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data
sudo btrfs-snapshot-manager status
sudo btrfs-snapshot-manager list
sudo btrfs-snapshot-manager prune --dry-run
sudo btrfs-snapshot-manager hold-list
systemctl --failed --no-pager
```

Require `19605` absent; no other legacy snapshots missing; complete native snapshot sets, holds, replication pin and off-site receiver/receipt preserved. Save the whole operator terminal output in `evidence/Step 11/execution/` (inside the feature directory) and capture receiver observation from `backup`. **Do not delete any further IDs.**

## D. Outstanding housekeeping

`diaries-pull.timer` on `mars` displayed 01:30 UTC in the 07:56 preflight; compare its unit and overrides with the expected 01:45 schedule separately. Do not change timer configuration during this pilot.
