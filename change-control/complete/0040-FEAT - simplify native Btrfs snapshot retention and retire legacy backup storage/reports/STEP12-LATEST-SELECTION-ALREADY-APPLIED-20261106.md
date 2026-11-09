# Step 12 — Latest selection already present on mango; documentation reconciliation

Date: 6 November 2026  
Status: **OPEN — scheduling not activated**

## Evidence and source identity

- The `mango` Playbooks checkout is on branch `main`, commit `813b7210d08865337770ae821bb9d88529115188`, with four deliberately preserved uncommitted files.
- The latest user terminal diff (`step12-playbooks-merge-analysis-20261106-163058.txt`) shows `choose_next()` already changed from ascending to descending eligible snapshot order. It also shows the corresponding three newest-first tests.
- The reported current Playbooks executable SHA-256 is `cfa8a696b36eb49935d518cfd2c99d38e28fe3fbbfaa7a0faa6618a485e2fd36`. This matches **exactly** the executable in `0040-step12-latest-selection-playbooks-20261106.zip`; no code merge or repeated patch is needed.
- `git diff --check` returned 0 on `mango`.
- The earlier locally checked source suite for that exact newest-first executable completed 20 simplified-replication tests successfully. Repeat the consolidated suite on `mango` before installing; remote tests have not yet been reported.
- The prior installed executable on `mars` and `backup` was SHA-256 `9be64295a6b6807df0fcd33d924b7a6549959f2a03dcab2953dcf0ac77fa6297`. That executable already passed the initial controlled transfer on 6 November; both records advanced to `20261101-150004Z`.

## Documentation discrepancy and correction

The two uncommitted Playbooks READMEs claimed the sender was oldest-first and could perform up to 96 transfers per scheduled invocation using `--max-transfers 1` for the smoke. The current executable instead selects the newest eligible snapshot and transfers one snapshot per `sender cycle`; it has no `--max-transfers` argument. These stale claims must not be used for operator commands. The accompanying docs-only Playbooks package corrects the behaviour and reflects the accepted manual cutover without replacing executable/test changes.

## Operational follow-through

1. Preserve the four uncommitted Playbooks files and review/apply the two documentation updates through Beyond Compare on `mango`.
2. Run consolidated source/protection/prune regressions on `mango`; confirm current source hash and inspect the binary-only Ansible check-mode diff (`--tags simplified-agreed-parent`).
3. Install only the accepted newest-first binary to both hosts with the existing timer stopped. Verify hashes and perform one controlled `sender cycle` on `mars`.
4. Read back and compare source and receiver agreed-parent records, and independently verify the new Btrfs received UUID/read-only flag.
5. Preview and apply `--tags scheduling` to select the simplified service and re-enable the existing 03:30 UTC timer. Verify no receiver prune changes.
6. Preserve all evidence in this feature directory; reconcile the remote mango-only evidence into the authoritative Windows Diaries working copy. Do not mark Step 12 CLOSED until activation and operational checks pass.

No snapshot cleanup, journal deletion, state reset, service activation or remote operation was performed while preparing this report.
