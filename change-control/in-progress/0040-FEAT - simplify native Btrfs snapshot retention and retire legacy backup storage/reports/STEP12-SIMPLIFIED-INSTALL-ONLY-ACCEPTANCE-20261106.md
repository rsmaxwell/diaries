# 0040-FEAT — Step 12 simplified replication install-only acceptance

**Date:** 2026-11-06 (UTC)  
**Decision:** **ACCEPTED — installation-only deployment and readback.** Step 12 and 0040-FEAT remain **OPEN**.

## Scope and results

The accepted source-level tests (18/18) and disposable real-Btrfs interruption/recovery integration preceded this deployment. Following a clean check-mode preview on both hosts, the operator ran the Playbooks native replication role with:

```text
--limit 'mars,backup'
--vault-password-file ~/.vault_pass.txt
-e '{"btrfs_native_push_schedule_enabled":true,"btrfs_simplified_replication_install_enabled":true,"btrfs_simplified_replication_active_enabled":false}'
```

Play recap: `mars`: ok=20, changed=2, failed=0, unreachable=0; `backup`: ok=36, changed=2, failed=0, unreachable=0. The updates installed `/usr/local/bin/btrfs-simplified-replication` and `/usr/local/sbin/btrfs-snapshot-manager` on each endpoint. The existing privileged native endpoint and source service were unchanged.

Installed file hashes **match on both hosts**:

| Installed file | SHA-256 |
|---|---|
| `/usr/local/bin/btrfs-simplified-replication` | `9be64295a6b6807df0fcd33d924b7a6549959f2a03dcab2953dcf0ac77fa6297` |
| `/usr/local/sbin/btrfs-snapshot-manager` | `07ca520d38c071b204adfe024151cb6f7a3861c27c64f643a82825bb8fb0691d` |

On `mars`, `btrfs-native-push.service` still had `User=richard` and `ExecStart=/usr/local/bin/btrfs-native-push --latest`. The active timer still specified **03:30:00 UTC**, and its next scheduled event at the time of inspection was 2026-11-07 03:30 UTC. On `backup`, the receiver snapshot-manager configuration asserted `receiver_prune_enabled` was `false`.

The preserved historical receiver checkpoint validation for **20261013-171228Z** and **20261018-165453Z** passed in the deployment run. No simplified parent bootstrap, replacement transfer, live switch, receiver prune, or snapshot deletion was performed by this acceptance.

## Repository provenance

The deployment transcript records `/home/richard/playbooks` on branch `main`, revision `bdba058b0f3b634f94e7da4b7ab62eeadfa625b6`, with local source modifications and untracked files at execution time. A later operator log shows that this repository was clean on `main` at commit `813b7210d08865337770ae821bb9d88529115188`, tracking `origin/main`. The later commit is **not** substituted retroactively for the deployment revision; installed SHA-256 hashes are the reliable binary readback.

The operator also confirmed the Windows Diaries checkout was clean at `471829f1a71eab16dcbe4601eae6d49282234c99` after committing the earlier change-control documents. At that inspection, the `mango` Diaries clone remained at `662179aa24f5ded77d54ead283589ed0ad860f16`; synchronise it with a fast-forward pull before further repository-based feature tooling.

## Source evidence

Raw operator-provided logs are preserved verbatim alongside this report:

- `note(20261106-104959).txt` — installation play and recap, including source revision and deployed tasks.
- `note(20261106-105013).txt` — `mars` installed files, hashes, service and timer readback.
- `note(20261106-105049).txt` — `backup` installed files, hashes and receiver-prune disabled assertion.
- `note(20261106-105441).txt` — later Playbooks/Diaries Git status, commits, and Windows push.

## Outstanding operational gates (not yet accepted)

1. Inspect existing original and simplified parent-state records, currently shared Btrfs snapshots and identity relationships **read-only** on `mars` and `backup`.
2. Verify the exact configured `mars` → `backup` SSH/sudo path, the endpoint filesystem identities and any live legacy transaction markers before touching new state.
3. Select and verify a common initial snapshot; bootstrap simplified state only after proving the same source UUID on both hosts and preserving the old operator state/holds.
4. Perform one controlled live sender cycle with identity/state readback and practical rollback; then deliberately opt in to the existing 03:30 service replacement while retaining its timer and old binary.
5. Retain `receiver_prune_enabled=false` until its independent acceptance criteria are met. Never infer the receiver-prune gate from this installation acceptance.

**Decision boundary:** The install-only stage is CLOSED/ACCEPTED. The operational cutover and overall Step 12 remain OPEN.
