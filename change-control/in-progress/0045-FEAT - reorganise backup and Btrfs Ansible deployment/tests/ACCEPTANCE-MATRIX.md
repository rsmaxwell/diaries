# 0045-FEAT — Consolidated acceptance matrix

**Status: Steps 1–3 CLOSED (11 November 2026), Step 4 OPEN.** Refer to `reports/STEP1-FINAL-ACCEPTANCE-20261111.md` for the accepted baseline and documented scope of external caller verification before launcher removal.

| ID | Check | Expected acceptance evidence | Status |
|---|---|---|---|
| A01 | 0039 and 0043 closed; Playbooks/Diaries Git baseline clean and recorded | Completed feature closures; `baseline-20261111-111819Z` captures both source revisions | PASS (Step 1) |
| A02 | Effective `/etc/ansible` inventory incl. 0043 central schedule frozen | `mango-source-and-inventory.txt`, no plaintext Vault disclosure | PASS (Step 1) |
| A03 | Old launcher/playbook caller audit complete | Known tracked source references mapped in Step 1; **external invocation check required before Step 2 deletion** | PASS — audited scoped host filesystem and 27 Jenkins jobs; original launchers retained, residual external scope documented |
| A04 | Full old→new managed asset and privilege map | Baseline old install captured; proposed new install mapping, compare after deployment | PASS — source-to-installed map and v2 manifests confirm managed asset equivalence |
| A05 | All new Ansible syntax, inventory host/tag selection and safety guards pass | Syntax/list-hosts/list-tags, guard test logs | PASS — 3 playbook syntax checks, task/source-equivalence, host dispatch and safety assertions |
| A06 | Maintained replication tests pass | `verify-replication.py`, `verify-protection.py`, `verify-shared-retention.py` logs | PASS — 25 replication cases, 5 protection cases and shared-retention check |
| A07 | Maintained snapshots / local backup regression tests pass | Test logs incl. 0043 source prune and 0039 qgroup invariants | PASS — corrected native snapshot and local-backup regressions |
| A08 | No unexpected change in installed executables/templates/units/config | Normalised before/after manifests, explicit all-equal result | PASS — `mars` and `backup` static manifests equal; runtime-only ExecStart digest reconciled |
| A09 | `mars` backup acquisition, mount, ACL, cron and writer/snapshot barrier preserved | Read-only service/config/mount/ACL and scheduled state | PASS — `mars` installed paths, units, cron, mount, ACL and barrier fingerprints unchanged |
| A10 | `mars`/`backup` replication roles, agreed-parent holds and retention remain correct | State readbacks and proof source/receiver distinction unchanged | PASS — native source/receiver playbook applied without change, hold checks passed |
| A11 | Timer, pruning, replication and qgroup schedules/activation exactly preserved | Unit and enabled/active/persistence readback, effective inventory | PASS — unit/config/schedule fingerprints match baseline and manager readbacks healthy |
| A12 | Scoped apply and second apply show no unexpected service/data changes | Ansible log and idempotence/managed-file evidence | PASS — 13:22 UTC reapply: all hosts changed=0, failed=0, unreachable=0 |
| A13 | No destructive backup operation, secret disclosure or unsanctioned `--delete` | Playbooks code review and deployment logs | PASS — source contract and actual apply; no manual data operations; review logs before public Git publication |
| A14 | Rollback path and accepted correctness evidence retained | Known-good SHA, pre-change manifest, risk/rollback receipt | PASS — rollback Playbooks `7dfa93f` and definitive baseline preserved; no rollback required |
| A15 | Playbooks and Diaries commits published; formal closure recorded | Git SHA/status/push receipts, feature under `complete/` | OPEN — Playbooks `1939a09` published; Diaries final evidence commit / formal feature move outstanding |

## Equivalence reporting rules

- Separate installed managed static content from mutable backup/snapshot state; runtime data preservation must be verified without freezing or resetting datasets.
- *Any unexpected managed asset, service, schedule, ownership, permission or protective-state difference fails acceptance.* Record exact mismatch and fix the refactor or revert it, then repeat only affected tests.
- An Ansible success summary or an offline syntax check **alone** does not establish equivalence.
- Do not add an artificial full restore or manual replication test when already accepted correctness and this feature's installed-state comparisons are sufficient.
