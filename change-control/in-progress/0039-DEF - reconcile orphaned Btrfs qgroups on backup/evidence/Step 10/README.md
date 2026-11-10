# Step 10 — Unattended deployment and first cycle — CLOSED (10 November 2026)

Both host-specific timers are enabled/active at 05:30 UTC; installed code and dry runs passed. The **first unattended** 10 November service invocation succeeded on both machines: `mars` removed 14 stale entries and finished at 0; `backup` began and finished at 0. Both exit status 0, no incomplete snapshot sets and the source Diaries backup verification remained valid.

The Windows collector already wrote `scheduled-maintenance-20261110.txt` in this directory. The verbatim uploaded copy is also preserved in `raw-terminal/`. Two newly eligible `mars` stale entries at 07:29 were observed after the 05:30 run; this is not treated as a failed run. A further scheduled cycle is needed for Step 11.

The 0042-FEAT simplified-replication acceptance, now formally CLOSED, verified protected common parent `20261110-030004Z` and unchanged timers/receipts. Keep its evidence under its own completed feature; do not duplicate or rewrite it here.
