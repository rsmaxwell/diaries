# 0046-FEAT — Private Ansible controller with public Playbooks and private inventory submodules

**State:** PLANNED — architecture agreed; implementation and acceptance OPEN.

**Original change-control directory name:** Retained to preserve existing feature references. Its former objective—committing only non-confidential inventory into the public Playbooks repository—is **superseded** by the three-repository decision of 11 November 2026.

**Change-control owner:** Diaries parent Git repository, this feature directory.

**Prerequisites:** 0045-FEAT and 0047-FEAT formally closed and published (reported completed on 11 November 2026); verify live Git revisions and state again before implementing. 0048-FEAT remains dependent on formal 0046 closure.

## Agreed outcome

Use three distinct Git repositories with explicit visibility:

| Repository | Visibility | Role |
|---|---|---|
| `rsmaxwell/ansible-controller` (proposed name; verify/create) | **PRIVATE** | Top-level operational checkout; pins two Git submodules and contains controller setup/usage documentation. |
| `rsmaxwell/ansible-playbooks` (existing) | **PUBLIC** | Reusable playbooks, roles, tests, templates; **no inventory, Vault ciphertext or protected site configuration**. |
| `rsmaxwell/ansible-inventory` (proposed name; verify/create) | **PRIVATE** | Entire site inventory: hosts, `group_vars`, `host_vars`, Vault-encrypted values and files. |

Keep `/home/richard/.vault_pass.txt`, private SSH keys, access tokens and any other **plaintext credentials** outside all three repositories. A private Git repository is an additional access boundary, **not a licence to commit plaintext passwords**.

```text
/home/richard/ansible-controller/             # new proposed checkout on mango (PRIVATE parent)
  .gitmodules
  README.md
  playbooks/                               # existing PUBLIC Git repository as submodule
    backup-collection.yaml
    snapshots.yaml
    btrfs-replication.yaml
    roles/ ...
  inventory/                               # new PRIVATE Git repository as submodule
    hosts                                  # final filename decided from live inventory
    group_vars/ ...                        # public-inventory-type data stays private here
    host_vars/ ...
    ...                                    # Vault-encrypted files in original group/host scope

/etc/ansible/ansible.cfg                   # system config points to new inventory path at cutover
/home/richard/.vault_pass.txt             # external, never committed
```

**Do not assume these repositories or the checkout exist yet.** Repository creation and credential/access configuration are implementation steps, not work already done. Do not replace the current running `/home/richard/playbooks` checkout or `/etc/ansible` inventory until acceptance supports cutover.

## Critical acceptance contract

With the *same frozen Playbooks installation-producing revision*, every managed host and every applicable playbook/host selection must have **identical installed configuration and secure behaviour** using old `/etc/ansible` inventory versus the private inventory submodule. Include all managed hosts, not only `mars` and `backup`. Variable precedence/effective values are diagnostics; any differences must be investigated and proven not to affect installations, targeting or security.

The final operational checkout must be reproducible by cloning the **private controller parent** and initializing its **exact pinned submodule commits**. The normal Ansible commands run from `playbooks/`, with the system configuration selecting the sibling private inventory and the existing Vault password file. No routine `-i` override.

The current `/etc/ansible` source and `/home/richard/playbooks` checkout remain the working and reversible baseline until controlled activation. The public Playbooks Git history must not acquire private inventory or encrypted Vault data.

## Implementation and evidence

- [IMPLEMENTATION-STEPS.md](IMPLEMENTATION-STEPS.md): baseline, implementation, estate-wide equivalence, cutover/closure.
- [THREE-REPOSITORY-ARCHITECTURE.md](THREE-REPOSITORY-ARCHITECTURE.md): submodule mechanics, paths and access rules.
- [SECRETS-AND-DISCOVERY-DESIGN.md](SECRETS-AND-DISCOVERY-DESIGN.md): encrypted Vault handling, preflight, no-leak requirements.
- [INVENTORY-AND-INSTALLATION-EQUIVALENCE-CONTRACT.md](INVENTORY-AND-INSTALLATION-EQUIVALENCE-CONTRACT.md): binding installation equality.
- [tests/ACCEPTANCE-MATRIX.md](tests/ACCEPTANCE-MATRIX.md): explicit acceptance gates.
- [reports/THREE-REPOSITORY-DECISION-20261111.md](reports/THREE-REPOSITORY-DECISION-20261111.md): accepted design and superseded proposal.
- [tools/README.md](tools/README.md): feature-local discovery/verification tooling rules.

**Status:** This package updates documentation only. No Git repository, submodule, active inventory, Vault file, Ansible configuration, CI job or host installation has been changed by the package.
