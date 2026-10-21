# Step 03 — Guarded qgroup reconciliation and recurrence design

**Status: DESIGN DRAFT ONLY — no filesystem mutation or OS upgrade authorised.** Prepared following the Step 02 exact-ID native and legacy deletion correlations on `mars`. Primary remediation target remains `backup`.

## Safety invariants

- `mars` initiates off-site sends; `backup` holds irreplaceable received snapshots, read-only ancestry, received UUIDs, replication receipts, protection and retention metadata. Preserve all intact.
- Inventory and candidate selection must use the actual filesystem and installed Btrfs utility outputs. `0/<id>` with zero usage alone is **not** a deletion predicate. Never select higher-level qgroups, live-subvolume IDs, active parent/child relations, under-deletion IDs, or ambiguous records.
- No unbounded `btrfs qgroup destroy`, `clear-stale`, `quota rescan`, quota disable/enable, forced pruning or mass deletion. No automatic cleanup on deployment.
- Continue unattended backup only while its normal health invariants hold; no independent pausing of replication or schedule changes without an approved gate.

## Candidate algorithm — for a future separate review

1. Produce a bounded, read-only snapshot of filesystem identity, `btrfs subvolume list` IDs including root ID 5, quota state, qgroup records (`-pcre` where supported), parent/child linkage, pending deletion state and rescan state. Preserve command provenance, versions, time and parser errors.
2. Partition level-0 qgroups into **live**, **pending deletion**, **related**, **unmatched-with-limit**, and **unmatched-without-limit**. Reject ambiguous or unexpectedly changing inventories. Distinguish `mars` explicit `<stale>` markers from `backup` zero-use unmatched candidates.
3. Independently validate each proposed individual candidate immediately before any future mutation, including its absence from the live-subvolume list, no relations, no pending deletion and stable filesystem/mount identity. Document whether installed `btrfs-progs` supports any intended operation; do not improvise unsupported flags.
4. Prefer an operator-reviewed, bounded small pilot only after independent acceptance and recovery planning, with pre/post inventory and a stop on the first mismatch. Widen only by another approval; no background automatic batch.

## Options to assess

| Option | Potential benefit | Risk / gap | Disposition |
|---|---|---|---|
| Leave records in place, monitor | Preserves backups; no quota mutation | 29,437 unmatched candidates on `backup`; growth/resource impact unknown | Safe interim baseline, bounded monitoring recommended |
| Targeted, validated individual qgroup operations | Can potentially reduce confirmed obsolete records | Irreversible metadata change, quota limit interactions, utility/version semantics unknown | **Not approved**; require exact command support, pilot and rollback assessment |
| Quota-wide repair/rescan/disable-enable | Might change accounting globally | Affects all qgroups, very large receiver, unsafe assumptions about retained limits | **No-go without a distinct design and approval** |
| Fix reporting and recurrence instrumentation | Correct diagnostics, detect growth before scale | Does not itself eliminate stale metadata | Recommended source work, separate gate |
| Supported OS/kernel/btrfs-progs updates | Maintain supported software; possibly improved behaviour | Reboot/network/recovery risk, no proof of cure | Distinct planned maintenance, not combined with cleanup |

## Monitoring/diagnostic requirements

- `backup` status must tolerate actual installed command output/headers and large tables, have bounded runtime/output, distinguish unavailable/parse failure from healthy, and never report zero orphan candidates merely because parsing failed.
- Expose total, live-matching, unmatched candidates, explicitly stale where available, pending deletion, and bounded change since last accepted inventory. Retained max-referenced limits are significant, not deletion proof.
- `mars` should surface an actionable warning for **nonzero recurring stale** records or sustained positive delta, not silently label 43 stale as `ok` solely due to a threshold of 100. Threshold policy and compatibility tests need a separate source acceptance gate.
- Add test fixtures for real `-pcre` and standard headers, missing/variable paths, `<stale>`, unrelated relationships, version failures, timeouts and large outputs. No production write in test mode.

## Platform refresh as separate gated work

- `backup`: Ubuntu **22.04.5 LTS** / kernel **5.15.0-164** / `btrfs-progs` **5.16.2**; evaluate **22.04→24.04 LTS** with provider console, boot recovery, tested remote access, filesystem/receiver snapshot checks, package hold review and sufficient free space. Do **not** schedule or perform upgrade with qgroup cleanup.
- `mars`: Ubuntu **24.04.4 LTS** / running **6.8.0-138** with later kernel already installed / `btrfs-progs` **6.6.3**. A planned reboot into an installed supported kernel is separate from storage-accounting experiments. Evaluate future releases only once supported and operationally justified.
- Freeze pre-upgrade received UUIDs, receipt state, quota baseline and boot rollback options. Compare all after maintenance. Existing rollback copies of programs do not reverse quota metadata.

## Stop conditions / approval gates

Stop on unexpected mount/filesystem ID, quota state, rescan/deletion in progress, active relationships, candidate mismatch, inadequate space, missing remote recovery, stopped replication/failed receipts, excessive command duration or any failed invariant. **Ansible `--check --diff` is required for deployed source changes but cannot simulate Btrfs metadata repair.**

**Next read-only work:** inspect `backup` manager command/parser and exact `btrfs qgroup show` output, and establish a non-destructive candidate partition/count. Present exact proposed mutation commands and pilot controls for **separate explicit authorisation**. Do not move Step 03 to CLOSED from this draft.
