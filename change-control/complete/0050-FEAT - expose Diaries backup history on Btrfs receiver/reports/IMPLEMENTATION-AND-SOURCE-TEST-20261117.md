# 0050 — Source implementation and consolidated regression results

**Date:** 2026-11-17 UTC  
**State:** SOURCE IMPLEMENTATION TESTED — NOT DEPLOYED; STEPS STILL OPEN.

## Implemented design

- `diaries-backup-history.py` now accepts a `diaries_history` reader-only configuration when `mode=receiver` and insists that the Btrfs snapshot-manager's `verification.required` remains **false**. Source mode continues to use the existing `verification` configuration and CLI semantics.
- Received snapshot root and `@data` inventory path must be canonical, local and non-symlinked; individual marker and dataset paths must resolve within their own received occurrence. Missing/damaged marker, unsafe symlink, invalid manifest hash and conflicting identity retain warnings/errors and nonzero health.
- The receiver manager template adds only read-only `diaries_history` metadata. Existing lock, receiver state, checkpoint holds, retention and pruning settings are retained.
- A dedicated Ansible task installs the **same shared** `diaries-backup-status`, `diaries-backup-history`, and independent schema-2 verifier on the receiver. It is conditional on existing receiver manager/retention installation; it does not alter the 0041 dedicated service accounts or add sudoers. The source's existing snapshots role continues owning its history/verifier installations.
- `diaries-backup-status.py` has only a neutralized docstring; its JSON schema, fields and exit behaviour are unchanged.

## Tests performed in disposable local source bundle

| Test suite | Result |
|---|---|
| 0050 receiver-only/source fixture | PASS, 9 tests |
| 0050 actual production schema-2 verifier in received-generation fixture | PASS, valid bytes accepted; tampering rejected |
| 0050 permanent installation/defence contract | PASS, 4 tests |
| 0049 management regression | PASS, 19 tests |
| 0041 dedicated service security regression | PASS, 8 tests |
| Agreed-parent replication tests | PASS, 25 tests |
| 0035 Diaries history source regression | PASS |
| 0049 Diaries-only status regression | PASS |
| 0040 receiver retention regression | PASS, 17 tests |
| 0040 source prune cap regression | PASS |
| Python byte compilation and YAML parse of relevant task files | PASS |

All raw outputs are captured in `evidence/Step 2/LOCAL-SOURCE-AND-REGRESSION-20261117.txt`.

**Limitations:** the local test harness does not have Ansible installed, live inventory/secrets or access to `mars`/`backup`; no Ansible syntax check, `--check`, deployment, health-readback or idempotence has been run. Real receiver data may include incomplete/old verification markers; they should generate warnings/degraded status, not silently disappear. Ansible's default inventory and vault file must be used on mango for validation and deployment. Do not mark Step 2 CLOSED until evidence is accepted.

## Next action

Apply the Playbooks ZIP to `/home/richard/ansible-controller/playbooks` via Beyond Compare 4. Run source tests and receiver-limited Ansible syntax/check on `mango` after recording branch, HEAD and dirty state. Validate the actual received marker and schema-2 dataset layout read-only before applying any deployment. Then deploy the single coherent change through `btrfs-replication.yaml --limit backup` and verify all receiver commands before considering acceptance. No backup transfer, prune or restoration is necessary.
