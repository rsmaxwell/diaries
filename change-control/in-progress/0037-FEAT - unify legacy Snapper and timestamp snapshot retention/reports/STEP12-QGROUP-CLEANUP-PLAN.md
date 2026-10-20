> **Historical pre-execution plan.** Cleanup was completed 2026-10-20; authoritative closure at `evidence/Step 12/STEP12-RECONCILIATION-AND-CLOSURE.md`. The OPEN / NOT approved statements below describe the gate *before* operator execution.

# 0037-FEAT — Step 12: stale Btrfs qgroup maintenance

Status: **OPEN — READ-ONLY PREFLIGHT; execution NOT approved**.

## Scope
Host `mars`, Btrfs filesystem mounted at `/media/usb` (historically `/dev/sdb1`). Earlier evidence showed approximately 16,000 `<stale>` quota group entries. Step 11 safely deleted only Snapper `@data/19605` and is CLOSED. No further snapshots are approved for deletion.

## Gate A — source and host baseline
Run `tools/step12-qgroup-preflight-from-cygwin.sh` from the Windows Diaries repository root. It uses SSH to `mars` and places all results in `evidence/Step 12/qgroup-preflight`. Inspect shell exit codes, mounted filesystem UUID, btrfs-progs version, and command availability. The tool is read-only.

## Gate B — operator review and decision
Review full quota list; counts of stale, live and under-deletion qgroups; any nonzero stale usage; hierarchy/limits; snapshot counts and holds; device errors and any USB warnings. Independently check the latest off-site replication receipt and maintenance concurrency before any metadata mutation. A successful capture is **not** approval to run cleanup.

## Gate C — controlled cleanup (separate authorisation required)
Only after reviewed GO, consider `sudo btrfs qgroup clear-stale /media/usb` if supported by the installed btrfs-progs. Official documentation says this removes stale level-0 qgroups without existing subvolumes. It may incur quota metadata I/O and does not address the underlying rate of accumulation. Avoid simultaneous create/prune, send/receive and other quota maintenance. Record terminal transcript. Do not disable quotas or perform `btrfs quota rescan` by default.

## Gate D — reconciliation
Compare pre/post qgroups, retained active qgroups, snapshot inventories, native set completeness, holds, replication pins, kernel/device error state and any new stale entries. Record errors honestly; retain the gate open if verification is incomplete.

References: https://btrfs.readthedocs.io/en/latest/btrfs-qgroup.html
