# Supplemental status extension — stale-qgroup visibility

Date: 2026-10-20

Status: **SOURCE IMPLEMENTED / SOURCE REGRESSION PASS / MARS DEPLOYMENT PENDING**.

## Change

Extend the existing read-only `btrfs-snapshot-manager status` command, using
`btrfs qgroup show <configured snapshot root>` with an 8-second timeout.

Expected healthy output:

```text
qgroups_total=145
qgroups_stale=0
qgroups_under_deletion=0
qgroups_status=ok
```

A warning is reported if stale > 100 or any under-deletion entries exist.
On timeout, missing Btrfs binary, command failure or malformed output,
`qgroups_status=unavailable;reason=...` is printed without turning the
existing status command into a failure.

The count is informational, **not an automatic deletion or cleanup**.
There are no quota changes, scheduled tasks, configuration migrations or additional
legacy snapshot deletions.

## Regression evidence

- `python3 -m py_compile` of the manager: PASS
- New `roles/snapshots/tests/verify-qgroup-status.py`: seven mock scenarios PASS
- Existing `roles/snapshots/tests/verify-btrfs-snapshot-manager.py`: PASS
- Live mars output, checksum and deployment: **pending**

## Known limitation

Query reports counters, not a diagnosis of the original Snapper used-space delay.
The old inventory timed out at 60s after cleanup; the `--disable-used-space`
workaround remains necessary.
