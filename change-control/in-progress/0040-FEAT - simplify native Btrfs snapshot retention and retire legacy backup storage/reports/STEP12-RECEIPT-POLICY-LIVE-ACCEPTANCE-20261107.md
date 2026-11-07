# Step 12 — Historical-receipt retention policy live installation acceptance (7 November 2026)

**Decision:** ACCEPTED — corrected receiver retention manager installed and verified in read-only mode. **Step 12 remains OPEN.** Live destructive pruning and unattended timer activation remain **NOT AUTHORISED**.

## Scope

This acceptance records the 7 November 2026 installation of the updated shared Btrfs snapshot manager on the production receiver `backup`, following accepted source regressions and the disposable real-Btrfs receipt-backed snapshot deletion test. This is a narrow acceptance for installation, configuration parity, and the live read-only plan; it does not approve any production deletion.

## Captured evidence

- Source file: `roles/snapshots/files/btrfs-snapshot-manager.py`, checksum `26ba24e711558a358069775ef042c01765355dd5dc80f9eb5521f42a2673dfc0` — verified before installation.
- Ansible inventory for `backup`: `btrfs_simplified_receiver_retention_install_enabled=true`; `btrfs_simplified_receiver_prune_enabled=false` — verified.
- Installation: `ansible-playbook btrfs-replication.yaml --limit backup --tags simplified-receiver-retention --vault-password-file ~/.vault_pass.txt`, recap `backup: ok=6 changed=1 unreachable=0 failed=0 skipped=0`.
- Installed `/usr/local/sbin/btrfs-snapshot-manager` SHA-256 matched the accepted source.
- Deletion gate: `/etc/btrfs-snapshot-manager.json` has `mode=receiver` and `receiver_prune_enabled=false`.
- Timer: `btrfs-receiver-simple-prune.timer` showed `ActiveState=inactive`, `UnitFileState=disabled`.
- Read-only plan: `receiver-simple-plan` succeeded; `keep=30`, `candidates=0`, `historical_receipts_preserved=27`, `historical_receipts_on_candidates=0`, `historical_receipts_orphaned=0`, `enabled=false`.
- Agreed parents: current `20261107-030031Z` (`7778dda5-2b91-8c4e-8b1a-1dd038a3675b`); prior `20261106-160001Z` (`e28d1139-a311-944c-a048-b60874a4dd02`).
- Checkpoint holds retained: `20261013-171228Z`, `20261018-165453Z`.

The captured terminal transcript accompanies this report. The original `mango` machine-generated evidence path is `evidence/Step 12/raw-logs/step12-receipt-policy-install-20261107-111204.txt` in `/home/richard/diaries`; that original log must also be synchronised to the authoritative Windows Diaries repository when collecting evidence.

## Interpretation

The historical receipts remain present as forensic evidence but no longer act as permanent retention pins. All 30 currently received snapshots are retained by the existing bucket-based policy and independent holds/parent pins; therefore there is no production deletion candidate today. The shared `retention_keep_set` policy counts *occupied* hourly/daily/weekly/monthly/yearly buckets, not simply an elapsed time window. With sparse daily receiver snapshots, 48 hourly occupied buckets can span considerably more than 48 elapsed hours; this is existing policy behaviour, not a new change in this installation.

## Outstanding gates

1. **Explicit operational approval** is required before changing `btrfs_simplified_receiver_prune_enabled` to `true`, because unattended execution would eventually delete future eligible off-site snapshots.
2. Before that change, inspect `backup`'s live read-only plan again, verify parent and hold state and `mars` scheduled replication, and preview the exact `backup` Ansible configuration change. Keep the `04:15 UTC` receiver-prune timer offset from the `03:30 UTC` sender schedule.
3. After any approved activation, verify installed config, enabled/active timer, service exit status and subsequent read-only plan, and preserve rollback directions: set the inventory variable back to `false` and reapply `--tags simplified-receiver-retention` on `backup`.
4. Reconcile current uncommitted Playbooks work and acceptance raw logs into the authoritative Windows Diaries change-control feature directory before formally closing Step 12. Steps 13–14 remain separate.

**No production deletion or enabling of receiver pruning was performed or inferred from this report.**
