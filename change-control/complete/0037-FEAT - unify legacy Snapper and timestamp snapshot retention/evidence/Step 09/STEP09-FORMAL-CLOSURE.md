# Step 09 — Formal closure (2026-10-20)

**Decision: CLOSED — staged Playbooks deployment accepted, legacy deletion disabled.**

## Evidence evaluated

Source: `diaries-sources-20261020-073254.zip`, `evidence/Step 09/pre/` and `post/`, and the operator's Ansible deployment transcript of 2026-10-19. Both captures contain all 12 expected files, including populated `snapper-data.txt`, `manager-journal.txt` and `SHA256SUMS.txt`.

- **Source/deployed SHA-256:** `3eb8717fdb06410943a2e9513dfc5f3e8b6892021bac0d741b58e2524bdff671` on Playbooks `mango` source and `mars` post-deployment executable. Previous `mars` checksum: `4897b15b7a728988a9de9ef6cecbe81ce4c0f5e75340e08f6cf4d0af853dcb09`.
- **Deployment:** targeted Ansible copy of `/usr/local/sbin/btrfs-snapshot-manager`, root:root mode 0755, `backup=yes`. Reported rollback copy: `/usr/local/sbin/btrfs-snapshot-manager.243021.2026-10-19@22:34:32~` (not independently restored/tested).
- **Systemd:** before/after `unit-definitions.txt` byte-identical, neither native unit invokes `legacy-delete`. Native create and prune timers remained enabled; timer activity continued. Snapper legacy timers were not changed.
- **Native safety:** before/after status reports 57 complete paired `root,@data` sets, zero incomplete; verified Diaries marker; native prune dry-run reports two checkpoint holds (`20261013-171228Z`, `20261018-165453Z`), replication pin (`20261019-030038Z`), 57/57 retained and zero proposed native deletions.
- **Expected rotation:** pre/post `native-list.txt` differ only by addition of `20261019-210024Z` and `20261019-220016Z` and removal of `20261017-210017Z` and `20261017-220027Z`, all complete paired sets. This is consistent with routine scheduled native snapshot rotation; it is not evidence of unintended legacy pruning.
- **Snapper:** `snapper-root.txt` and `snapper-data.txt` byte-identical pre/post. Existing 25 numbered legacy `@data` snapshots unchanged. The read-only legacy plan is byte-identical: 17 KEEP, 8 WOULD-DELETE, zero deletions authorised.
- **Journal:** no error, failure, or traceback lines identified in the captured journal output. The journal capture is bounded and is not a substitute for unattended multi-day acceptance.

## Safety boundary

`legacy-delete` is installed but opt-in, and no root-owned approval file or `--execute` invocation was performed. The `backup` receiver diagnostic path limitation remains explicitly out of scope; this step neither reconfigured nor independently health-tested off-site replication. No destructive legacy operation is approved through this closure.

**Step 10 begins with exact per-ID operator review.** Any Step 11 live pilot requires a separate explicit approval after a fresh plan and protections check.
