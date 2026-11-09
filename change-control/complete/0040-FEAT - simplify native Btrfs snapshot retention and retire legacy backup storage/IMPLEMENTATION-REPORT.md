# 0040-FEAT — Receiver directory-root preflight correction

The live `backup` check confirmed that `/@data/mars-received` is an ordinary directory on the Btrfs filesystem. Previously, the common manager unconditionally required it to be a subvolume. The fix keeps `require_btrfs()` in both modes, applies `require_subvolume()` only to source mode, and rejects missing/symlink roots. The existing snapshot-collection filesystem UUID equality check is unchanged.

No replication configuration or receiver deletion activation changes. The correction must be checked on `mango`, deployed with the already accepted receiver-manager Ansible tag, and verified with `receiver-inventory`, `receiver-plan`, and Ansible idempotency. Neither ZIP changes production on its own.

Local regression: Python compilation and receiver/source/symlink/cross-filesystem cases passed. File-based mocks do not substitute for live verification.
