# 0040-FEAT Step 12 — Authorisation of unattended receiver pruning

Date: 7 November 2026 (UTC)
Status: **AUTHORISED; deployment and first scheduled execution not yet evidenced**

## Explicit operator authorisation

The operator explicitly stated:

> I authorise "enabling unattended receiver pruning on `backup` at 04:15 UTC, with a maximum of ten snapshot deletions per run, using the existing retention policy"

The approval is confined to the already implemented and independently verified simplified receiver-retention mechanism. It does **not** approve changing retention buckets, bypassing the shared Btrfs snapshot-manager safety checks, deleting checkpoint holds or agreed parents, removing legacy forensic receipt records, or running legacy receiver pruning.

## Prior accepted evidence

- Simplified replication first unattended run: 7 November 2026 03:30 UTC, successful; source and receiver agreed-parent state matched at `20261107-030031Z` (previous `20261106-160001Z`).
- Corrected shared manager SHA-256: `26ba24e711558a358069775ef042c01765355dd5dc80f9eb5521f42a2673dfc0`, installed and verified on `backup`.
- Disposable real-Btrfs test verified deletion of eligible receipt-backed snapshots, receipt preservation, two agreed-parent pins, checkpoint holds and repeat-run idempotence.
- Most recent live read-only plan: `keep=30`, `candidates=0`, `historical_receipts_preserved=27`, two checkpoint holds. Pruning and timer were disabled/inactive at that time.

## Authorised durable settings for backup

```yaml
btrfs_simplified_receiver_retention_install_enabled: true
btrfs_simplified_receiver_prune_enabled: true
btrfs_simplified_receiver_prune_on_calendar: "*-*-* 04:15:00 UTC"
btrfs_simplified_receiver_prune_max_delete: 10
```

Deploy using `/home/richard/playbooks/btrfs-replication.yaml` on `mango` (default inventory `/etc/ansible`, Vault password file `~/.vault_pass.txt`), tag `simplified-receiver-retention`, limit `backup`. Do not invoke `receiver-simple-prune` manually to perform an extra production deletion.

## Pending acceptance evidence

1. Effective Ansible inventory reflects the authorised settings; playbook preview shows only expected changes.
2. Playbook completes successfully; live `backup` JSON configuration reflects `receiver_prune_enabled=true`.
3. `btrfs-receiver-simple-prune.timer` is enabled and active, its calendar is 04:15 UTC, and the service has `--max-delete 10`.
4. Live `receiver-simple-plan` executes successfully with the authorised gate, and agreed-parent/hold protections remain intact.
5. First unattended timer execution result and actual deletion count (including a zero-deletion success), with post-run read-only state verification, are preserved in Step 12 evidence.

Retain Step 12 **OPEN** until the activation and subsequent scheduled-operation evidence is accepted. Evidence belongs under `0040-FEAT/evidence/Step 12/` in the authoritative Windows Diaries repository; any execution logs initially captured in `/home/richard/diaries` on mango must be synchronised back rather than treated as the permanent master record.
