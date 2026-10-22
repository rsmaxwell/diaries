# Step 03 — Disposable qgroup-reconciliation Gates A–D, 2026-10-21

## Purpose and boundary

Preserve the original `mango` SSH logs for a **disposable** 512 MiB loopback-backed Btrfs rehearsal. Device `/dev/loop0`, image `/var/tmp/diaries-qgroup-reproduction/filesystem.img`, mount `/mnt/diaries-qgroup-reproduction`, UUID `8346c9fd-6dbb-45b6-94dc-e8b4728e2757`. Do not apply the commands to `backup` or `mars`. The image was **not dismantled** during these observations.

## Source evidence and integrity

The four logs below are copied byte-for-byte, with original filenames, into `reconciliation/mango/`. The exact SHA256 values are in `STEP03-RECONCILIATION-EVIDENCE-SHA256.txt`, whose paths are relative to the **defect root** (`0039-DEF - reconcile orphaned Btrfs qgroups on backup`), *not* relative to this Step 03 directory.

| Gate | Raw evidence | Outcome |
| --- | --- | --- |
| A — pre-destruction baseline | `reconciliation/mango/note(20261021-144806).txt` | PASS: image/loop/mount/UUID matched; subvolumes 256, 258; qgroups 0/5, 0/256, 0/257, 0/258, 0/259; no pending deletions/rescan |
| B — unlimited stale qgroup | `reconciliation/mango/note(20261021-144936).txt` | PASS: `btrfs qgroup destroy 0/257` succeeded; active rows unchanged; 0/259 still limited and stale |
| C — 1 TiB-limited stale qgroup | `reconciliation/mango/note(20261021-145100).txt` | PASS: `btrfs qgroup destroy 0/259` succeeded; exact active qgroup rows unchanged |
| D — final reconciliation/no-op | `reconciliation/mango/note(20261021-145218).txt` | PASS: exactly the expected two active subvolumes/three qgroups; zero `<stale>` candidates; no pending deletion/rescan |

## Inventory reconciliation

Before (Gate A):

| Qgroup | Referenced | Exclusive | Max referenced | Path/state |
| --- | ---: | ---: | --- | --- |
| `0/5` | 16.00 KiB | 16.00 KiB | none | `<toplevel>` |
| `0/256` | 16.00 KiB | 16.00 KiB | none | `source-a` |
| `0/257` | 0 B | 0 B | none | `<stale>` |
| `0/258` | 16.00 KiB | 16.00 KiB | none | `source-b` |
| `0/259` | 0 B | 0 B | 1.00 TiB | `<stale>` |

After (Gate D): **only `0/5`, `0/256`, `0/258` remained**, each at 16.00 KiB referenced and exclusive, no max limits, same paths. Both destroyed IDs were absent. Active subvolume IDs 256 and 258 survived; both deleted snapshots remained absent. All four command sequences terminated at their respective COMPLETE markers.

## Acceptance limits and outstanding work

The rehearsal validates selective destroy and a read-only no-op selection on this isolated filesystem with Btrfs utilities v6.6.3 and kernel 6.8.0-142. It does **not** prove safety of deleting any of the 29,437 unmatched production qgroups, nor production-scale operation, concurrent-change safety, checkpoint/receiver protection, rollback, Linux/Btrfs-version equivalence, or idempotency of a future implementation. The selected test qgroups had zero space accounting and no relationships. Destroying qgroups is not an undoable operation on production without additional recovery design.

**Rehearsal Gates A–D: PASS. Evidence preservation:** pending operator checksum verification after application to Windows checkout. **0039-DEF Step 03 remains IN PROGRESS** pending production remediation design and explicit safety/acceptance gates. No production Btrfs modification is authorised. Retain disposable image until a separately approved teardown.
