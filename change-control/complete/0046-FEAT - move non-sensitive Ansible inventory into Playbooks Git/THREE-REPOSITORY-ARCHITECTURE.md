# 0046 — Three-repository layout and cutover contract

## Repository boundaries

1. **Private controller parent** (`rsmaxwell/ansible-controller`, proposed): holds a `.gitmodules` file, exact submodule Git links and controller/operator documentation; **not** a replacement for Diaries change-control.
2. **Existing public Playbooks** (`rsmaxwell/ansible-playbooks`): retain its independent history, current tested revision and role tree, including `backup-collection`, `snapshots`, and `btrfs-replication`. Keep the repository public and free of private site inventory and all Vault data.
3. **Private inventory** (`rsmaxwell/ansible-inventory`, proposed): all hosts, groups, group/host variable files, and whole-file or inline Vault-encrypted variables. Preserve inventory filename, structure and relative variable discovery unless a change passes estate-wide equivalence.

Before creating or pushing content, confirm both new GitHub repositories have **PRIVATE** visibility and correct access control. The two names are proposals, not verified existing repositories or remote URLs. The **actual** remote of the existing Playbooks repo must be read from `mango` rather than guessed.

The parent pins the exact commit of each submodule. Independently committing/pushing a child does **not** update the parent reference. Parent publication follows successful child publication; the accepted operational state is the triple: parent SHA, Playbooks SHA, inventory SHA.

## Expected layout on `mango`

```text
/home/richard/ansible-controller/                 # private parent working copy
  .gitmodules
  playbooks/                                   # public submodule
    *.yaml
    scripts/
    roles/
  inventory/                                   # private submodule
    hosts                                     # choose actual filename in Step 1
    group_vars/
    host_vars/

/etc/ansible/ansible.cfg                        # system-level Ansible config
/home/richard/.vault_pass.txt                   # NOT in any repository
```

The system `ansible.cfg` can select the new inventory by **absolute path**:

```ini
[defaults]
inventory = /home/richard/ansible-controller/inventory/hosts
```

This is illustrative; preserve any other actually effective configuration, do not overwrite `/etc/ansible/ansible.cfg` wholesale, and validate inventory naming during discovery. There must be no unreviewed higher-priority `ANSIBLE_CONFIG`/`ANSIBLE_INVENTORY` or working-directory config override. Standard commands should work from `/home/richard/ansible-controller/playbooks` without `-i`, using `--vault-password-file ~/.vault_pass.txt` where required.

**Ansible variable loading:** `group_vars/` and `host_vars/` inside the inventory submodule are inventory-relative and remain automatically discoverable. Audit any playbook-adjacent `group_vars/` and `host_vars/` in the public Playbooks repository and any explicit includes for precedence conflicts. Do not introduce custom Vault symlinks, external loaders or another inventory repository if native discovery suffices.

## Git commands — examples only, not instructions to execute yet

After the two child repositories and parent exist and SSH access is authorised:

```bash
# Terminal: SSH session on mango, from the new parent root
cd /home/richard/ansible-controller
git status --short --branch
git submodule status --recursive

# On a fresh controller (after private access is provisioned):
# git clone --recurse-submodules <VERIFIED_PRIVATE_PARENT_REMOTE> /home/richard/ansible-controller

# After pulling an updated parent; use pinned revisions, not --remote:
git pull --ff-only
git submodule update --init --recursive
```

Review each submodule's branch, detached-HEAD condition, uncommitted state and exact pinned SHA before editing or deploying. To change the inventory or Playbooks intentionally: commit and push that child, then stage **its updated Git link** in the parent, commit and push the parent. A parent pull without submodule update leaves child working-tree revisions unchanged.

## Migration and controlled cutover

- **Baseline:** leave `/home/richard/playbooks` and `/etc/ansible` untouched as the operational reference; capture live Ansible config and inventory discovery, current Git SHAs, Vault classification, host/playbook coverage and complete installed-state footprints.
- **Stage:** create the parent and submodules at `/home/richard/ansible-controller`, populate private inventory using audited content; do not put plaintext secrets in private Git, and never put any inventory/Vault in public Playbooks. Freeze the public Playbooks code revision for old/new comparisons.
- **Compare:** explicitly choose old and staged inventory only in isolated tests; validate Vault access, host/group selection, every applicable playbook and all-host identical installation results. No bulk destructive operations or backup restore.
- **Activate:** update the actual effective Ansible config to point to the private inventory, update launchers/CI/operator working directories and authorised private repository credentials. Record effective config before and after. Keep old sources recoverable as rollback **without a second active inventory fallback**.
- **Close:** verify normal no-`-i` commands on `mango`, every managed host and CI/operator callers; publish child SHA receipts and parent pin; retain rollback evidence within the Diaries feature directory. Retire old active checkout and duplicate inventory only after acceptance and deliberate reconciliation.

## Security and availability

Private GitHub access is required to clone/update both the private parent and inventory; a public Playbooks user must not need private access just to use the reusable roles. The public repo must not contain private submodule references that force private access on public consumers.

Audit all automation users (including Jenkins) before moving paths. If a caller lacks private inventory access, provide a deliberately authorised deployment route, **not** a copy of Vault files into public source. Do not put GitHub tokens, SSH private keys, credential-bearing remote URLs, Vault passwords, or rendered decrypted files into any Git repository or evidence bundle.

Temporary feature-specific scripts and receipts belong in the Diaries feature folder. Permanent configuration, if required, belongs to a suitable Playbooks role or controller documentation, not ad hoc scripts in `/home/richard`.
