# 0046-FEAT — Estate-wide installation-equivalence acceptance matrix

**Status: ALL OPEN / NOT TESTED.** The **sole equivalence acceptance criterion** is identical installation for **every managed host and every applicable playbook** when using the old `/etc/ansible` inventory versus the Git-controlled inventory, with the **same frozen post-0045 installation-producing Playbooks revision** and other operating inputs. Variable precedence and effective-variable equality are **diagnostics**, not standalone gates.

| ID | Required check | Acceptable evidence | State |
|---|---|---|---|
| A01 | 0045 formally CLOSED and published; correct current Git trees | 0045 closure receipts, source SHA, branch/status/submodule pins | OPEN |
| A02 | Frozen same post-0045 Playbooks installation-producing source, environment and dependencies across comparison | SHA and Ansible/tool/version/config receipts; no change to installation-producing role/template sources | OPEN |
| A03 | Complete old inventory discovery and secret-safe classification | Original sources, managed-host and operational playbook registry, classified file map | OPEN |
| A04 | New inventory securely selects the same managed hosts and applicable playbook/tag targeting | Complete old/new host/playbook/selection matrix with no missing coverage | OPEN |
| A05 | Only reviewed non-sensitive inventory committed; external Vault loading secured | Staged-secret scan, permissions, secure failure-mode checks, no secret in Git/evidence | OPEN |
| A06 | Repository `ansible.cfg`, launchers and normal operator invocations choose new inventory correctly | Source/config readback and scripts/automation discovery | OPEN |
| A07 | Full host-by-host baseline of the installation produced by old inventory | Complete all-managed-host installation footprints, stable managed-asset manifests, accepted volatile exclusions | OPEN |
| A08 | Full host-by-host installation-output comparison of old/new inventories | For every host and applicable playbook, deterministic rendered/install-plan comparisons with zero unexplained differences | OPEN |
| A09 | All-host controlled post-cutover apply/readback or equivalent validated installed-state proof | Per-host before/after managed-installed manifests, safe execution receipts and zero unexpected deltas | OPEN |
| A10 | `mars` and `backup` backup/replication/snapshot installation unchanged | Full assets, mode, ACL, units/timers, agreed-parent and policy readbacks | OPEN |
| A11 | All **other** managed hosts' installation unchanged | Complete per-host install equivalence evidence; representative checks alone insufficient | OPEN |
| A12 | Package/user/permission/service/cron/mount/security outcomes identical everywhere | Complete target result diff; secret-bearing assets compared securely in restricted process | OPEN |
| A13 | No host/playbook missing; no unreviewed exceptions | Coverage matrix with host and playbook names, evidence links and reviewer status | OPEN |
| A14 | Resolved variable and precedence differences reviewed *where they exist* | Redacted diagnostic report and demonstration of zero installed/security effect; equality is optional | OPEN |
| A15 | Secure Vault loading, secret availability and fail-closed safety unchanged | Protected-value use and access behaviour, negative tests and no disclosed values | OPEN |
| A16 | Normal backup/Btrfs regression checks and appropriate playbook syntax/host/tag checks pass | Consolidated logs; not accepted as substitutes for all-host installation equality | OPEN |
| A17 | Safe inventory cutover, no destructive work or silent `/etc/ansible` fallback | Deployment/activation record, change review and safe rollback | OPEN |
| A18 | Old inventory recoverable and no target installation mutations introduced for migration | Reversible controller source change and read-only backup-state safety evidence | OPEN |
| A19 | Final evidence/implementation accepted for the **entire managed estate** | Signed-off all-host zero-installation-delta manifest and any analysed non-impacting variable differences | OPEN |
| A20 | Playbooks and Diaries published; formal feature closure | Commit, remote and status receipts; 0046 under `complete/` | OPEN |

## Review rules

- **An installation delta on any managed host is a failure**, including changed managed file content, ownership/mode/ACL, user/privilege, package, service/timer, rendered configuration, or installed security behaviour. Naturally changing timestamps and data are not installation output; document each allowed volatile exclusion.
- **Changed variable precedence or effective variable value is not automatically a failure.** Investigate it and provide a complete per-host proof that the installed result, host targeting and security behaviour are unaffected. Unexplained differences remain open.
- A host or applicable playbook lacking installation-equivalence evidence is an **OPEN acceptance gap**, even when both inventories parse and `mars`/`backup` pass.
- Preserve raw logs and sanitised machine-comparable manifests under `evidence/Step N/` and avoid secret values or encrypted files in Git. Never run destructive backups/restores/snapshot pruning merely to validate inventory relocation.
- Mark a step CLOSED only after its actual evidence passes; formally close 0046 only when **all managed hosts and applicable playbooks** have PASS status, rollback is recorded and both repositories are published.
