# Step 8 — Host inventory and recurrence diagnosis — CLOSED (10 November 2026)

The existing Windows Cygwin raw baseline files, collected 9 November, are:

- `mars-baseline-20261109-135149Z.txt`
- `backup-baseline-20261109-135152Z.txt`

Both passed, with kernel 6.8.0-147, btrfs-progs v6.6.3 and native `btrfs qgroup clear-stale` supported. `mars` had 656 native stale entries; `backup` had zero. Later exact-ID pending deletion analysis is preserved in `../Step 09/raw-terminal/` and explained by `../../reports/STEP08-10-ACCEPTANCE-RECONCILIATION-20261110.md`.

Do not replace or regenerate the original host baseline logs. Step 8 is closed on the documented diagnosis, not on a claim to have identified an upstream kernel bug.
