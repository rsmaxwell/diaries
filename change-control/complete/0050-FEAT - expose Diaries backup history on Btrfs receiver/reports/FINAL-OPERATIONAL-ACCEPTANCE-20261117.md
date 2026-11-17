# 0050 — Final operational acceptance (17 November 2026)

**Feature state:** Operationally accepted; Git finalisation and formal change-control closure pending.

## Evidence and observed results

The operator ran a strict receiver-limited Ansible reapply from `/home/richard/ansible-controller/playbooks` on `mango`. The recap was `backup: ok=37 changed=0 unreachable=0 failed=0 skipped=43`, followed by `0050 ANSIBLE IDEMPOTENCE: PASS`.

The same read-only command queried each host's local `diaries-backup-history --json list` independently over SSH, without requiring identical snapshot retention:

| Inventory | mars (source) | backup (receiver) |
| --- | ---: | ---: |
| Distinct Diaries backup identities | 22 | 30 |
| Retained snapshot occurrences | 77 | 42 |
| Identities retained on both | 19 | 19 |
| Identities only on this host | 3 | 11 |

**11 naturally retained receiver-only backup identities were observed:**

- `production/20261015-003023Z`
- `production/20261016-003019Z`
- `production/20261017-003102Z`
- `production/20261019-003106Z`
- `production/20261020-003106Z`
- `production/20261021-003106Z`
- `production/20261022-003107Z`
- `production/20261024-003215Z`
- `production/20261026-003102Z`
- `production/20261027-003055Z`
- `production/20261028-003103Z`

The host-history comparison concluded `0050 HOST-HISTORY COMPARISON: PASS`; the combined operation concluded `0050 FINAL OPERATIONAL CHECK: PASS`.

The earlier live verification accepted schema-2 full-content checking of **128 files** for `production/20261116-003112Z` at receiver snapshot `20261116-150008Z`; receiver local Diaries status was **HEALTHY**, with 30 distinct backups, 42 retained occurrences and 0 manifest conflicts. Corrected reader deployment was `ok=37 changed=1 failed=0` (updated reader only). See the existing corrected-live-verification acceptance report and source log. The 0050 feature fixture separately proved receiver-only discovery, selection and verifier invocation; disposable real schema-2 tests additionally proved integrity and tamper rejection.

**Evidence boundary:** The live 11 receiver-only identities were discovered by manifest/marker inventory. This check did **not** fully content-verify all 11 receiver-only backups. Likewise, 42 occurrences does not imply 42 full file-integrity scans. No snapshot was transferred, pruned, rewritten or restored for this comparison.

## Acceptance decision for next stage

The primary feature requirement is demonstrated in production: a host-local read-only reader on `backup` finds Diaries backup identities absent from `mars`. The receiver command's independent schema-2 full verification has passed on a selected live retained backup. `backup`'s subsequent Ansible reapply is strictly idempotent. Previously completed security, protocol, regression, malformed-marker, conflict and receiver-only fixture tests remain accepted.

Remaining: commit/publish the 0050 Playbooks source; update/publish the `ansible-controller` Playbooks gitlink; commit/publish the Diaries change-control receipts; retain the feature under `in-progress` until explicit formal closure approval. No further destructive or full restore testing is required on this evidence.

## Raw evidence

- `evidence/Step 3/MANGO-STRICT-IDEMPOTENCE-AND-HISTORY-COMPARISON-20261117.txt`
- `evidence/Step 3/FINAL-OPERATIONAL-LOG-SHA256-20261117.md`
- Previously packaged: `reports/RECEIVER-LIVE-VERIFICATION-ACCEPTANCE-20261117.md` and its verbatim deployment/verification logs
