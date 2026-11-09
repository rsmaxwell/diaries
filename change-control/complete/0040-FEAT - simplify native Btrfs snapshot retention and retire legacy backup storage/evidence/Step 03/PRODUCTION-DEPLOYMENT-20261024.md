# 0040-FEAT Step 03 — Production deployment verification, 24 October 2026

**Decision: ACCEPTED for non-destructive deployment/runtime verification only. Step 3 remains OPEN.**

This report is an index to operator evidence and conclusions. The supplied logs were reviewed, not bundled here. The supporting detailed evidence and caveats are in `README.md` in this directory.

| Verification | Observed result |
|---|---|
| `mango` Python AST syntax | Six native Btrfs Python scripts passed |
| Initial check-mode safeguard | Failed because read-only grep was skipped; installed wrapper proved legacy phase absent |
| Safeguard remedy | Add `check_mode: false` to read-only inspection; keep real assertion |
| Final Ansible check/diff | `mars ok=15 changed=4 failed=0`; `backup ok=20 changed=3 failed=0` |
| Real Ansible deployment | `mars changed=4 failed=0`; `backup changed=3 failed=0` |
| Second real Ansible run | Both hosts `changed=0 failed=0` |
| Native script SHA-256 | All four deployed source/installed comparisons PASS |
| Snapshot manager SHA-256 | Source/`mars`/`backup` identical: `fe3fc7a9298f8a56b0a9f2b6e0197eddc64fe0142a496e19270714d5b7569f2c` |
| `mars` native push timer | `enabled`, `active` |
| `backup` manager/retention configs | Both `mode=receiver`, `receiver_prune_enabled=false`; checkpoint holds required in manager |
| Recovery | `CLEAN`, `authorizes_repair=false` |
| Production receiver inventory | 20 verified of 20, `problems=0`; newest `20261024-030038Z` |
| Mandatory historic checkpoint receipts | `20261013-171228Z` and `20261018-165453Z` verified; Ansible hold assertions pass |

**Important qualification:** installation diff included previously developed functional Step 3 code, not just comments. A new native snapshot had been received unattended by 03:00 UTC; this observation is not evidence of a new user-invoked send/receive test *after* the deployment. No production deletion or prune activation was performed. The production trusted source-held deletion session and recovery acceptance remain outstanding.

**Source traceability:** Diaries revision `ab14f43f3604eeb31cfb8a6c2ce6a416c123eddc`, Playbooks observed revision `80eed96482628ef09050e3b9e4efc59c18e46963` before/at checksum inspection. Reconcile the check-mode one-line fix's final Git commit when formally recording the promoted baseline.

**Next:** Review current Playbooks source and pending Step 3 parent-UUID regression evidence; complete bounded cross-host coordination and disposable adversarial tests before any separate activation gate.
