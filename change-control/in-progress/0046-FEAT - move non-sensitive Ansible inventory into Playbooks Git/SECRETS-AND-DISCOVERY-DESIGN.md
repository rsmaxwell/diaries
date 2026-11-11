# 0046 — Vault, inventory discovery and secret-handling design

## Accepted security boundary (11 November 2026)

- **Public** `ansible-playbooks`: reusable playbooks/roles/tests/templates; no actual inventory or Vault material.
- **Private** `ansible-inventory`: all site host/group declarations and variables, including Vault-encrypted files and encrypted inline values. A private repo still has a permanent Git history; only correctly encrypted secrets may enter it.
- **Private** `ansible-controller`: top-level submodule pointers and documentation; no passwords or copied Vault files.
- **Outside all Git repositories:** `/home/richard/.vault_pass.txt`, private SSH keys, GitHub tokens, plaintext credentials, decrypted outputs, and controller-local sensitive runtime state.

A file containing an Ansible `!vault` field is **not necessarily wholly encrypted**. Read it in a restricted context and check each plaintext field for secrets before committing. Files with `$ANSIBLE_VAULT;` headers may be whole-file encrypted, but verify format and decryption locally without logging content. Never simply commit `/etc/ansible` recursively or assume that everything under `group_vars` is protected.

Do not place actual private inventory, Vault ciphertext, plaintext credential fields, hostvars dumps, sensitive file names if classified as secret, or decrypted rendered configurations into the Diaries feature ZIP or evidence. GitHub remote visibility must be verified as **PRIVATE before first push** of private inventory. If anything secret has ever entered public Git, treating a later deletion as sufficient is unsafe; escalate for credential rotation/history remediation instead of silently continuing.

## Discover on `mango` before modifying anything

Read the effective config location and applicable `ANSIBLE_CONFIG`/`ANSIBLE_INVENTORY`, active `/etc/ansible/hosts`, `group_vars`/`host_vars`, dynamic inventory, Vault password/ID workflows, plugins and YAML includes. Find out which of the current files contain plaintext credentials, encrypted whole files or inline values; compare permissions and symlink targets. Do not print secret values or copy them to an intermediate ZIP.

Audit playbook-local variable directories and overrides. Once the new inventory lives at `/home/richard/ansible-controller/inventory`, inventory-relative `group_vars`/`host_vars` can be read normally by Ansible; the Vault password supplied with `--vault-password-file ~/.vault_pass.txt` decrypts encrypted values. **Moving inventory does not make Vault content automatically discoverable elsewhere**: preserve relevant relative directory structure and check actual precedence.

Also audit:

- All hosts, groups, `ansible_host`, `ansible_user`, connection and become settings.
- Variable loading through `vars_files`, `include_vars`, plugins and playbook-level vars.
- Jenkins jobs, Windows operator commands, scripts, systemd timers, cron and `cd` assumptions.
- Host/group precedence and the Btrfs roles and central maintenance schedule; compare against the *live frozen* baseline rather than historical hard-coded values.
- Missing submodule, missing private remote access, wrong Vault password and mixed inventory source negative cases.

## Safe movement of encrypted Vault files

1. Confirm private destination/repository permissions, branch access and correct Git remotes.
2. Inventory/classify all source files without exporting contents into chat, raw logs or change-control evidence.
3. If a plaintext credential must become Git-managed, first encrypt it using an accepted Ansible Vault mechanism in the trusted environment. Validate decryption locally without printing it; do not copy pre-encryption content to the private repo or staging area.
4. Preserve exact original logical scope (`group_vars`/`host_vars` names, nested paths, group priority and include references) where possible. Run all-host effective and installed-output comparisons.
5. Add and inspect only intended paths in the private repository. Verify there is no plaintext secret, private key, Vault password, or secret-bearing output in the staged data. Also verify no Vault material is staged in **public** Playbooks or in the parent.
6. Commit/push child inventory privately and update the parent pin only after acceptance; preserve the original `/etc/ansible` source as a reversible rollback artifact, not a second active inventory.

## Access model and failure modes

An authorised operator or automation account needs read access to the private controller parent **and** private inventory submodule; public users need only the public Playbooks repository. Using SSH Git remotes avoids embedding tokens in `.gitmodules`; never use credential-bearing HTTP URLs.

If the private repo cannot be cloned, a submodule checkout is missing, Vault password is absent/wrong, or the inventory config resolves to an unexpected source, the execution must **fail clearly** before any installation/deletion. Do not introduce automatic fallback to `/etc/ansible/hosts`, empty vars, a public dummy inventory or permissive Btrfs defaults.

## Documentation hygiene

Old planning reports dated 10 November 2026 remain historical evidence. This file supersedes their earlier assumption that all Vault ciphertext stays outside Git and that the public Playbooks repository owns the inventory. The Vault **password** remains outside Git in every design.
