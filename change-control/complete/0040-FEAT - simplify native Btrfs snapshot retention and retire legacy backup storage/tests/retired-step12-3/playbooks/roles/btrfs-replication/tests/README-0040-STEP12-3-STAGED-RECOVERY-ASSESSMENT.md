# 0040-FEAT Step 12.3 — Private-name staged recovery assessment (2026-11-05)

This package is **read-only incident classification** for previously-booted,
nonce-bound staged transfers. It does not enable destructive cleanup, sender
retransmission, publication, receipt commitment or scheduler changes.

The fixed receiver exposes `--assess-staged-recovery`, which obtains both
canonical receiver locks, reads the receiver's own state and journal, confirms
receipt absence, validates the staged journal, then fences a **previous boot**
using the journal's recorded boot ID. The new module checks the exact
`.receive-<nonce>` candidate in the canonical `@data` directory and the
journal's directory device/inode. It refuses a published candidate, symlink,
changed parent, invalid Btrfs metadata, same-boot recovery, or incompatible
witness. It classifies `private-stage-complete-awaiting-sender-proof`,
`private-stage-incomplete-manual-recovery`, or
`private-stage-absent-unresolved`, always with all authority flags false.

This deliberately does not attempt same-boot process termination detection.
Systemd unloading a transient scope is not an independent termination fence.
Nor does a nonce-derived filename alone prove a partially received Btrfs
subvolume can be safely deleted. Source-authenticated completion is still
required before recovered complete stages can be published.

## Test (SSH terminal on mango)

```
cd /home/richard/playbooks
(
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-recovery-assessment.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-fixed-receiver.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-privileged-reboot-assessment.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-scoped-reconciliation-contract.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-staged-finalisation.py &&
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-private-stream-runtime.py &&
  python3 -m py_compile \
    roles/btrfs-replication/files/btrfs-agreed-parent-staged-recovery.py \
    roles/btrfs-replication/files/btrfs-agreed-parent-receiver-entry.py &&
  git diff --check
)
if [ "$?" -eq 0 ]; then
  echo 'PASS: read-only staged recovery assessment'
else
  echo 'FAIL: read-only staged recovery assessment'
fi
```

## Operational limitation

Do not deploy this package in isolation just to invoke the new CLI. Deployment
requires ensuring the complete private-name runtime from the prior accepted
package is also installed. Step 12.3 remains OPEN; keep the existing 03:30
native replication timer unchanged. Never automatically delete a private
stage or retransmit because an assessment identifies it as incomplete.
