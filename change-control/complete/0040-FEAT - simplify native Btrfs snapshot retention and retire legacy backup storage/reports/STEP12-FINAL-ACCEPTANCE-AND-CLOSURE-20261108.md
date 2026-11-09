# 0040-FEAT — Step 12 final operational acceptance and closure

**Date:** 8 November 2026

**Decision:** **Step 12 CLOSED** — simplified replication, interrupted-receive retry protections, independent receiver retention, operational status reporting and guarded legacy executable retirement are accepted.

**Boundary:** **0040-FEAT remains IN PROGRESS.** Steps 13 and 14 remain OPEN.

## Accepted operating state

- `mars` runs `/usr/local/bin/btrfs-simplified-replication sender cycle` under the existing `btrfs-native-push.service` / `.timer` at **03:30 UTC**. The simplified sender and receiver executables match the accepted Playbooks source by SHA-256, and neither the old source executable nor the intermediate agreed-parent runtime is the active sender.
- `backup` uses the simplified receiver and the shared snapshot-manager retention implementation. The receiver-only `btrfs-receiver-simple-prune.timer` is enabled at **04:15 UTC**, with an explicit maximum of **10** deletions per run. The retired legacy-prune unit is absent.
- Agreed parent at the observed acceptance: `20261108-030011Z`, UUID `dcb7bae6-d1b0-824c-9d2d-1f5c7b8a2d58`; prior `20261107-030031Z`, UUID `7778dda5-2b91-8c4e-8b1a-1dd038a3675b`. Source and receiver agreed-parent records and actual receiver identity passed the read-only checks.
- The **first unattended receiver pruning** ran automatically 8 November at 04:15:04 UTC and ended at 04:15:05 UTC with `Result=success`, `ExecMainStatus=0` and `RECEIVER-SIMPLE-DELETED count=0`. The plan had 0 deletion candidates, retained 31 snapshots, preserved 27 historical receipts with none orphaned, and retained two historical holds. Zero deletions was the correct outcome.
- On 8 November, after the 25/25 simplified regression run and additional Playbooks checks, the updated runtime was deployed successfully. The new `sender status` and `diaries-backup-status` returned verified source/receiver status without changing either parent record. Both scheduled timers remained enabled and active.
- Exactly **39** obsolete code files were removed from `mars` and **35** from `backup` after read-only path, SHA-256 and dependency checks. The deployed source and receiver remained healthy. Both rollback archives were checked for SHA-256, TAR members, mode and owner. No data, snapshots, agreed-parent records, checkpoint holds or receipts were targeted.

## Resolved incident during retirement

The first guarded `--apply` invocation **returned a nonzero status after removing all 74 files** because its final audit treated the expected absence of `btrfs-legacy-prune.timer` as a command failure. The original failure log remains intact. A separate read-only verification confirmed all files absent, old timer `LoadState=not-found`, backup-status health and both active timers. The corrected tool then used receipt-only `--finalize`, revalidated the original TAR members/hashes and produced the missing completion receipt. **No deletion or restoration was repeated.**

## Evidence index

All paths below are relative to this feature directory. The authoritative permanent copy is the Windows Diaries Git repository; final evidence was also synchronised to `mango`.

| Gate | Evidence | Outcome |
|---|---|---|
| Accepted source/disposable real-Btrfs design | `reports/STEP12-SIMPLIFIED-SOURCE-AND-REAL-BTRFS-ACCEPTANCE-20261105.md` | ACCEPTED |
| First unattended receiver pruning | `evidence/Step 12/raw-logs/step12-first-unattended-prune-20261108-075908Z.txt` and `.json`; `reports/STEP12-FIRST-UNATTENDED-RECEIVER-PRUNING-ACCEPTANCE-20261108.md`; `evidence/Step 12/receipts/first-unattended-prune-formal-acceptance-20261108.json` | ACCEPTED |
| Simplified source tests and deployment | `evidence/Step 12/raw-logs/step12-legacy-retirement-source-verification-rerun-20261108.txt`; `step12-legacy-retirement-deployment-20261108-083053.txt` | PASS |
| Candidate identity and references | `evidence/Step 12/manifests/legacy-code-retirement-manifest-20261108-083525Z.json`; `evidence/Step 12/raw-logs/step12-legacy-reference-audit-rerun-20261108-085024.txt` | PASS — 39 + 35 exact candidates |
| Original guarded execution (historical failure) | `evidence/Step 12/raw-logs/step12-legacy-retirement-execution-20261108-085903.txt` | Files removed; final audit failed |
| Independent post-removal check | `evidence/Step 12/raw-logs/step12-legacy-retirement-postfailure-check-20261108-090527.txt` | PASS |
| Corrected receipt-only finalisation | `evidence/Step 12/raw-logs/step12-legacy-retirement-finalisation-20261108-091629.txt`; `evidence/Step 12/rollback/legacy-code-retirement-20261108-085914Z.json` | PASS |
| Verified rollback copies | `evidence/Step 12/rollback/legacy-code-mars-20261108-085914Z.tar` and `legacy-code-backup-20261108-085914Z.tar` | SHA-256 + members verified |

### Rollback TAR integrity

| Host | Members | SHA-256 |
|---|---:|---|
| `mars` | 39 | `c7c900e99a8dd552a1966cd2ed5185dc38e57a41efd264e453fdd783cf26b638` |
| `backup` | 35 | `7769d82d75a1c4f7bad2428a8df3d247070a8340403a7890c39d566eb892648c` |

## Git promotion and reconciled state

- Playbooks main implementation and retention: `6553ace`; final simplified read-only status and installer gates: `e5ae755` (pushed).
- Diaries original acceptance and manifests, correction/test receipts, and final archived rollback evidence culminated in `a719542` (pushed).
- Windows Diaries and `mango` execution copy both observed at `a719542`, with the six final archive/log/receipt copies reconciled by identical Git object hashes.
- The latest source ZIP on its own is not evidence of post-deployment Git state; Git revisions and terminal logs listed here establish acceptance.

## Decision and remaining work

**Step 12: CLOSED, 8 November 2026.** Accepted correctness evidence is sufficient. Do not repeat expensive restore, manual A→B replication, scheduled receiver-pruning execution or code retirement without a new material reason.

**Step 13: OPEN.** Reconcile final role/configuration and inventory (including obsolete comments, retained maintenance tools and editor backups) without changing accepted behaviour; update operational runbooks and final promotion/rollback ownership and preserve the completion evidence.

**Step 14: OPEN.** Independently verify final feature-wide criteria (no recreated native root snapshots or legacy trees, `@data` histories and holds intact, capacity/Btrfs status where required, unattended health and configuration idempotency), record an explicit overall closure decision and move the feature only after acceptance. The 0041-FEAT dedicated replication-user hardening is not part of these gates.
