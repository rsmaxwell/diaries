# 0040-FEAT — durable pruning-pin isolation

Status: source-only gate, **NOT deployed**, receiver deletion disabled.

The native sender's `protect_common_parent()` now calls `protect-prune-source` instead of the ordinary `protect-source` operation. The privileged endpoint persists a separate `prune_protected` mapping in the existing `.replication-protection.json` alongside the manager-consumed `protected` mapping, under its existing manager lock and durable atomic write. The ordinary `release-source` operation refuses any timestamp present in `prune_protected`, preventing an ordinary `--latest` replication from unpinning the parent reserved for pruning.

No pruning-pin release operation is introduced. Such pins remain in place for explicitly reviewed reconciliation. The new endpoint role is **not** added to sudoers in this package and is **not** installed on either host, so do not execute `--prune-preflight` on production until coordinated deployment and sudoers review. The existing source `--latest` path is unchanged. Production receiver pruning is still disabled.

Offline regression: four tests pass (pin persists and normal release fails closed, ordinary transfer pin is releasable, sender requests stronger pin, receiver deletion remains blocked). Python compilation passes. This does not prove cross-host deletion, concurrent-replication safety, or real Btrfs mutation. Those remain acceptance gates.

Check the files in Beyond Compare and run the feature regression against `mango` before deployment. The prior accepted `backup` inventory remains 19 verified, with no deletion candidates; no need to manufacture a production candidate.
