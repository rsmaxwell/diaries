# 0046-FEAT — Move non-sensitive Ansible inventory into Playbooks Git

**State:** PLANNED — NOT STARTED  
**Created:** 10 November 2026  
**Owner:** Diaries parent Git repository, `change-control/in-progress/0046-FEAT - move non-sensitive Ansible inventory into Playbooks Git/`  
**Execution host / operational Playbooks:** `mango`, `/home/richard/playbooks`  
**Dependency:** **Start only after 0045-FEAT has been formally CLOSED and published.** Complete the already in-progress 0039-DEF and 0043-FEAT before beginning 0045, in line with the accepted 0045 plan.

## Objective

Move the **non-sensitive** Ansible inventory (host and group declarations, group/host variables and relevant Ansible repository configuration) from its current authoritative location in `/etc/ansible/` on `mango` into the **Playbooks Git repository**. Keep all Vault-protected secret material and the Vault password outside Git. Make the source-controlled inventory the **single authoritative non-secret inventory** used by normal invocations from the Playbooks checkout, without requiring routine `-i` arguments.

**Non-negotiable acceptance contract:** Using the **same then-current, post-0045 Playbooks installation-producing revision**, an installation driven by the new Git-controlled inventory must produce **exactly the same installed result as the original `/etc/ansible` inventory for every managed host and every applicable playbook/host targeting combination**. This is an estate-wide criterion, **not** a special case for `mars` and `backup`. No differences are authorised in managed files, rendered settings, ownership, permissions, packages, units, schedules, privileges, operational policy or behaviour. Pre-existing data and naturally changing runtime state must remain safe and are not installation artifacts.

**Variable precedence and effective variable equality are diagnostic tools, not independent acceptance gates.** They may differ if the resulting installation and behaviour remain demonstrably identical for all hosts. Any differences must be investigated and shown not to affect the installation, host targeting, secrets handling or security before acceptance.

This is an **inventory-source relocation**, not a chance to change role defaults, backup policy, credentials, deployments or installed software. The only permitted deliberate differences are **controller-side inventory location/version control and secure external Vault discovery**, provided the target installations remain identical. A precedence-preserving loader is one possible way to achieve this, but is not mandatory.

## Sequence and baseline

1. Complete and formally close **0045-FEAT — Reorganise backup and Btrfs Ansible deployment**. Do **not** base 0046 implementation on the older November Playbooks source archive or on a Playbooks commit recorded before 0045.
2. At the **start of 0046**, freeze the then-current clean, published Playbooks Git SHA and the actual authoritative `/etc/ansible` inventory/configuration from `mango`; identify **every managed host and applicable playbook**, all callers and secret sources. Capture a per-host baseline of the installation produced by the original inventory.
3. Migrate reviewed non-secret inventory into Git **without modifying installation-producing roles or their template/source contents**. Choose a secure external Vault loader and verify both inventories side by side. Use precedence/effective-variable comparison to identify risks, not as a substitute for installed-result comparison.
4. Run one consolidated, **estate-wide host-by-host installation-equivalence verification** using the same Playbooks source and repeatable collectors. Include `mars`, `backup` and **all other managed hosts**; do not use successful tests on two hosts as a proxy for the rest. Use safe controlled applications and/or fully verified deterministic installation-output comparison as appropriate to each host, and keep the feature OPEN wherever exact installation equality cannot be established.
5. Publish the two repositories' accepted changes and evidence, then formally close and move the feature to `change-control/complete/`.

**No work on 0046 begins merely because the planning ZIP has been applied.** Every implementation and acceptance step remains OPEN until actual evidence is collected and accepted.

## Proposed destination (subject to Step 1 discovery)

```text
/home/richard/playbooks/                 # tracked in Playbooks Git
  ansible.cfg                            # sets repo inventory, retains existing effective config
  inventory/
    hosts.yaml                           # complete non-secret host/group definitions
    group_vars/                          # non-secret group settings
      all/btrfs-maintenance-schedule.yaml
      ...
    host_vars/                           # non-secret host settings
      ...
  roles/ ...
  *.yaml                                  # playbooks, as delivered at 0045 closure

/etc/ansible/vault/ (or verified existing external Vault paths on mango)
  ...                                     # encrypted secret vars ONLY; outside Playbooks Git
~/.vault_pass.txt                         # outside Git; never copied to evidence
```

The directory layout is a **proposal**, not a claim that the current `/etc/ansible` inventory has been inspected. Existing Vault files need not be physically relocated if their original protected locations are appropriate. The migration must preserve an unambiguous secret-loading mechanism; Ansible does **not** automatically discover external `/etc/ansible/group_vars/` after switching inventory source to a repository directory.

## In scope

- Read-only source/variable classification and tracing of `/etc/ansible/hosts`, inventory plugins, `group_vars/`, `host_vars/`, `ansible.cfg`, wrappers, scheduled invocations, dynamic inventory if present, and all non-secret overrides (including current Btrfs maintenance scheduling).
- Complete transfer of reviewed **non-secret** inventory into Git, maintaining all managed-host and playbook targeting coverage. Variable names, source ordering and precedence may change **only where no installed-result or security difference arises**. Update active operator documentation, launchers/config resolution and controller bootstrap guidance as required.
- Keep **Vault files**, encrypted `!vault` values and secret credentials outside Git. Preserve Vault access/permissions and the existing `--vault-password-file ~/.vault_pass.txt` workflow unless equivalent secure behaviour is explicitly accepted.
- Baseline, secure variable-resolution diagnostics, **every-host installed-result equality**, and source-control/rollback evidence. Verify all applicable hosts and playbooks, not just backup endpoints. Plan safe controlled applications or equivalent complete deterministic installation-output proof for other hosts; never mistake syntax/host-list checks alone for installation equality.

## Out of scope and prohibitions

- No modifications to backup/replication/snapshot role logic, installed asset contents, service/timer calendar/activation, prune limits, retention, qgroups, agreed-parent pins, SSH/sudoers policy, backup data or deployment flags.
- No real secret values, Vault ciphertext, private keys, credential-bearing rendered files or Vault password in **either Git repository**, ZIP changes, committed evidence, terminal receipts or unsafe diagnostic output.
- No blind `ansible-inventory --list/--host` dumps into logs: those commands can expose decrypted inventory secrets. Sanitise **inside** the trusted comparison process before writing evidence; write only PASS/FAIL for protected-value equality.
- No duplicate active inventory in Git and `/etc/ansible`, no automatic fallbacks that silently select the old inventory, and no unreviewed use of higher-precedence `vars_files`/`include_vars` to load secrets.
- No destructive Btrfs operations, snapshot deletion, manual replication, backup restores, bulk sync against backup/state directories or forced service restarts solely to prove equivalence.

## Deliverables

- Git-controlled reviewed non-sensitive inventory and documented `ansible.cfg`/external Vault integration in `/home/richard/playbooks`.
- Secure side-by-side **old vs new inventory** comparison using the **same installation-producing Playbooks source SHA**, with a complete inventory of **every managed host and applicable playbook/host selection**.
- Same-tool **per-host old/new installation-output and installed-state comparisons across the entire managed estate**, with zero unexplained installation differences; backup data and other existing application data remain untouched.
- Controlled deployment/idempotence and read-only operational checks, version/commit receipts, rollback plan, final documented acceptance and formal change-control closure in the Diaries parent repository.

## Documents

- [`IMPLEMENTATION-STEPS.md`](IMPLEMENTATION-STEPS.md): four substantial implementation and acceptance steps.
- [`INVENTORY-AND-INSTALLATION-EQUIVALENCE-CONTRACT.md`](INVENTORY-AND-INSTALLATION-EQUIVALENCE-CONTRACT.md): exact equality requirements.
- [`SECRETS-AND-DISCOVERY-DESIGN.md`](SECRETS-AND-DISCOVERY-DESIGN.md): controller discovery, Vault precedence and security approach.
- [`reports/PLANNING-SOURCE-REVIEW-20261110.md`](reports/PLANNING-SOURCE-REVIEW-20261110.md): supported source observations and unknowns.
- [`tests/ACCEPTANCE-MATRIX.md`](tests/ACCEPTANCE-MATRIX.md): evidence gate checklist.
- [`tools/README.md`](tools/README.md): future one-off tools and evidence conventions.

**Closure rule:** Keep 0046 in `in-progress` with all steps OPEN until 0045 is CLOSED and installation equivalence has been proven for **every managed host and every applicable playbook**. Equal variable precedence is **not** required; unresolved or unverified installation results are not acceptable. Only then move to `complete` and publish the final receipts.
