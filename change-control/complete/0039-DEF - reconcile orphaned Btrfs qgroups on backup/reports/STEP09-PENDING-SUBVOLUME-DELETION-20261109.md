# 0039-DEF — Step 9: stale qgroups and pending subvolume deletion (9 November 2026)

**Status:** Diagnosis accepted as an exact live ID correlation. Proposed
shared-code improvement tested offline only. Step 9 and the defect remain
**OPEN**; the update in this package has **not** yet been deployed or tested
on production hosts. No Ubuntu upgrade is part of 0039-DEF.

## Grounded operations and findings

The following observations come from user-run terminal logs on 9 November
2026, not from an assistant-executed production command. Preserve the
original logs in this feature's evidence records if they are not already
present in the Windows Diaries repository.

| Evidence | Observation |
| --- | --- |
| `note(20261109-135244).txt` | Initial mars baseline: 656 stale qgroups; backup 0; Btrfs v6.6.3 on both hosts |
| `note(20261109-142530).txt` | `backup` native service succeeded with zero stale; `mars` native `clear-stale` returned `Device or resource busy` |
| `note(20261109-142857).txt` | `mars` partial cleanup: 656 → 62 stale; 62 nonzero; timer disabled |
| `note(20261109-153205).txt` | No parent/child qgroup relationships for stale entries |
| `note(20261109-201045).txt` | Completed quota rescan, but remaining nonzero stale accounting persisted |
| `note(20261109-201356).txt` | 43 queued deleted subvolumes, 44 nonzero stale and 56 zero stale; deletion processing underway |
| `note(20261109-205245).txt` | `btrfs subvolume sync` timed out (rc 124) after 20 minutes; pending 43 → 38; nonzero stale 44 → 38; snapshot sets still complete |
| `note(20261109-224524).txt` | **11 pending subvolume IDs = exact set of 11 nonzero stale qgroup IDs**; 91 zero stale; 102 total stale; 70 complete snapshot sets, 0 incomplete; production Diaries verification valid; `mars` timer inactive/disabled |

The final ID-set intersection shows:

```text
pending_deletions=11
stale_zero=91
stale_nonzero=11
pending_and_nonzero=11
nonzero_not_pending=[]
pending_not_nonzero=[]
```

**Interpretation:** The pending kernel deletion queue explains the blocked
nonzero stale qgroups on `mars` at the observation point. This is strong
correlation, not proof that all future EBUSY errors have the same cause or
that pending deletions will always drain automatically. It does not justify
deleting snapshots, disabling quota accounting, repeating expensive rescans,
or changing the OS.

## Proposed common-code correction

Apply the separate 0039-DEF Playbooks package to `/home/richard/playbooks`
on `mango` after reviewing the current working-tree diff. The same executable
must remain deployed on `mars` and `backup`; each host retains its own
Ansible-rendered `/etc/btrfs-stale-qgroups.json` and systemd timer state.

- Read pending-deletion IDs using `btrfs subvolume list -d` under existing
  manager → writer locks. Never wait indefinitely for deletions.
- Permit the **single native** `btrfs qgroup clear-stale` to clear eligible
  entries, even if pending deletions make the native command return EBUSY.
- Treat an EBUSY result as an expected **deferred** outcome only when all
  reported busy IDs belong to the kernel's pending-deletion queue, all
  residual stale IDs are pending after the command, and the non-stale
  qgroup inventory is preserved.
- Log `result=deferred_pending` with the count; do **not** report
  `stale_after=0` unless that is observed. An unexpected error or unmatched
  residual must fail closed.
- Keep the shared 2,000-stale ceiling, strict configuration/mount checks,
  lock order and dry-run semantics. Do not add automatic quota rescans,
  snapshot deletion or subvolume sync waits.

## Regression and acceptance

Offline verification (in preparation environment): **22 automated tests
passed**, including pending-subvolume parser, exact EBUSY classification,
expected partial completion (102 stale = 91 eligible + 11 pending), and
fail-closed cases. This does **not** verify installation or live execution.

**Next consolidated acceptance action** on `mango`:

1. Apply the Playbooks source update using Beyond Compare, inspect Git
   changes and run `python3 roles/snapshots/tests/verify-btrfs-clear-stale-qgroups.py`.
2. Preview the Ansible change separately for each host. Keep `backup` timer
   **enabled** and `mars` timer **disabled** until the installed dry-run and
   explicit first live invocation are reviewed.
3. Deploy both host copies with their host-specific JSON files, perform
   dry-runs and a controlled `mars` service execution; review journal's
   `result`, `removed`, `deferred_pending`, and poststate. Never infer
   zero residual stale from `systemctl` success alone.
4. Verify complete snapshot sets, the agreed replication parent and
   incremental replication state using existing 0040 evidence or limited
   current diagnostics; do not repeat an accepted full restore.
5. Enable `mars` timer following acceptance and observe successive normal
   snapshot/prune/replication cycles. The deferred queue must drain rather
   than accumulate indefinitely before closing 0039-DEF.

**Rollback:** Disable the `mars` timer and restore the previous Playbooks
shared script and service deployment if errors appear. Keep the already
running `backup` timer functional; avoid reversing legitimate Btrfs qgroup
metadata changes or touching snapshot data.
