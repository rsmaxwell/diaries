# 0040 Step 12.3 — Btrfs read-only received-subvolume rename boundary

The real-Btrfs test on `mango` (2026-11-03 09:05) failed at `renameat2(RENAME_NOREPLACE)` with EROFS while moving an intact received readonly Btrfs subvolume from a nonce staging directory to the final snapshot parent.

This is a diagnostic test ONLY. It does not change receiver runtime, journals, pruning, timers or production filesystems.

From the **SSH terminal on `mango`**:

```bash
cd /home/richard/playbooks
(
  python3 -m py_compile roles/btrfs-replication/tests/verify-0040-step12-3-btrfs-rename-boundary.py &&
  sudo -n python3 roles/btrfs-replication/tests/verify-0040-step12-3-btrfs-rename-boundary.py --run &&
  git diff --check
)
if [ "$?" -eq 0 ]; then echo 'PASS: isolated Btrfs rename boundary'; else echo 'FAIL: isolated Btrfs rename boundary'; fi
```

The test creates **two fresh 512 MiB sparse Btrfs image files** under a temporary folder and mounts them via loopback; it uses no pre-existing mounts or snapshots. It receives a read-only snapshot from the disposable source filesystem. It then attempts the formerly failing cross-parent rename, and tests whether same-parent rename (then reversal) preserves both subvolume UUID and received UUID. It verifies readonly status and uses `renameat2` with `RENAME_NOREPLACE` for each move.

If unmount fails, the test **retains** its test images and reports the path rather than deleting a mounted filesystem.

**A same-parent PASS is not a production architecture approval.** The test initially receives under the visible final name. A safe redesign must address that exposure, coordinate all final-namespace consumers/pruners, prove crash-safe reservation and publication, and maintain authentication and journal invariants. Do not switch the receiver or unattended timer from the existing working path on this evidence alone. No automatic cleanup of agreed-parent snapshots is authorised.
