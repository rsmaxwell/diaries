# 0046-FEAT — Private Ansible controller with public Playbooks and private inventory submodules

**State:** CLOSED — 12 November 2026. Migration, verification, publication and cleanup accepted.

**Authoritative closure evidence:** [reports/0046-FEAT-CLOSURE-20261112.md](reports/0046-FEAT-CLOSURE-20261112.md).

**Change-control owner:** Diaries parent Git repository, under `change-control/complete/`.

## Accepted operational topology

The completed implementation uses these **actual** repositories (not the preliminary names appearing in historical design notes):

| Repository | Visibility | Purpose | Verified `main` revision at closure |
| --- | --- | --- | --- |
| `rsmaxwell/ansible-controller` | **PRIVATE** | Parent checkout, documentation, `enter.sh` and pinned submodules | `f6ba7fec7752f4bbfa1535958500bde9dea3ea84` |
| `rsmaxwell/playbooks` | **PUBLIC** | Reusable Ansible playbooks, wrappers and roles, no inventory or Vault files | `df68a0e3bc57bae29a76f46a58c30835126d7f20` |
| `rsmaxwell/inventory` | **PRIVATE** | Complete inventory, group/host variables and encrypted Vault content | `ebcce026723db37b9b53b76ba21903a351d48466` |

The canonical operational checkout is `/home/richard/ansible-controller` on `mango`, with `playbooks/` and `inventory/` submodules. From an interactive shell on `mango`:

```bash
source "$HOME/ansible-controller/enter.sh"
```

The helper moves to the `playbooks/` directory, sets the private inventory path and selects `/etc/ansible/ansible.cfg`. The external Vault password file remains at `~/.vault_pass.txt` and is **not** in any Git repository. Pinned submodule revisions must be updated intentionally; a parent pull does not automatically advance child commits.

## Closure scope and evidence

The closure report records inventory semantic reconciliation, reviewed publication and repository visibility, a clean-source security scan, fresh-clone and submodule-pin verification, 13 inventory hosts, 14/14 top-level Ansible syntax checks and `pluto` connectivity (`pong`, no change). It also documents removal of the obsolete checkout and migration directories.

Those results do **not** constitute a separately demonstrated all-host installation-equivalence or end-to-end backup restore test. The original broad criteria remain preserved as historical planning requirements in [IMPLEMENTATION-STEPS.md](IMPLEMENTATION-STEPS.md) and [tests/ACCEPTANCE-MATRIX.md](tests/ACCEPTANCE-MATRIX.md). Do not read their original `OPEN` labels as the current feature status or infer that each planned test individually passed. The accepted closure scope and its stated limitations are in the closure report.

## Historical design and supporting documents

- [reports/0046-FEAT-CLOSURE-20261112.md](reports/0046-FEAT-CLOSURE-20261112.md) — authoritative completion and retained evidence summary.
- [IMPLEMENTATION-STEPS.md](IMPLEMENTATION-STEPS.md) and [tests/ACCEPTANCE-MATRIX.md](tests/ACCEPTANCE-MATRIX.md) — original requirements, preserved for traceability; not the current status register.
- [THREE-REPOSITORY-ARCHITECTURE.md](THREE-REPOSITORY-ARCHITECTURE.md) — historical architecture design (names and proposed paths can predate final implementation).
- [SECRETS-AND-DISCOVERY-DESIGN.md](SECRETS-AND-DISCOVERY-DESIGN.md) — historical secrets design and inventory discovery constraints.
- [INVENTORY-AND-INSTALLATION-EQUIVALENCE-CONTRACT.md](INVENTORY-AND-INSTALLATION-EQUIVALENCE-CONTRACT.md) — planned comparison standard.
- [tools/README.md](tools/README.md) — historical feature tooling and safe execution guidance.

**Next feature:** 0048-FEAT can proceed using the accepted 0046 closure, without repeating migration or destructive backup operations.
