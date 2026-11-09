# 0040-FEAT Step 12 — Legacy reference audit false-positive fix

Date: 8 November 2026  
Status: Source fix prepared; live retirement not yet executed

## Observed evidence

The 20261108-084011 prerequisites log confirms that Ansible removed
`/etc/sudoers.d/diaries-native-btrfs` from `mars` and found it absent on `backup`.
The deployment/accepted-state prerequisites passed. The subsequent legacy
reference scan stopped because a compiled cache
`/usr/local/bin/__pycache__/btrfs-native-pushcpython-312.pyc` contains references
to `/usr/local/bin/btrfs-native-push` and
`/usr/local/libexec/btrfs-native-endpoint`. Both referenced executables are
already included in the same exact-file retirement manifest. The cache is
not an executable entrypoint or a scheduled service.

## Corrective change

The `retire-0040-obsolete-code.py` remote reference audit no longer descends
into `__pycache__` directories. It still scans operational source scripts and configuration files,
and expands the audit to include retained `/usr/local/libexec` code that was
previously outside the scan scope. All exact-file capture,
root ownership, file modes, SHA-256, receipt, sudoers, snapshot-state and
rollback-archive requirements remain unchanged.

A new offline test executes the actual audit scanner against disposable files:
compiled bytecode containing legacy paths must not block retirement, while a
remaining operational script referencing a legacy executable must block it,
including non-retired scripts under `/usr/local/libexec`.

## Remaining gates

Run the offline regressions on `mango` and repeat the **read-only** readiness
audit against the existing 39-file sender and 35-file receiver manifest.
Review the result before authorising the separately guarded, destructive
retirement. Preserve the earlier failed log as evidence; do not rewrite it.
