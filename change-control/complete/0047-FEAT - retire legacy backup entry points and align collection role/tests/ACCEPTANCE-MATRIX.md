# 0047-FEAT — Final acceptance matrix

| Criterion | Evidence | Outcome |
|---|---|---|
| Retire legacy operator interfaces | Guarded Step 1 deletion/rename output; `b04de9e` | ACCEPTED |
| Preserve executable bit for original seven files | Git mode-only commit `833da94` | ACCEPTED |
| Preserve per-path source modes with native rsync, no `--chmod` | `source-modes.json`/regression; 14 verified paths; `dca638c` | ACCEPTED |
| No changed content during corrective filter sync | `.f...p.....` entries only; named-copy-task guard | ACCEPTED |
| Installed configuration identical to 0045 static baseline | `evidence/Step 2/deployment-20261111-160900Z/` | ACCEPTED |
| Second deployment idempotent | collection on `mars`, replication on `mars` and `backup` each changed/failed/unreachable=0 | ACCEPTED |
| Docker signing key and health | unchanged SHA-256, health commands pass | ACCEPTED |
| External caller coverage | 0045 four-host and 27 Jenkins job definitions; SCM/external gaps disclosed | ACCEPTED with residual scope |
| Future fresh-clone permission simplification | 0048-FEAT; depends on 0046 + 0047 | DEFERRED |
| Formal Diaries move/commit/push | Closure command output | PENDING EXECUTION |

No full restore or live replication test was repeated; previously accepted
correctness evidence remains adequate for the source-interface change.
