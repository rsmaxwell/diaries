# 0040-FEAT — Step 07 Ansible review, rollback and acceptance

**Decision: CLOSED — 25 October 2026.** See `../evidence/Step 07/README.md` for the evidence register.

## Scope and change approval

- Target hosts: `mars` and `backup`, playbook `native-btrfs.yaml`, Ansible controller `mango`.
- Final reviewed changes: source manager JSON reserialization and native push update on `mars`; receiver-manager update and sudoers comment-only adjustment on `backup`.
- Explicit operator exception: keep `richard ALL=(root) NOPASSWD: /usr/local/libexec/btrfs-native-endpoint --role delete-receiver --snapshot *` on `backup`. The initial proposed removal was **not** accepted; the corrected diff preserved it.
- Receiver remains in `mode=receiver`, `receiver_prune_enabled=false`. `mars` remains on paired snapshot creation, not the proposed `@data`-only scheme.

## Evidence and rollback

Rollback directories:

- `mars`: `/home/richard/rollback/0040-step07-20261025-073634Z/`
- `backup`: `/home/richard/rollback/0040-step07-20261025-073636Z/`

Original relative paths are preserved by `cp -a --parents`. There has been no rollback test or restoration; no rollback copies were pushed off host.

Syntax and final check/diff passed, then controlled installation was performed ahead of the original Step 8 schedule. Its repeated check/diff reported `changed=0` on both hosts. Runtime checks returned `CLEAN` receiver recovery, valid Diaries verification and intact sudoers parsing.

Accepted Playbooks commit: `a8f857c` (parent `b51a5b0`).

## Boundaries

Step 7 closure approves the reviewed diff and preserved rollback options, **not** migration to `@data`-only creation, receiver deletion, legacy retirement or change to scheduled replication. Work performed early that belongs under Step 8 must be reconciled to Step 8's acceptance criteria rather than assumed complete.

Separate maintenance observation: 234 stale qgroups on `mars`; not attributed to Step 7.
