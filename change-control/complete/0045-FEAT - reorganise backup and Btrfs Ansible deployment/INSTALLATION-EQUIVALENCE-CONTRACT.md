# 0045-FEAT — Installation equivalence contract

**Principle:** Reorganisation is acceptable only if an approved run of the new Playbooks against the established hosts and inventory produces the same installed system as the approved original Playbooks. We compare **material installed state and behaviour**, not the layout or number of Ansible tasks.

## Source and effective-input freeze

Immediately before implementation (and after closure of 0039/0043), capture in `evidence/Step 1/`:

- Playbooks `main` SHA, branch, worktree state, and the tracked file/role/task list. Capture current Windows Diaries parent SHA/branch/status and submodule revisions. Do not presume `mango` Diaries mirror is synchronized with Windows.
- Effective inventory: `/etc/ansible` host/group membership, the non-secret effective variables for `mars` and `backup`, and an inventory source manifest including central `btrfs-maintenance-schedule.yaml`. Record **hashes/identifiers only** for secret material; do not write Vault plaintext, passwords, keys or credential-bearing rendered files to evidence.
- Active playbook entry points, wrappers, the `btrfs_native_endpoint_role` map (`source`/`receiver`), opt-in booleans and Ansible invocation options (`--vault-password-file ~/.vault_pass.txt` when needed, no redundant `-i`).
- Existing `mars`/`backup` installed-state evidence gathered read-only **before** any deployment changes, and a complete managed-file install manifest derived from the then-current roles.

## Required equality / invariants

| Category | Required before/after result |
|---|---|
| Executables and static content | Same installed paths and SHA-256 of managed scripts/modules, including all required source- and receiver-specific copies; same absence of retired helpers |
| Rendered templates and units | Same rendered non-secret content, owner/group/mode and units/drop-ins; for sensitive files compare restricted hashes/stat, never disclose content |
| Directories and privileges | Same managed path identities, ownership, modes, ACLs, sudoers effective policy, SSH requirements and system accounts; no new writable attack paths |
| Jobs and activation | Same cron jobs, enabled/disabled/masked unit states, timer `OnCalendar`, `Persistent`, service `ExecStart`, user, arguments, lock paths, restart/reload sequencing and active states |
| Source / receiver split | `mars` remains `source`, `backup` remains `receiver`; no generic source snapshot config on receiver; role and tag invocation result equivalent |
| Data protection | Existing snapshots, protected checkpoint holds, agreed-parent/latest states, replication receipts, Btrfs volumes, directories and active backup datasets preserved **without modification by the refactor** |
| Backup policy | Same retention buckets, age/cap controls, pruning safety, qgroup handling, writer lock and verified-Diaries gating; keep 0043 schedule/current effective values |
| Dependencies | Same required packages, Mounts/UUIDs, systemd/cron entries, users and host services; no incidental upgrade/removal |
| Validation | Same fail-closed assertions and refusal cases (missing/wrong inventory, unsafe filesystem state, unapproved activation, invalid protection state, privileged paths) |
| Runtime behaviour | No unexpected restarts, service launches, snapshot creates/prunes, manual transfers or restores resulting from refactor; natural scheduled activity remains healthy |

**Allowed source-interface exceptions only:** rename operator entry point `local-backup.yaml`/wrapper to `backup-collection.yaml`/wrapper, and retire `remote-backup.yaml`/wrapper **after** callers are reconciled. These changes must not alter the installed system or supported host/tag/option behaviour. Inventory group and role names remain unchanged unless separately justified and explicitly approved (not part of this feature).

## Comparison method

1. **Before** applying changes, save a dated managed-installation manifest for each host in `evidence/Step 1/`: target path, type, mode, owner, group, SHA-256 for managed files; capture unit metadata and effective schedules; include expected absent paths and state-directory existence/permissions. Record collection commands and exit codes. Capture effective inventory in redacted form. Do not record volatile secrets or private SSH keys.
2. Prepare a machine-comparable normalized manifest: sorted paths, types, checksums and stable unit properties. Separate **managed static configuration** from **mutable operational data** (backup content and snapshot history), which must not be hashed wholesale or frozen while regular backups run.
3. Offline verification: `ansible-playbook --syntax-check`, `--list-hosts`, `--list-tags` and relevant `--check --diff` with default `/etc/ansible`; compare rendered templates/unit text safely in an isolated staging process if needed. Existing read-only regression suites, especially the 0044 permanent `verify-replication.py`, `verify-protection.py`, `verify-shared-retention.py`, and maintained snapshot/local-backup tests must pass.
4. Apply the coherent refactor through the normal existing operations **after** reviewing the plan/diff. Capture Ansible results and the actual applied configuration. Avoid changing activation variables merely to force a test. No unapproved destructive backup or snapshot action.
5. **After** apply, collect manifests with the **same tool and normalization** and diff them. Any unexpected static-file checksum, mode, path, unit, cron, ACL, enabled-state, policy or privilege difference is **FAIL**, not an acceptable side effect. If a difference is caused by regular scheduled backup activity, separate it using service timestamps and runtime evidence rather than silently waiving it.
6. Re-run an approved apply to check practical idempotence; no unexpected managed resource change or service reload. Confirm healthy live source/receiver status, unchanged agreed-parent holds, snapshot sets and qgroup conditions with read-only commands. Retain passing 0039/0043 evidence; no repeat full restore or manual send/receive solely for this refactor.

## Safety and rollback

- Prior to any apply, capture the known-good Playbooks Git SHA and the managed installation manifest. Keep the original deployed configuration until the new layout passes offline validation.
- Rollback is reverting to the known-good Playbooks commit and reapplying normal playbooks with the **same inventory**, **without** restoring/deleting snapshot datasets. Capture rollback decision and exact changes if needed.
- **No broad `synchronize --delete`** on system `/etc`, `/usr/local`, home directories, backup datasets, retention roots, or state trees. Restrict sync to explicit program-only asset trees; use templates for rendered/secret files and scoped Ansible state controls for system services. Do not remove pre-existing files just because they are absent from a reorganised source tree.
- Preserve existing root/normal-user privilege boundaries, sudoers validation, receiver prune authority, writer and replication locks, source/receiver protection pins, systemd handler flushes before enablement, and fail-closed state assertions.

## Acceptance criteria

**Equivalence passes only if** the comparison manifests and effective inventory match for all managed installed assets and critical policies; existing automated regressions pass; controlled apply and live readback show healthy unattended operation; Git and evidence receipts are complete. Small, documented differences in **Ansible source structure** and **operator-facing filenames** are expected; **installed-state differences are not**.

Do not close 0045 based solely on source diffs, syntax checks or an Ansible `ok` summary. Conversely, do not require another full backup restore or manual replication when established correctness evidence and the new installation comparison suffice.
