# 0045-FEAT — Source review (planning evidence)

**Date:** 10 November 2026  
**Reviewed:** uploaded `playbook-sources-20261109-122355.zip`, specifically `playbooks/roles/ledger/tasks/`, `roles/local-backup/`, `roles/snapshots/`, `roles/btrfs-replication/`, relevant top-level playbooks and launcher scripts; plus accepted 10 November work recorded for 0043 and 0044. This is **design review only**, not a live `mango` or installed-host baseline.

## Ledger deployment structure observed

`roles/ledger/tasks/main.yaml` uses `import_tasks` to orchestrate `check.yaml`, firewall, utilities, `copy.yaml` and frontend configuration. `roles/ledger/tasks/copy.yaml`:

1. Creates a **list of required directories** with `ansible.builtin.file`.
2. Uses `ansible.posix.synchronize` to copy the managed `sync/` static tree, with `--omit-dir-times`.
3. Uses one `ansible.builtin.template` loop for multiple runtime files, with explicit modes.
4. Handles sensitive `.env`, a systemd unit and validation with dedicated tasks.

The desired pattern is **phase-oriented orchestration and concise manifests**, not blindly replacing every safety-critical task with a bulk copy.

## Existing backup layout observed in the uploaded bundle

| Source location | Observed responsibility | Planning implication |
|---|---|---|
| `local-backup.yaml` | `local_backup` group invokes `local-backup` role | Proposed user-facing rename to `backup-collection.yaml`; retain role and group |
| `scripts/local-backup.sh` | Check/apply wrapper invokes `local-backup.yaml` with `--limit mars` | Proposed companion rename with preserved flags and vault usage |
| `remote-backup.yaml` | `remote_backup` group invokes *default* `btrfs-replication` role | Check remaining callers; default `main.yaml` is **not** the same as `native.yaml` |
| `scripts/remote-backup.sh` | Check/apply wrapper invokes `remote-backup.yaml` with `--limit backup` | Candidate retirement only after source/live caller audit |
| `btrfs-replication.yaml` | Targets `local_backup:remote_backup`, includes `btrfs-replication` `tasks_from: native.yaml` | Preserve current source/receiver entry point |
| `snapshots.yaml` and `scripts/snapshots.sh` | Host-specific wrapper roles and `--tags snapshots` | Preserve host/tag semantics, not replace with generic snapshot role indiscriminately |
| `roles/local-backup/tasks/main.yaml` | Utility/setup, Btrfs USB mount, Diaries pull, source ACL, snapshots and script install | Already partly phase-oriented; guard source access and verified-Diaries barrier |
| `roles/local-backup/tasks/install_user_scripts.yaml` and `install_machine_scripts.yaml` | Create directories, synchronize static trees, render template loops, install cron | Already Ledger-like; preserve explicit exclusions, owner/mode and cron |
| `roles/local-backup/tasks/diaries_pull.yaml` | Opt-in receiver scripts, shared writer lock, services and timer state | Ordering/activation needs explicit checks; never bulk-copy lock state |
| `roles/snapshots/tasks/main.yaml` | Preconditions, Btrfs subvolumes, executable/template installation, service validation and activation | Major Ledger-style orchestration candidate; must preserve receiver refusal and snapshot safety gates |
| `roles/btrfs-replication/tasks/native.yaml` | Long source/receiver install pipeline, state/security checks, scripts, units and activation | Main refactor candidate; preserve endpoint-sensitive conditional actions and ordering |
| `roles/btrfs-replication/tasks/agreed-parent-runtime.yaml` | Receiver/source module manifests and launchers | Existing grouping can be reused; no unnecessary file moves |
| `roles/btrfs-replication/tasks/main.yaml` | Default role includes generic snapshots role | **Not equivalent** to `native.yaml`; resolve entry-point ownership deliberately |

The 9 November bundle's `native.yaml` is roughly 1,193 lines, and `snapshots/tasks/main.yaml` roughly 334 lines. These are *source-organisation observations*, not current-source assertions. The bundle contains obsolete or later-retired feature artefacts; the 10 November 0042/0043/0044 changes take precedence.

## Specific live-state and source-version concerns

- 0043 implemented central inventory scheduling under `/etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml`; on 10 November, source+receiver pruning is set for **04:15 UTC**, source prune cap **32**, receiver cap **10**, with independent timer activation and persistence. The 9 November role defaults still show the old hourly source prune and max-10 guard. **Use latest committed source and accepted installed state instead of copying these outdated defaults.**
- 0044 closed with three permanent maintained replication tests: `roles/btrfs-replication/tests/verify-replication.py`, `verify-protection.py`, `verify-shared-retention.py` and the README `roles/btrfs-replication/tests/README.md`. These newer names supersede the filenames in the 9 November bundle.
- 0042 retired the previous `remote-backup` **role** from permanent Playbooks; the **playbook** `remote-backup.yaml` may remain as a distinct obsolete entry point. Verify the actual current tree before deletions.
- The generic snapshots role must not be invoked on `remote_backup` if it would install source-mode configuration. Preserve the existing fail-closed receiver boundary.
- No source review can establish whether CI, cron, shell scripts, operator procedures or other repos still call `remote-backup.yaml`. Search the current Playbooks source, `/etc/ansible`, scheduled commands and reachable operator documentation at implementation time.

## Discovery to perform when work starts

1. Verify on **`mango`** `/home/richard/playbooks`: `git status --short --branch`, `git rev-parse HEAD`, `git remote -v`, `git ls-files`, role and launcher inventories. Verify the authoritative **Windows Cygwin** Diaries parent revision/status and submodule pins before changing source.
2. Read the **effective** `/etc/ansible` group/host variables for `mars` and `backup` (including Vault without publishing secrets), and installed service/timer units on both hosts. Check that 0039/0043 are complete.
3. Trace every caller, tag, handler, role default, conditional and installed-file destination before merging task files. Include `snapshots.yaml`, `btrfs-replication.yaml`, backup collection, cron, systemd and launchers.
4. Audit `ansible.posix.synchronize` scope: sync program-only trees; preserve exclusions (`diaries-pull.py`, `__pycache__/`, `*.pyc`), correct ownership and no blanket deletion. No `--delete` against directories containing state, logs, snapshots, credentials or operator-created files.
5. Generate a manifest of source→destination mapping, template inputs, owner/group/mode, privilege context, service handlers, activation gates, and intended installed-present/absent paths. Compare before and after, not source layout alone.

The end result should be smaller, understandable `main.yaml` orchestration with e.g. `validate.yaml`, `directories.yaml`, `copy.yaml`, `templates.yaml`, `security.yaml`, `activate.yaml` **where those boundaries are sensible**. File names are proposals, not mandatory micro-phases or invitations to create needless wrappers.
