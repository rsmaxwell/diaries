# 0046 — Inventory migration and installation equivalence contract

## Binding result

For every managed host and every applicable playbook/host/tag/limit combination, old `/etc/ansible` inventory and the new **private inventory Git submodule** must produce **exactly the same installed configuration, policies and secure behaviour**, using the **same frozen installation-producing Playbooks revision** and other relevant inputs.

This replaces the previous destination of inventory within the **public** Playbooks repository. The complete site inventory and only genuinely Vault-encrypted secret material belong in the **private inventory repository**. No raw plaintext credentials, Vault password, private SSH keys or sensitive rendered outputs may be committed in any of the three repositories.

## What must remain equal

- Full managed-host and playbook targeting matrix, including all groups, limits, tags, applicable roles and CI/scheduled callers.
- Installed/static asset bytes and hashes; owner/group/mode/ACL/xattrs where managed; file presence/absence and directory permissions.
- Packages/users/groups/privileges; sudoers, SSH and network access, mounts, service/systemd units, timer/cron enablement and schedules, application settings, security policies and controller intent.
- `mars` and `backup` native Btrfs snapshot, qgroup, replication, agreed-parent protection and Diaries backup configuration; no destructive test operations.
- Every **other** managed host and applicable playbook, without representative-host substitution.
- Vault resolution and authorization, including fail-closed handling of missing or incorrect password, inaccessible private inventory, or missing submodule.

Runtime data, volatile job histories and timestamps that are not managed installation outputs may be excluded only with documented justification. No unexplained static differences are permitted.

## Diagnostic versus binding tests

Equal effective variable maps or identical precedence are useful **diagnostics**, not independent closure criteria. Differences must be accounted for and shown to have no effect on the binding installed-result, host selection or security requirements. Syntax checks, successful `--list-hosts`, safe `--check` results, role unit tests or matching only `mars`/`backup` are **not** sufficient to close the feature.

Freeze the original full Playbooks commit and use it for both source comparisons; do not accidentally use an older standalone `/home/richard/playbooks` revision versus a newer `playbooks/` submodule. The parent must pin that commit, and its submodule status must match the accepted receipt. After final cutover, the parent, public child and private child committed SHAs define the deployed source state.

## Rollback and evidence

Keep original `/etc/ansible` inventory and existing `/home/richard/playbooks` working copy available until accepted cutover, with an explicit reversal of the effective config/callers. Do not let normal Ansible silently fall back to two active inventory sources. Revert source-selection changes if proof fails. No backup dataset, snapshot, restoration, retention or replication state is to be changed solely for acceptance.

Store *sanitised* source and all-host equality receipts in the Diaries feature `evidence/Step N/` directories. The private inventory, encrypted Vault payloads, plaintext secrets and credential-bearing rendered files **must not** be copied into the publicly shared artifacts or Diaries Git evidence. Protected comparisons run inside a trusted boundary and output only PASS/FAIL and safe counts/hashes as reviewed.
