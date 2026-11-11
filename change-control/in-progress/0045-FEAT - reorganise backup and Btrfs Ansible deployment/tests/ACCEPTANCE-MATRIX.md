# 0045-FEAT — Consolidated acceptance matrix

**Status: Step 1 baseline CLOSED (11 November 2026); implementation and deployment OPEN.** Refer to `reports/STEP1-FINAL-ACCEPTANCE-20261111.md` for the accepted baseline and documented scope of external caller verification before launcher removal.

| ID | Check | Expected acceptance evidence | Status |
|---|---|---|---|
| A01 | 0039 and 0043 closed; Playbooks/Diaries Git baseline clean and recorded | Completed feature closures; `baseline-20261111-111819Z` captures both source revisions | PASS (Step 1) |
| A02 | Effective `/etc/ansible` inventory incl. 0043 central schedule frozen | `mango-source-and-inventory.txt`, no plaintext Vault disclosure | PASS (Step 1) |
| A03 | Old launcher/playbook caller audit complete | Known tracked source references mapped in Step 1; **external invocation check required before Step 2 deletion** | PARTIAL — Step 2 gate |
| A04 | Full old→new managed asset and privilege map | Baseline old install captured; proposed new install mapping, compare after deployment | BASELINE PASS; new-map verification Step 2/3 OPEN |
| A05 | All new Ansible syntax, inventory host/tag selection and safety guards pass | Syntax/list-hosts/list-tags, guard test logs | OPEN |
| A06 | Maintained replication tests pass | `verify-replication.py`, `verify-protection.py`, `verify-shared-retention.py` logs | OPEN |
| A07 | Maintained snapshots / local backup regression tests pass | Test logs incl. 0043 source prune and 0039 qgroup invariants | OPEN |
| A08 | No unexpected change in installed executables/templates/units/config | Normalised before/after manifests, explicit all-equal result | OPEN |
| A09 | `mars` backup acquisition, mount, ACL, cron and writer/snapshot barrier preserved | Read-only service/config/mount/ACL and scheduled state | OPEN |
| A10 | `mars`/`backup` replication roles, agreed-parent holds and retention remain correct | State readbacks and proof source/receiver distinction unchanged | OPEN |
| A11 | Timer, pruning, replication and qgroup schedules/activation exactly preserved | Unit and enabled/active/persistence readback, effective inventory | OPEN |
| A12 | Scoped apply and second apply show no unexpected service/data changes | Ansible log and idempotence/managed-file evidence | OPEN |
| A13 | No destructive backup operation, secret disclosure or unsanctioned `--delete` | Playbooks code review and deployment logs | OPEN |
| A14 | Rollback path and accepted correctness evidence retained | Known-good SHA, pre-change manifest, risk/rollback receipt | OPEN |
| A15 | Playbooks and Diaries commits published; formal closure recorded | Git SHA/status/push receipts, feature under `complete/` | OPEN |

## Equivalence reporting rules

- Separate installed managed static content from mutable backup/snapshot state; runtime data preservation must be verified without freezing or resetting datasets.
- *Any unexpected managed asset, service, schedule, ownership, permission or protective-state difference fails acceptance.* Record exact mismatch and fix the refactor or revert it, then repeat only affected tests.
- An Ansible success summary or an offline syntax check **alone** does not establish equivalence.
- Do not add an artificial full restore or manual replication test when already accepted correctness and this feature's installed-state comparisons are sufficient.
