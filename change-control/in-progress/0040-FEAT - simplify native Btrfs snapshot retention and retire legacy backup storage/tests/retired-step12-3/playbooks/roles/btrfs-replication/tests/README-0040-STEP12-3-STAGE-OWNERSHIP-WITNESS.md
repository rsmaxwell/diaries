# 0040-FEAT Step 12.3 — receiver-owned stage creation witness

The staged receive coordinator now observes the exact private Btrfs subvolume
during supervised scoped streaming. The observation is written once to a
root-owned, mode-0600, fsynced sidecar under the receiver state directory,
bound to the durable nonce, candidate, scope, receiver boot, parent directory,
stage inode and Btrfs subvolume UUID.

An unwitnessed incomplete receive remains manual-only. An existing sidecar
may be read back, never overwritten with a different identity. A successful
staged stream requires a durable creation witness. This code does not delete
subvolumes, remove journals, grant retransmission, change the sender or change
systemd timers. The witness is **necessary but not sufficient** for future
cleanup: recovery must additionally prove the previous-boot process fence,
current Btrfs UUID+inode, no publication/receipt, stable receiver state and a
durable post-deletion readback.

The original `--receive` and `--receive-scoped` paths remain unchanged. Do
not deploy independently of the rest of the staged runtime and do not enable
automatic cleanup/retry until a controlled destructive test of disposable Btrfs
subvolumes and sender/receiver recovery hand-off has passed.

## Source regression on mango

From `/home/richard/playbooks`:

```bash
(
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-stage-ownership-capture.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-stage-observer-integration.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-coordinator.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-migrated-receive.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-recovery-assessment.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-fixed-receiver.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-postreceive.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-scoped-integrated-binding.py &&
  python3 -m py_compile roles/btrfs-replication/files/btrfs-agreed-parent-stage-ownership.py roles/btrfs-replication/files/btrfs-agreed-parent-receive-core.py &&
  git diff --check
)
if [ "$?" -eq 0 ]; then echo 'PASS: stage creation witness'; else echo 'FAIL: stage creation witness'; fi
```

No interactive-shell fail-fast options are used.
