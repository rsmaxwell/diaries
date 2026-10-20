# Step 10 — Fresh operator acceptance capture

**Status: OPEN. No deletion approved.**

From Cygwin in the Diaries repository root:

```bash
bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tools/step10-capture-from-cygwin.sh"
```

This executes read-only commands via SSH on `mars` and writes outputs to `evidence/Step 10/fresh-preflight/` (including `SHA256SUMS.txt`). No remote scripts, temporary Linux files, Snapper deletion, or approval files. Inspect all outputs before any operator decision.

## Acceptance requirements

1. Compare text/JSON plans; confirm the intended *single* ID remains WOULD-DELETE, and confirm no new anomalies.
2. Cross-check the candidate ID/date against Snapper CSV and `btrfs subvolume show` and verify `ro=true`.
3. Check native status and timer state, protection records, source mapping, restore coverage, current jobs and replication/receiver health as appropriate. `mars` manager preflight is not an independent receiver-health check.
4. Record the operator's explicit APPROVE or REJECT decision, candidate ID, rationale, timestamp, stop conditions, recovery expectations. Do **not** create an approval file or invoke `legacy-delete --execute` in Step 10.
5. Treat candidate `19605` as a proposed review subject only; NOT approved.

The capture of running jobs is point-in-time and **cannot** reserve a later Step 11 maintenance window. A fresh job/concurrency check must be repeated immediately before any subsequent pilot.
