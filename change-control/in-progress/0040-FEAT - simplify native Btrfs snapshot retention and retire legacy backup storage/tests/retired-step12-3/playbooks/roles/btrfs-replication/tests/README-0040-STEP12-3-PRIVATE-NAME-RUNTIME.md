# 0040 Step 12.3 — private-name Btrfs receive adaptation

Source-level implementation, **not yet approved for production deployment**.

The root-owned fixed `staged-receiver` endpoint validates the nonce-bound
receiver journal and FINAL parent directory device/inode. It reads and verifies
at most 64 KiB of the Btrfs stream's first command before launching `btrfs receive`.
It changes exactly the initial PATH TLV from the expected timestamp to
`.receive-<64hex-nonce>` and recalculates the command CRC32C. The rest of the
stream is copied unchanged in <=1 MiB chunks, without buffering the whole
stream or writing stream data to temporary files. An invalid first command
fails without starting `btrfs receive`.

The parent directory ` /@data/mars-received/@data ` is pinned by root-owned
journal device/inode. A `.receive-<nonce>` subvolume is created there by Btrfs,
never under a published timestamp. Publication is an atomic same-parent
`renameat2(RENAME_NOREPLACE)` from the nonce-private name to the timestamp.
Publication requires lock-held authenticated sender proof, a durable witness
and verified Btrfs identity. Interrupted private subvolumes remain for
reconciliation: **no automatic deletion, restart or retransfer** is enabled.

Snapshot inventory and pruning logic select timestamp-shaped names; private
`.receive-` entries do not match the strict timestamp pattern. This exclusion
must also be verified in the final operational acceptance exercise.

## Validation (terminal: SSH `mango`)

Run after applying the package to `/home/richard/playbooks` with Beyond Compare:

```bash
cd /home/richard/playbooks
(
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-private-stream-runtime.py &&
  sudo -n python3 roles/btrfs-replication/tests/verify-0040-step12-3-same-parent-storage.py &&
  sudo -n python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-received-inspection.py &&
  sudo -n python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-postreceive.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-finalisation.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-fixed-receiver.py &&
  python3 -m py_compile \
    roles/btrfs-replication/files/btrfs-native-endpoint.py \
    roles/btrfs-replication/files/btrfs-agreed-parent-stream-name.py \
    roles/btrfs-replication/files/btrfs-agreed-parent-staging-storage.py &&
  git diff --check
)
if [ "$?" -eq 0 ]; then echo 'PASS: private-name runtime source regression'; else echo 'FAIL: private-name runtime source regression'; fi
```

To test actual Btrfs operations with disposable loopback images, separately
invoke the **explicit opt-in** integration test. It creates and destroys only
its own temporary image files; it does not touch mars/backup Btrfs datasets.

```bash
cd /home/richard/playbooks
(
  sudo -n python3 roles/btrfs-replication/tests/verify-0040-step12-3-private-name-real-btrfs.py --run &&
  git diff --check
)
if [ "$?" -eq 0 ]; then echo 'PASS: disposable private-name Btrfs runtime'; else echo 'FAIL: disposable private-name Btrfs runtime'; fi
```

If any real-Btrfs test fails, do not deploy the changed endpoint or enable
staged replication. Preserve the original 03:30 native timer. Do not
automatically delete any staged or published Btrfs subvolume.

## Remaining acceptance work

The disposable test proves the module-level stream rewrite and same-parent
publication on real Btrfs; it does **not** exercise the full systemd scope,
SSH sender authentication, deployed runtime paths, or automatic retry. Those
remain separate final operational acceptance requirements.
