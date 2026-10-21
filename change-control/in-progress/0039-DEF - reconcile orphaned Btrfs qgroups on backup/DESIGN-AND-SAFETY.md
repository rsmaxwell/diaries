# Diagnostic design and safety boundaries

## Separate two problems
A. **Quota metadata hygiene:** large difference between live subvolumes and qgroup records may reflect orphaned entries; current aggregate counts alone cannot classify individual IDs.
B. **Manager reporting:** `qgroups_status=unavailable;reason=unexpected_output` is an observed symptom; the mechanism is unknown until the installed code/command's captured output is inspected. Do not declare a parser bug or assume it is purely cosmetic.

## Architecture invariants
- Source: `mars`; receiver: `backup`; off-site native Btrfs send/receive remains initiated from `mars`.
- Receiver data: `/@data/mars-received/@data`; replication receipts: `/@data/mars-received/.replication-state`.
- On `backup`, local snapshot-manager create/prune/legacy-prune timers must remain disabled/inactive.
- Preserve received read-only snapshots, Received UUID, transfer receipts and incremental parent chains.
- 0038-FEAT stays closed, with its emergency installed-file copies retained; do not repurpose them as quota-metadata rollback.

## No-go and explicit approval
No commands involving `btrfs quota enable|disable|rescan`, `btrfs qgroup destroy|clear-stale`, snapshot/subvolume deletion, quota limit updates, native replication schedule edits, mount changes, scrub/repair with mutation, or receiver reseed until Step 3 acceptance and user approval. Btrfs quota metadata changes may be nonreversible without broader data recovery. Preserve existing backup/replication operation unless the controlled maintenance design specifically requires a pause.

## Evidence handling
Use short, bounded summaries and selected sample IDs. Preserve terminal logs in `evidence/Step NN/` or named references; never add bulk qgroup dumps, credentials, or private backup data to source. Record installed versions before choosing Btrfs subcommands; `btrfs quota status` is unsupported in v5.16.2 on `backup`.

## Recurrence and platform-upgrade scope clarification (2026-10-21)
The operator confirms `mars` was previously cleaned to zero stale qgroups and has subsequently accumulated 39. Preventing or bounding recurrence is part of acceptance. `backup` is on Ubuntu 22.04 LTS, `mars` on Ubuntu 24.04 LTS. Supported distro-managed upgrades should be reviewed under a separate, explicitly approved maintenance gate. An OS upgrade is not a cure for stale qgroups by assumption; observed recurrence on newer `mars` supports independent lifecycle diagnosis. Do not reboot, upgrade or change quotas as part of read-only investigation.
