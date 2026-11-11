# 0045-FEAT — Step 1 ACL collector correction (11 November 2026)

**State:** Collector correction prepared; original installed baseline **not yet accepted**.

## Evidence and observed failure

The Windows Diaries planning commit `47c96ba` was successfully published to `origin/main`. The first Step 1 baseline capture reached `mars` after collecting Windows Git and `mango` source/inventory topology, then failed:

```
=== Capture mars static installed manifest ===
FAIL: 0045 managed-host fingerprint: Metadata command failed: getfacl
FAIL: 0045 baseline capture
```

The error comes from an operating-system exception while launching or waiting for `getfacl`, not from a detected ACL difference. The log cannot distinguish a missing binary from a timeout. No installation changes were made. The timestamped initial evidence directory is **partial** and must not be accepted as the Step 1 baseline.

## Correction

`tools/collect-0045-host-state.py` now reads POSIX ACL metadata directly through Python's `os.getxattr` on the **specific configured backup directory only**, using `system.posix_acl_access` and `system.posix_acl_default`. The SHA-256 of each present ACL xattr is captured, together with uid, gid and mode. A normally absent extended ACL is represented explicitly; other failures stop the capture rather than being mistaken for absence. Neither ACL bytes nor secret values are emitted. The tool requires no installation of `acl` or other packages on managed hosts.

This preserves the original installation and makes ACL comparison reproducible. Future Step 3 comparisons must use this same collector revision on both sides; retain the accepted initial baseline unchanged after approval.

## Verification and next action

The updated script is syntax checked and has passed isolated tests for absent, present and unreadable ACL xattrs. Apply this patch in the authoritative Windows Diaries repository, rerun the existing read-only Step 1 collector, and review both host manifests and remaining source-to-install destination coverage. Do not close Step 1 simply because the collector returns `PASS`.
