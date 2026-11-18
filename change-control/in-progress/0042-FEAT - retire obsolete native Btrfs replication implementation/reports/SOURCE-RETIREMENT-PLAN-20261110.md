# 0042 source retirement — static inspection report

**Date:** 10 November 2026. **Status:** Prepared offline; not executed on mango or production hosts.

User-supplied live-state evidence confirms that on 10 November the `mars` systemd `ExecStart` was `/usr/local/bin/btrfs-simplified-replication sender cycle`, the `03:30` sender timer was enabled/active, and sender/receiver agreed-parent identities matched (`20261110-030004Z`, `relation=equal`, `receiver_parent_verified=true`). The receiver simple-prune timer was enabled/active.

The latest 9 November Playbooks source bundle still contained both fallback legacy source/receiver installers and dormant staged-protocol implementation plus a duplicate unreferenced `roles/remote-backup` role. The prepared Playbooks updates remove those branches and the old fallback while retaining the original systemd unit names, simplified runtime, shared manager, retention policy, parent/checkpoint files and imported 0039 qgroup maintenance.

The source deletion manifest contains **215** exact candidate files from the supplied 9 November Playbooks bundle. Each records a SHA-256 hash. The guarded one-off script must refuse any change made after this bundle; changes require manual reconciliation. Historical acceptance evidence is retained in the completed 0040 Diaries feature and in Git history, with a new exact rollback tar prepared from *actual mango bytes* before removal. The archive is not yet created.

Offline successful checks: the simplified runtime regression (25 tests), simplified protection (3 tests), simplified cutover-readiness (5 tests), shared-retention source check and replacement legacy source contract. Consolidated suite and live Ansible preview/deploy still pending at time of preparation.
