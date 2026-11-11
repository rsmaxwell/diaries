# 0046-FEAT — Three-repository and estate-wide installation acceptance matrix

**All checks OPEN / NOT TESTED.** Architecture agreed; no operational migration was performed by the documentation amendment.

| ID | Acceptance requirement | Status |
|---|---|---|
| A01 | Closed/published 0045 and 0047 prerequisites verified; current Windows Diaries and `mango` Git states captured | OPEN |
| A02 | Old effective `/etc/ansible` config/inventory and **all hosts/playbooks/callers** discovered without secret leakage | OPEN |
| A03 | Existing Playbooks install-producing source and runtime dependencies frozen at an exact SHA | OPEN |
| A04 | Complete all-host installed-state and host/playbook/tag/limit baseline recorded | OPEN |
| A05 | Real private parent and inventory repositories identified; **PRIVATE** visibility/access confirmed before data push | OPEN |
| A06 | Existing public Playbooks repository retains its independent history and has no inventory/Vault content | OPEN |
| A07 | Private parent contains correct `.gitmodules`, two child URLs, and exact pinned child revisions | OPEN |
| A08 | Complete inventory, group_vars, host_vars and encrypted Vault material migrated **only** to private inventory child | OPEN |
| A09 | No plaintext secrets/password/private keys in any Git repository, packages, evidence or remote; private staged-secret audit passed | OPEN |
| A10 | Vault password file remains outside all Git; private submodule and Vault access fail closed | OPEN |
| A11 | Native inventory-relative `group_vars`/`host_vars` discovery, explicit includes and precedence risks verified | OPEN |
| A12 | Original `/etc/ansible` and `/home/richard/playbooks` still recoverable during comparisons | OPEN |
| A13 | All old/new inventory host/group/playbook/tag/limit targets accounted for; no missing host/playbook | OPEN |
| A14 | Every-host source/rendered/installed output produces identical installation under both inventories with same Playbooks SHA | OPEN |
| A15 | Packages, file hashes/modes/ACL, sudoers/users, timers/cron, units/services, mounts and privilege/security outcomes identical everywhere | OPEN |
| A16 | `mars` and `backup` Btrfs/Diaries backup static installation and protection unchanged; health checks safe | OPEN |
| A17 | All **other** managed hosts checked; no representative-host shortcut | OPEN |
| A18 | Vault/variable differences resolved as to installed effects; protected comparisons stay secret-safe | OPEN |
| A19 | Maintained regressions, Ansible syntax, controller freshness and intended failure-mode tests pass | OPEN |
| A20 | Fresh private-parent clone with `--recurse-submodules` reproduces exact accepted child commits | OPEN |
| A21 | Effective `/etc/ansible/ansible.cfg` and caller working directories transition with no routine `-i` | OPEN |
| A22 | All relevant Jenkins/CI/operator/scheduled callers verified with authorised private inventory access | OPEN |
| A23 | Controlled all-host cutover, exact state readback/idempotence, and documented non-destructive rollback accepted | OPEN |
| A24 | Public/private child and parent Git SHA/visibility/pin receipts published and clean | OPEN |
| A25 | All evidence accepted, feature formally CLOSED under Diaries `change-control/complete/`; 0048 unblocked | OPEN |

**Hard gates:** A single unexplained installation difference, missing host, missing private submodule, failed Vault loading, plaintext secret in staged material, private repo misconfigured as public, or unverified CI caller blocks acceptance. Differences in variable precedence/effective maps are diagnostic but cannot result in changed installed/security behaviour. Do not run backup restores, manual snapshot deletion/pruning, or redundant full end-to-end exercises merely for inventory migration.

**Evidence:** In `evidence/Step N/`, store only safe manifest metadata, aggregate results, source/parent SHA receipts and sanitised outputs. Never commit actual private inventory or even encrypted Vault ciphertext to Diaries. Preserve unmodified operational evidence inside the designated feature directory where safe.
