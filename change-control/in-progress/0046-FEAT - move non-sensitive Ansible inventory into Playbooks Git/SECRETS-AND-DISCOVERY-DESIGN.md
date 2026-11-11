# 0046-FEAT — Inventory discovery, secret isolation and precedence design

**Status: design proposal only — NOT implemented.** Confirm exact controller version, original inventory and file classification on `mango` during Step 1. Avoid premature changes to `ansible.cfg` or `/etc/ansible`.

## Controller-side source-of-truth model

- **In Git:** `/home/richard/playbooks/inventory/hosts.yaml`, its reviewed `inventory/group_vars/` and `inventory/host_vars/`, and repository-level `ansible.cfg` to direct normal Playbooks-root invocations to this inventory.
- **Outside Git:** the existing encrypted Vault files (prefer a clearly documented protected location such as `/etc/ansible/vault/...`, but preserving valid existing locations is allowed), plus `~/.vault_pass.txt` and any relevant external credentials. Do not put plaintext, encrypted `!vault` blocks, full Vault ciphertext or private keys in Git or evidence.
- **One authoritative active source:** after acceptance, do not leave active conflicting definitions in `/etc/ansible/group_vars`/`host_vars` which Ansible might still load through another inventory or playbook location. Preserve an offline rollback copy; do not remove OS/package-managed `/etc/ansible/ansible.cfg` simply to make the tree empty.

Example **candidate** repository configuration (not a ready-to-apply file):

```ini
[defaults]
inventory = ./inventory/hosts.yaml
```

The actual `ansible.cfg` must also preserve **every relevant effective setting** previously obtained from Ansible's configuration hierarchy; an apparently minimal file can suppress a setting previously defined in `/etc/ansible/ansible.cfg`. Test `ansible --version` and sanitised `ansible-config dump --only-changed` from the repo root and from any operational launchers. Relative paths may behave differently under `ANSIBLE_CONFIG` and different working directories. Keep routine `ansible-playbook ... --vault-password-file ~/.vault_pass.txt` calls free of redundant `-i`; use explicit dual-inventory selection only inside isolated equivalence tests.

## External Vault loading must preserve installed results (not necessarily precedence)

Ansible's default inventory variable loading is location- and precedence-dependent. Files under `inventory/group_vars` and `inventory/host_vars` can be discovered at inventory scope, and playbook-adjacent `group_vars` may introduce a separate precedence layer. **Files left under `/etc/ansible/group_vars` do not automatically follow a repository inventory.** Also, a blanket `vars_files` or `include_vars` for secrets runs at a different variable-precedence level than inventory group/host variables and may change values despite identical source text.

The *presence* of a precedence difference is a diagnostic signal, **not an independent failure**. The acceptance criterion is unchanged installed output and secure operation on **every managed host**. At Step 2, compare these viable mechanisms against the **actual inventory** and select one supported, secure, explicit method:

1. **Maintain group/host-scope Vault loading using controller-provisioned, Git-ignored links or references** from appropriate inventory variable locations to externally protected Vault files. This is a straightforward way to reduce risk, but equivalent precedence is not a requirement. Validate resolution, paths, ownership/mode and reproducibility; do not commit actual secret files or credentials.
2. **Use a supported inventory or vars plugin** to load external encrypted files securely. Changed scope or priority is permissible only when complete per-host installation-equivalence and security checks show no effect; avoid hidden multiple inventory sources or nondeterministic source ordering.
3. **Use explicit `vars_files`/`include_vars` if appropriate**, even though precedence may differ, provided every affected host and playbook produces identical installed results and security/credential behaviour. A successful syntax check or equality on `mars`/`backup` alone is insufficient.

Prefer the simplest mechanism that passes comparison, is supported by the installed Ansible version, fails clearly when Vault is unavailable, and is documented as part of `mango` controller bootstrap. Secret-loading references should not require per-role special cases. Vault file contents and permissions must remain protected while comparisons are performed.

## Inventory migration consistency checks

- Preserve the complete managed-host set and equivalent selection/installation behaviour for all operational playbooks. Track aliases, group nesting, priorities (`ansible_group_priority`) and source ordering carefully: structural changes may be acceptable **only if** the resulting installation and security behaviour remain identical for every affected host. Avoid confusing duplicate inventory sources.
- Preserve host/user/SSH/become settings and any `ansible_connection`/`ansible_host` or `ansible_ssh_common_args` overrides. Reclassify sensitive values before copying; even values that look ordinary can contain tokens or credentials.
- Check for Vault data embedded within non-secret YAML. Splitting may change precedence; compare resolved values to diagnose risk and verify the **installed effect** for every affected host. Do not assume that a moved variable is harmless merely because Ansible accepts the file.
- Preserve repository-root playbook behaviour, script wrappers and CI/scheduled launchers by auditing their working directory, `ANSIBLE_CONFIG`, `ANSIBLE_INVENTORY`, current inventory and Vault flags. Include **all other managed hosts** in the installed-result equivalence matrix, using safe methods appropriate to each host; a simple selection check does not establish acceptance.
- Check that `btrfs_native_endpoint_role` remains `source` for `mars` and `receiver` for `backup`, and that the central 0043 schedule and any post-0045 inventory overrides remain effective. Never substitute old, hard-coded planning-time values for the actual frozen baseline.
- Document and test error cases: missing Vault source, inaccessible protected file, wrong controller working directory, unexpected `ANSIBLE_CONFIG` override, absent group variable and conflicting old `/etc/ansible` sources. A failure must be visible and must not silently default to potentially unsafe Btrfs values.

## Documentation and Git safety

- Extend the Playbooks `.gitignore` only for clearly specified secrets or locally provisioned integration artifacts; do not use broad ignore patterns that hide legitimate inventory diffs.
- Before any Playbooks commit, explicitly inspect staged paths and scan for accidentally staged secrets including `!vault`, password/private-key tokens and encrypted file payloads. Record a **PASS/FAIL-only** security receipt; do not print suspect secret contents.
- Keep secrets outside both the Playbooks and Diaries repositories. Protect private collection tools or their transient data and ensure raw terminal logs do not include expanded Vault values. Do not include actual secret file content in ZIPs or rollback packages.

## Reference material for implementation verification

- [Ansible inventory organisation and host/group variables](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html)
- [Ansible configuration discovery and precedence](https://docs.ansible.com/projects/ansible/latest/reference_appendices/config.html)
- [Ansible variable precedence, including `vars_files` and `include_vars`](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_variables.html)

Validate the exact Ansible version on `mango` during implementation; the linked documentation is general guidance, not proof of the controller's present behaviour.
