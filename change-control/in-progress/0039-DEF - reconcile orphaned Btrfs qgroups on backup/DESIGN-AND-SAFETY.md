# 0039-DEF — Design and safety boundaries

**Current contract (accepted 10 November 2026):** Shared, guarded Btrfs stale-qgroup maintenance is installed on `mars` and `backup`, and both 05:30 UTC timers are enabled and active. Steps 8–10 are CLOSED on observed evidence. Step 11 still requires an additional unattended cycle; Step 12 formal defect closure remains OPEN. Ubuntu upgrades are out of scope. The 22 October historical receiver remediation remains accepted.

## Distinguish the problems

1. **Reporting/parsing:** The previous `qgroups_status=unavailable;reason=unexpected_output` issue involved version-sensitive `Qgroupid` output parsing and was corrected (Step 2 CLOSED).
2. **Orphaned/unmatched qgroups:** The 22 October guarded `backup` deletion removed 29,437 unmatched level-0 qgroups, with a subsequent successful incremental receive (Steps 3–7 CLOSED). This was **point-in-time remediation**, not a recurring cleanup solution.
3. **Recurring `<stale>` entries:** Previously cleaned `mars` accumulated new stale qgroups; 0040-FEAT's 9 November audit reported 606. Do not equate `<stale>` markers, unmatched IDs, zero-usage qgroups and transient pending deletions without independent checks. Capability and output may vary by installed Btrfs userspace version.

## Architecture that must remain intact

- `mars` is the sender; `backup` is the off-site receiver. Send/receive is initiated from `mars`; sender and receiver maintain a protected, agreed incremental parent and checkpoint holds.
- Receiver dataset: `/@data/mars-received/@data`; protected receiver replication-state/receipts live under `/@data/mars-received/.replication-state`.
- Keep existing **source** create/prune and **receiver** prune schedules and distinct roles intact. A receiver-mode prune timer exists under 0040-FEAT; do **not** re-enable source-mode create/prune timers on `backup` or presume all receiver prune timers should be disabled (that was a historical constraint superseded by the accepted 0040 design).
- Preserve snapshot/subvolume identities, readonly state, received UUIDs, held parents, retention checkpoints, receipts and lock semantics. Cleanup must not issue snapshot/subvolume deletions, reset quota accounting or rewrite replication state.
- Reuse 0038-FEAT evidence and 0040-FEAT current code contracts; emergency installed-file copies are not quota-metadata rollback backups.

## Shared automatic housekeeping design requirements

- **One common implementation** (one maintained source file and shared service/timer templates) must be installed on `mars` and `backup`. Host configuration can differ for Btrfs filesystem (`/media/usb` vs `/` in the known source layouts), lock files, timer schedule and capability; the 9 November baselines and deployed dry runs verified `/media/usb` on `mars` and `/` on `backup`.
- The original `roles/snapshots/files/btrfs-clear-stale-qgroups.py` had a fixed receiver filesystem and writer lock and was installed from the generic snapshots role, which refuses `remote_backup`. The deployed implementation **replaced that source file** and installs it from `btrfs-replication.yaml` on both endpoints, with a separately rendered `/etc/btrfs-stale-qgroups.json` on each host (mode, mounted filesystem, expected writer lock and limits), cross-checked against the installed snapshot-manager configuration. The old snapshots-role installer was removed, avoiding duplicate cleaners.
- Acquire established operation locks in a consistent order before collecting final deletion candidates or modifying quota metadata; use nonblocking failure/deferral under contention. Where a mandatory lock/capability is unavailable, fail closed, log it and do not mutate.
- Confirm filesystem identity, manager/writer locks, live subvolume IDs and qgroup paths; use only the supported native `btrfs qgroup clear-stale`. The installed code refuses unmarked orphan qgroups, an unexpected live-subvolume/`<stale>` collision, simple-quota placeholders, missing/unsupported command and any batch exceeding 2,000 stale qgroups. `<under deletion>` is not a cleanup candidate. Never infer safe deletion solely from count differences or broad regular expressions. If host capabilities cannot provide a safe operation, stop and record the limitation for Step 11; do not silently fall back to unsafe mass `qgroup destroy`.
- Default executable invocation remains read-only. Mutating mode is explicitly gated by the managed service, scheduled and enabled only after approved deployment. Keep logs bounded and diagnostically useful; use meaningful success/deferral/failure states, suitable systemd service failure behaviour and idempotence.
- Avoid scheduling predictable overlaps with source prune, receiver prune and replication, while retaining lock enforcement for unplanned overlap. Do not modify unrelated retention or replication scheduling in this defect.


## Observed deferred-deletion behaviour (9–10 November 2026)

A native `clear-stale` invocation on `mars` removed 594 of 656 stale qgroups but returned `Device or resource busy` for some with nonzero accounting. A quota rescan alone did not resolve that cohort. Btrfs had subvolume deletions pending; a later exact-ID comparison showed **11 pending deleted subvolumes and exactly the same 11 nonzero stale IDs**, with empty set differences. As those deletions completed asynchronously, the nonzero cohort decreased.

The shared cleaner was extended to classify an exact pending-ID match as `deferred_pending`, rather than conflating normal background work with an unbounded failure. The accepted 9 November controlled run removed 95 eligible entries, deferred 8 pending IDs and preserved snapshot counts. The first unattended 10 November 05:30 run completely cleared the then-current 14 entries on `mars`; the receiver had none. **A two-day recurrence trend is still required before closing Step 11**; transient new entries after 05:30 are expected and require next-cycle observation.

## Mutation approval and rollback boundary

The original 21 October **no-go** for `btrfs qgroup destroy|clear-stale`, quota resets/rescans, subvolume deletion, replication schedule changes, receiver reseed and other mutating commands was lifted **only** for the specifically approved 22 October `backup` cleanup. It does not confer indefinite authority for new metadata changes.

The 9 November scope agreement authorised **designing and implementing automatic cleanup**, not enabling an unverified timer by itself. Step 10 was subsequently executed with source/tests, Ansible check/diff, filesystem/version checks, dry runs, live controlled cleanup and operator-initiated timer activation; its first unattended run passed on 10 November. Rollback can stop/disable the timers and revert code/configuration, but **cannot be assumed to reverse Btrfs quota metadata**. No broad quota reset or filesystem mutation is implicit.

## Evidence and acceptance discipline

- Keep command outputs, source/diff, installed state, timer and journal logs, rollback instructions and verification in this feature's `evidence/Step 08/` through `evidence/Step 12/` under the Diaries **parent** repo. One-off scripts and tests belong under this feature's `tools/` and `tests/`; lasting operational code belongs in Playbooks.
- Capture host, branch/commit and uncommitted changes for the Windows Diaries and `mango` Playbooks repositories before any change. Windows and mango are not assumed synchronised. Use the latest uploaded source bundle for review while validating live state at deployment.
- Acceptance must show correctly classified and safely reconciled qgroups, no indefinite accumulation over normal prune/receive cycles, clear failure/deferral reporting, and no regression in agreed parents, retained snapshots or incremental replication. Reuse existing accepted October correctness evidence; do not repeat a full restore or the bulk deletion without a new need.
- Keep bounded counts and selected sample IDs, not bulk qgroup dumps, credentials or private backup contents. Both hosts were observed on 9 November with btrfs-progs v6.6.3 and native `qgroup clear-stale` supported; do not infer capability on any newly rebuilt host without checking.

## Historical decisions retained for context

The 21–22 October read-only, candidate-validation, disposable-test, guarded batch journal and receiver-restore safeguards are documented in Steps 1–7 and their existing evidence. The October interrupted batch journal remains **FAIL**, with a separate successful reconciliation acknowledgement. The earlier proposed `evidence/STEP08-FINAL-CLOSEOUT.md` is historical; defect closure now requires completing recurrence Steps 8–11 and formal Step 12. The Ubuntu upgrade of `backup` or `mars` belongs to separate platform maintenance and is **not** a step of 0039-DEF.
