# 0046-FEAT — Estate-wide installed-result equivalence contract

## Governing requirement

The original `/etc/ansible` inventory and new Git-controlled inventory are alternative controller inputs to the **same frozen, accepted post-0045 Playbooks installation-producing implementation**. For **every managed host and every applicable playbook/host/tag selection**, installing with the new inventory must produce **exactly the same installed result** as installing with the old inventory.

**No host is exempt because it is not `mars` or `backup`.** Both backup endpoints receive detailed safety readbacks, but **every other managed host requires its own accepted installed-result equivalence proof**. A clean playbook run, matching inventory variables or testing only representative hosts cannot substitute for this requirement.

**Variable precedence and effective-variable equality are not separate mandatory acceptance criteria.** Different variable-loading mechanisms are acceptable when the resulting installations, targeting and security behaviour are demonstrably identical. Variable comparisons remain highly useful for identifying where installation differences might arise. An unexplained variable discrepancy is an unresolved investigation, not proof of equivalence.

## What must remain identical on every host

| Installation category | Required equality between old and new inventories |
|---|---|
| Host and playbook targeting | Same managed hosts selected by each applicable playbook and operational tags/limits; no missing or additional installation work |
| Executables and static assets | Same deployed paths and content hashes, expected-absent paths, owners, groups, modes, executable bits |
| Rendered templates and configuration | Same generated files and settings, including protected/secret-bearing content compared only in trusted restricted context |
| Directories and security | Same managed directory layout, filesystems/mounts, ACLs, sudoers, users, groups, SSH/security scope and capabilities |
| Packages and dependencies | Same package versions and installation decisions, no unexpected installations/removals or upgrades caused by inventory relocation |
| Services, units, timers and cron | Same unit contents, service parameters, enabled/masked/active policies, schedules, cron and intended activation/restart outcomes |
| Host-specific application configuration | Same application artifacts and operational settings for each host managed by Playbooks, not just backup/replication components |
| Btrfs and backup endpoints | Same collection, replication, snapshot/retention, pruning limits, qgroup behaviour, agreed-parent protection and safety controls on `mars` and `backup` |
| Failure/security behaviour | Same credential use and availability, host authorisation, fail-closed checks and refusal of unsafe actions |

The only intended differences are **controller-side paths/inventory configuration and source control**. Naturally advancing runtime data (logs, clock readings, database contents, backup snapshots and transient counters) are not installed configuration and must be excluded **only when their classification and independent safety checks are documented**. No destructive data operation is authorised to force equality.

## How to establish estate-wide equivalence

1. **Freeze the implementation.** Record the actual post-0045 Playbooks full Git SHA, Ansible/core, collections, role/module/template sources, environment, Vault source and comparator versions. Do not compare different installation-producing code revisions and call that an inventory test.
2. **Enumerate complete coverage.** Inventory all managed hosts and operationally applicable playbook entry points, including tags, selections, launchers and scheduled commands. Create a host-by-playbook matrix with no unverified host rows.
3. **Capture old-inventory installation baseline for every host.** Use consistent, read-only collectors for installed configuration, scripts, permissions, packages, units, users, services and security settings. Include existing managed-state manifests and expected-absent assets. For complex hosts, supplement readback with source/template/parameter tracing that establishes what an installation of the frozen Playbooks using the original inventory produces.
4. **Compare new-inventory installation results for every host.** In secure isolated comparison runs, render/plan the installation with both inventories under the same code and environmental inputs, compare all managed outputs, and use controlled safe applications/readbacks wherever necessary to prove actual installed equality. Check-mode and rendered-file comparison alone are insufficient if they cannot account for all installed effects. Where safe proof cannot be achieved for a host, record it as OPEN; do not silently limit acceptance to `mars`, `backup` or a representative sample.
5. **Compare inventory/variable resolution diagnostically.** Examine missing/extra hosts, group targeting, effective variable values, undefined states, secret resolution, type and precedence to understand differences. A precedence/value difference is allowed only after showing it cannot change the installation, host targeting, safety or authorised secrets usage. Do not log decrypted variable values, ciphertext or guessable hashes.
6. **Cut over safely.** Set the repository inventory as the normal controller default only after the complete comparison is viable. Verify every host with the same collector/normalisation before and after controlled deployment or equivalent accepted proof, and verify wrappers/cron/CI select the new inventory. Any unexpected installed delta blocks closure; restore original controller inventory selection and investigate.
7. **Reconcile evidence.** The accepted coverage matrix must show PASS for **every managed host and every applicable playbook**, including non-Btrfs services. Preserve zero-difference results, classified volatile exclusions, any demonstrated non-impacting precedence changes, safe negative tests and rollback procedure under this feature.

## Security and operating constraints

- Vault ciphertext, password files, decrypted secrets and private keys must remain **outside both Git repositories and committed evidence**. Comparators may access protected values only within a trusted restricted process and must emit redacted results.
- The new Vault loader may use different precedence where that still produces an identical and secure installation. Missing/inaccessible credentials, changed installed secrets, privilege expansion or an unsafe failure path are not permitted.
- Do not mutate Btrfs snapshots, backup datasets, databases or unrelated host data to prove installation equivalence. Use appropriate safe applications and deterministic installation-output checks to establish the same result for the entire host estate.
- Preserve the old inventory in a protected, reversible controller-side form until the new source passes all-host acceptance. Do not leave an ambiguous active fallback in `/etc/ansible`.

## Failure and closure

**FAIL or OPEN:** any unexplained installed difference; changed host/playbook targeting; missing or insecure secrets; unexpected changed file/config/package/privilege/unit state; a host or playbook with unverified installation effects; secret disclosure; a destructive verification action; or any inability to restore known-good controller inventory selection. Precedence differences alone are **not** failures.

**Rollback:** revert the controller inventory selection to the preserved `/etc/ansible` source and verify managed installations remain unchanged. If an unexpected target asset changed, reconcile that specific asset with the frozen known-good Playbooks code and old inventory; do not restore or delete unrelated data.

**Closure:** every managed host and applicable playbook has accepted **identical installed-result evidence**; no security regression, and Playbooks/Diaries publication and change-control receipts complete. Otherwise 0046 remains **IN PROGRESS**.
