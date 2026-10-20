# 0037-FEAT Step 11 — Pre-execution review

**Status: OPEN — capture only; one approved candidate; deletion not authorised by this document.**

Operator-authorised candidate: host `mars`, source `@data`, Snapper config `@data`, snapshot ID `19605` (2026-09-28 00:00:38 UTC). Previously observed Btrfs subvolume ID `20165`, UUID `489332dc-3b48-eb40-b59a-d9bd86cc9915`.

## Required gate

1. Capture from Cygwin: `bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tools/step11-preflight-from-cygwin.sh"`.
2. Confirm host `mars`, UTC time, manager version, plan classification `WOULD-DELETE` for **only the approved ID** and exact Snapper timestamp, subvolume ID, UUID, and `ro=true`.
3. Inspect the native snapshot inventory for incomplete sets, prune dry-run, checkpoint holds, and replication pins reported by manager status. Compare with the fresh `backup` received history and receipts. Note that timestamp agreement alone is not proof of a restore.
4. Inspect concurrent processes and failed units; stop if anything unexpected is active. Decide whether existing recovery evidence suffices; do not claim a restore was tested during this step.
5. Make a separate same-session **GO/NO-GO** decision before creating any root-owned deletion approval. Never approve another ID by implication.

No active approval file, enabled approval JSON, or destructive command is included. The existing feature `reports/STEP11-SINGLE-SNAPSHOT-PILOT-RUNBOOK.md` describes the later execution gate. Preserve evidence under `evidence/Step 11/pre-execution/`; do not move reports into the Playbooks production tree. Only following explicit review of these captured outputs can the controlled single-ID deletion be considered.
