# 0049 — Rollback readiness and accepted operational state (16 November 2026)

**Readiness documented, NOT a live rollback exercise.** Real 0049 replication and the post-transfer parent/UUID read-backs were accepted; no destructive rollback, prune, rebootstrap or restoration is justified solely for this presentation/naming feature.

## Accepted installed state

| Endpoint | Operational identity | Installed scheduling | Accepted record |
| --- | --- | --- | --- |
| `mars` | `btrfs-push.service` executes under `btrfs-send` through the 0041 root-owned wrapper | `btrfs-push.timer` active; next normal schedule 03:30 UTC | Agreed parent `20261116-150008Z`, prior `20261116-030016Z` |
| `backup` | Restricted `btrfs-receive` SSH transport, receiver-owned guarded prune | `btrfs-receiver-prune.timer` active; next normal schedule 04:15 UTC | Same parent/prior, new snapshot `Received UUID=818b8956-76de-564f-8351-37cc89037d14`, read-only |

At final read-back the receiver had 41 retained snapshot sets, 2 independent checkpoint holds, 27 historical receipts and 0 proposed prune deletions. Both hosts had `changed=0` on final Ansible reapply. These are dated observations, not permanent assumed counts.

## Controlled rollback if future operations require it

1. Identify exact committed Playbooks implementation and pre-0049 baseline revisions; verify the selected rollback commit is post-0041 and retains dedicated service identities. Do not use a blind `git reset --hard` on a dirty checkout.
2. Disable the current `btrfs-push.timer` and `btrfs-receiver-prune.timer` before restoring their former units. Confirm both old and new *services* are inactive. Never enable two timers targeting the same replication/prune operation.
3. Restore a complete, matching Ansible-managed runtime/unit/wrapper set on **both** endpoints from the verified baseline. Re-enable the historical timer names only once unit definitions and 0041 restricted SSH/forced-command/sudoers are verified.
4. Preserve snapshot datasets, retention policy/caps, checkpoint holds, historical receipts and `.simple-agreed-parent.json` state files **unchanged**. These internal filenames are deliberately not migrated by 0049. Never rebootstrap the parent as a name-only rollback.
5. Confirm source/receiver agreed-parent identity, timer exclusivity and output/exit states via read-only checks. Capture an operator-reviewed rollback record in this feature, if ever exercised. No on-host rollback was needed during accepted deployment.

**Important:** The original 0049 feature ZIP and `0904bc7...` baseline are useful references, but actual rollback commands must be validated against the committed Playbooks tree and current deployed identity/lock state before execution. No rollback is claimed as tested on live hosts.
