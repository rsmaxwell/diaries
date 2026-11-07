0040-FEAT Step 12.3 — Disposable real-Btrfs integration test (2026-11-03)

Package is repository-relative to /home/richard/playbooks on mango. Apply
using Beyond Compare 4 after checking the Playbooks checkout for local changes.

Run in SSH terminal on mango:

cd /home/richard/playbooks
(
  python3 -m py_compile roles/btrfs-replication/tests/verify-0040-step12-3-real-btrfs-staging.py &&
  sudo -n python3 roles/btrfs-replication/tests/verify-0040-step12-3-real-btrfs-staging.py --run &&
  git diff --check
)
if [ "$?" -eq 0 ]; then
  echo 'PASS: isolated real-Btrfs staging smoke test'
else
  echo 'FAIL: isolated real-Btrfs staging smoke test'
fi

Requires btrfs-progs, mkfs.btrfs, root, and support for loopback-mounted Btrfs.
Creates only two newly allocated, disposable 512 MiB sparse image files in a
unique temporary directory. Formats ONLY those new files (never a disk device),
mounts them as separate source/receiver Btrfs filesystems, creates A/B read-only
snapshots, sends full A and incremental B, inspects the received B with the
production read-only inspector, publishes B via the production no-overwrite
staging helper, verifies UUID/read-only/payload and rejects a second publish.

No production paths, snapshots, services, scheduler, or SSH endpoints are used.
Test-owned images and mounts are removed after a successful unmount. On failure
to unmount, they are retained for explicit operator intervention. DO NOT run a
manual recursive delete of the printed working directory while a mount is active.

This does not test the fixed receiver CLI, systemd scope supervision, sender
proof authentication, receipt commit, crash fencing or automatic cleanup/retry.
Those operational gates remain OPEN. Do not deploy staged mode or change the
03:30 native timer solely on the basis of this test.
