# 0032 Step 8 - acceptance matrix

| Acceptance criterion | Status | Evidence / decision |
| --- | --- | --- |
| `scripts/windows` contains no completed 0031 `0031-step*` operator directories | PASS | Step 4 after inventory; Step 8 `BEFORE-AFTER.md`; final `verify-live-script-policy.py` PASS |
| Playbooks synchronized production source contains no retired 0031 `stepN-*` migration/control scripts | PASS | Step 5 after inventory; final production-deployment-contract validator PASS |
| `pluto` contains no stale deployed retired helpers | PASS | Step 6 `PLUTO-SCRIPTS-POST.txt`, `DIFF.md`, `VERIFICATION-OUTPUT.txt` |
| Supported start/stop/status/log/shell, backup/restore and storage-safety commands remain present/documented | PASS | Steps 4-7 source documentation and Step 6 deployed inventory |
| Every removed script is archived or explicitly justified | PASS | Step 3 archive manifest/hash evidence; final 60-row disposition |
| Permanent regression coverage protects behaviour rather than retired feature structure | PASS | Step 4/5 promoted validators; Step 7 recurrence guards; final host/source regression PASS |
| `migration0024ImageCatalogue.sh` disposition is explicit | PASS | Step 2 decision B; Step 3 0024 archive; Steps 5/6 source/deployed removal |
| Cleanup changes no database rows, schema, mutable Files bytes or retained MQTT state | PASS | Cleanup scope plus Step 6 unchanged production config/selectors and healthy services; Steps 7/8 are source/evidence-only |
| Full relevant Diaries and Playbooks regression checks pass after cleanup | PASS | `DIARIES-HOST-REGRESSION.txt`: Windows/source guards, 11 Node tests, Gradle Java tests and Angular production build all pass. `PLAYBOOKS-HOST-REGRESSION.txt`: all three permanent validators and native `ansible-playbook --syntax-check diaries.yaml` pass. |
| Permanent guard/convention detects future completed-feature accumulation | PASS | Step 7 Windows live-script guard + production deployment-contract recurrence test |
| Feature close-out records exact before/after inventories for development, Playbooks source and production | PASS | `BEFORE-AFTER.md` plus Steps 1/4/5/6 inventories |

## Decision

**11 of 11 acceptance criteria are evidenced and PASS.** Step 8 is complete and 0032 is approved for movement from `change-control/in-progress/` to `change-control/complete/`.
