# 0032 Step 2 close-out — Approve the final tooling disposition and archive layout

## Result

**COMPLETE — 2026-10-03.**

All **60** Step 1 candidates now have an approved final classification and destination. There are no pending decisions.

## Approved totals

```text
ARCHIVE          43
PROMOTE/RENAME   17
TOTAL             60
```

## Key decisions

1. all `scripts/windows/0031-step*` migration/evidence harnesses are historical and will be archived under the completed 0031 feature;
2. lasting ImageFragment smoke helpers and 0031 storage/backup/diagnostic assertions are retained only through behaviour-oriented live names;
3. the Windows and Playbooks `verify-0031-step16.py` final gates are historical aggregation gates and will be archived;
4. all seven 0031 production `stepN-*` helpers will be archived under 0031 and removed from the Playbooks sync tree and `pluto` later;
5. `migration0024ImageCatalogue.sh` is explicitly decision B — completed migration tooling — and will be archived under completed 0024, then removed from production deployment;
6. 0026 Step 14 artifact-verifier tooling is archived under completed 0026, while the reusable ImageFragment reader smoke workflow is promoted to neutral names;
7. the archive layout separates Diaries and Playbooks validation sources to prevent filename collisions and does not duplicate bulky runtime evidence.

## Safety statement

Step 2 is planning/evidence only. No live source path, deployed production script, database, Files root, retained MQTT state or running service has been changed.

## Handoff to Step 3

Step 3 can now preserve the historical tooling into the exact destinations in `ARCHIVE-MAP.md` and record fingerprints/source metadata before any live cleanup begins. It must use `FINAL-DISPOSITION.csv` as the authoritative per-file contract and must not delete/rename a live file until its required archive copy (where specified) exists and hashes correctly.
