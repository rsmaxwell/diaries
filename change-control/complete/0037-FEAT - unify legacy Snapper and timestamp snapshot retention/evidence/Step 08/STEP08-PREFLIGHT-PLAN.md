# 0037-FEAT — Step 8 live read-only preflight

**Status:** CLOSED — read-only captures reconciled and formally accepted 2026-10-19. See STEP08-RECONCILIATION.md and STEP08-FORMAL-CLOSURE.md.

## Objective

Capture the current `mars` snapshot and Snapper inventories, candidate `legacy-plan` reasoning, host/timezone, mount identity, native manager status, protection state as reported by the manager, and systemd timer status. Compare with the Step 4 baseline (57 native complete sets, 25 legacy @data snapshots, 17 KEEP / 8 WOULD-DELETE **at that earlier moment only**). Current inventories may legitimately differ; never reuse historical candidate IDs as deletion authority.

## Execution from Windows Cygwin

From the Diaries repository root:

```bash
bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tools/step08-capture-from-cygwin.sh"
```

The script invokes only read-only commands over `ssh mars` and writes results to `evidence/Step 08/`; it does not copy scripts or leave test files on `mars`. It calls `sudo -n` so a password prompt fails rather than hanging. **Do not use `legacy-delete`, `prune`, `create`, or `run`.**

## Review before closure

1. Reconcile Snapper `root`/`@data` SUBVOLUME paths with native sources and Btrfs mount; establish UTC/time semantics.
2. Compare complete/incomplete native sets, pins/holds as exposed by manager, and creation/prune schedules. If protection state cannot be evidenced, do not approve any deletion.
3. Count and explain every `KEEP`, `EXCLUDED`, and `WOULD-DELETE` entry in both text and JSON reports; reconcile against inventories and GFS buckets.
4. Preserve historical anchors and the minimum-age requirement; no prospective candidate is yet approved.
5. Assess receiver boundary separately: no attempt to treat received `backup` Btrfs subvolumes as local legacy Snapper. Step 1 documented a receiver diagnostic-path discrepancy; do not mutate it during Step 8.
6. Record expected changes versus Step 4 and any omissions/failures; attach operator results before formal Step 8 closure.

**Important:** This preflight is not a test of actual deletion-time revalidation or live replication correctness; those belong to later authorised gates.
