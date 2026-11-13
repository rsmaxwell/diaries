# 0048-FEAT — Step 1 ACL reconciliation (12 November 2026)

**Status:** Step 1 evidence collected; **READY FOR OPERATOR REVIEW**, not formally CLOSED. No production permission changes or deployment occurred.

## Scope, provenance and frozen revisions

The read-only collector ran from the authoritative Windows Diaries checkout, streamed to `mango` and inspected installed paths on `mars`. The successful run started `2026-11-12T21:34:15Z` and ended `PASS`. Original logs are preserved under `evidence/Step 1/raw-logs/`. The earlier missing-`getfacl` failure, from 21:31, remains in the existing Windows evidence directory and must not be discarded.

- Windows Diaries: `main` at `00688a4a1d816baa240db7fecafab47e5b97bfba`, status clean at the prior inspection; 0046 and 0047 directories under `change-control/complete/`.
- `mango` controller: `f6ba7fec7752f4bbfa1535958500bde9dea3ea84`.
- Playbooks submodule: `df68a0e3bc57bae29a76f46a58c30835126d7f20`.
- Inventory submodule: `ebcce026723db37b9b53b76ba21903a351d48466`.
- Effective Ansible inventory: `/home/richard/ansible-controller/inventory/hosts`, config `/etc/ansible/ansible.cfg`. Git clean-state and parent/submodule pins passed the collector.
- Historical 0047 baseline: `roles/backup-collection/source-modes.json`, frozen from 0045's accepted installation.

The 0046 closure report records formal closure and accepted publication evidence; the 0047 closure directory was observed. The separate 0046 post-closure documentation reconciliation/push is outside this Step 1 proof.

## Source and installed permission matrix

All entries are `richard:richard` at both locations. Source directories on `mango` are `0775`; installed destinations on `mars` are `0750`. The nine filter files are `0664` at both locations; their installed hashes match the 0047 `source-modes.json` contract according to the earlier successful installed-hash log.

| Source entry relative to `roles/backup-collection/` | Installed destination on `mars` | Source | Installed | Consumer / needed operations |
|---|---|---|---|---|
| `files/backup/` | `/home/richard/scripts/backup/` | 0775 | 0750 | `richard` backup job and installer need traverse; installer needs write |
| `files/backup/home/` | `/home/richard/scripts/backup/home/` | 0775 | 0750 | `richard` backup job needs traverse; installer needs write |
| `files/backup/home/includes` | `/home/richard/scripts/backup/home/includes` | 0664 | 0664 | user rsync reads filter; group writing not established |
| `files/backup/home/excludes-1` | `/home/richard/scripts/backup/home/excludes-1` | 0664 | 0664 | user rsync reads filter; group writing not established |
| `files/backup/home/excludes-2` | `/home/richard/scripts/backup/home/excludes-2` | 0664 | 0664 | user rsync reads filter; group writing not established |
| `files/backup-machine/` | `/root/scripts/backup/` | 0775 | 0750 | root backup job needs traverse; installer needs write |
| `files/backup-machine/home/` | `/root/scripts/backup/home/` | 0775 | 0750 | root rsync reads filters; installer needs write |
| `files/backup-machine/home/includes` | `/root/scripts/backup/home/includes` | 0664 | 0664 | root rsync reads filter; group writing not established |
| `files/backup-machine/home/excludes-1` | `/root/scripts/backup/home/excludes-1` | 0664 | 0664 | root rsync reads filter; group writing not established |
| `files/backup-machine/home/excludes-2` | `/root/scripts/backup/home/excludes-2` | 0664 | 0664 | root rsync reads filter; group writing not established |
| `files/backup-machine/remote/` | `/root/scripts/backup/remote/` | 0775 | 0750 | root remote rsync filter directory, conditional legacy usage |
| `files/backup-machine/remote/includes` | `/root/scripts/backup/remote/includes` | 0664 | 0664 | root remote rsync reads filter if legacy path enabled |
| `files/backup-machine/remote/excludes-1` | `/root/scripts/backup/remote/excludes-1` | 0664 | 0664 | root remote rsync reads filter if legacy path enabled |
| `files/backup-machine/remote/excludes-2` | `/root/scripts/backup/remote/excludes-2` | 0664 | 0664 | root remote rsync reads filter if legacy path enabled |

No extended access ACL, default ACL, or unexpected symlink was found on the 14 paths inspected. Their `getfacl -cp` output consists of the standard `user`, `group`, and `other` entries only. Absence is asserted for *these paths*, not the broader backup dataset.

## Parent chain and adjacent scripts

- `/home/richard` is `0750 richard:richard`; `/home/richard/scripts` is `0775 richard:richard`. Non-group users cannot normally traverse the home directory.
- `/root` is `0700 root:root`, `/root/scripts` is `0755 root:root`. The `/root` boundary prevents an ordinary `richard` process from reaching the `richard`-owned backup files below without privilege elevation.
- Prior installed-state log shows templated launcher scripts at `0744`; their mode is explicitly controlled by the Ansible `template` tasks, not the nine-filter source contract. Other adjacent scripts had mixed `0755` and `0744`; `/root/scripts/backup/cron` and some runtime/rollback subdirectories were `0775`. Those are not part of the 14-entry historical source-mode contract and must not be silently modified.
- The source `diaries-pull.py` is excluded from generic machine-script synchronization and is controlled by its separate opt-in task.
- `richard`'s existing sudo group and sudoers settings are to remain unchanged; no sudo-policy work is authorised under 0048.

## Relevant Ansible task ordering and risk

1. `install_user_scripts.yaml` uses `file: state=directory mode=0750` for several user backup directories, **then** `ansible.posix.synchronize` in `archive: true` mode from `backup/` with `--omit-dir-times` (not `--no-perms`).
2. `install_machine_scripts.yaml` creates machine directories without explicit mode, **then** archive-mode rsync copies `backup-machine/` (excluding `diaries-pull.py`).
3. Both paths template launcher scripts separately at `0744`.

Because rsync preserves source modes in archive mode, a conventional fresh checkout may use `0755` directories and `0644` non-executable regular files. In particular, a subsequent `0750` Ansible directory task may contend with rsync restoring `0755` from a clean clone. **The proposed mode simplification is not accepted until this is tested twice in a disposable local target.** Current `mango` source modes `0775` differ even from the recorded `0750` historical contract and should not be deployed as-is.

## Step 1 outcome and next gate

**Evidence available for P0/A1/A2 review:** prerequisite closures; exact controller and submodule SHAs; installed hashes and selected executable modes; per-path modes, ownership, ACLs and ancestry; consumer/task-order analysis; failed and successful collection logs. No evidence asserts that group-write or other-traverse permissions are necessary. These are **unresolved design questions for Step 2**, not Step 1 inspection failures.

**Step 1: READY FOR REVIEW, not CLOSED.** Next: run the supplied disposable Step 2 clean-clone/Ansible harness and decide which modes are safe and idempotent. Do not run a real `backup-collection` deployment yet.

## Separate operational notes (not 0048 blockers)

`acl` was installed successfully on `mango` and `mars`. Installation reported a pending `mango` reboot into kernel `6.8.0-147` (current `6.8.0-142`); schedule independently. Ubuntu suggested `apt autoremove` on `mars`; do not run it as part of 0048, especially without reviewing Btrfs/Snapper dependencies.
