# 0040-FEAT Step 10 — Backup legacy retirement preflight acceptance

**Date:** 25 October 2026  
**Scope:** `backup` only  
**Decision:** **ACCEPTED for backup**; overall Step 10 remains **OPEN** for `mars` and other planned inventories.

## Authorisation and identities

- Original `backup` inventory comprised **83** numerical Snapper root snapshots under `/.snapshots` and **32** numerical `@data` Snapper snapshots under `/@data/.snapshots`: **115** total.
- Two separately UUID-checked pilot snapshots (one root, one `@data`) were retired first. The remaining **113** were included in a frozen one-off allowlist (`backup-retirement-approved-manifest.json`).
- Manifest SHA-256: `1d25d3095b36fec8ce95cbab062ece9e2d5da2c72431c47eef78af0bbdfc1e64`.
- One-to-one matching of approved paths and UUIDs against the original inventory succeeded; live validation checked 113 targets, 16 permitted Snapper filelists and **zero problems**.
- The retirement tool passed its Python source regression and the initial production **read-only** rehearsal: `PLAN approved=113 remaining=113 completed=0 mode=READ_ONLY`, followed by `NO DELETION AUTHORISED`.
- Native receiver recovery was `CLEAN`. The receiver's native received history and receipts were outside the approved deletion set; native receiver pruning remained disabled.

## Evidence on mango

Located at `/home/richard/0040-step10-evidence/`:

- `backup-before-retirement.txt`, `backup-retirement-preflight.txt`, `backup-retirement-validation.txt`
- `backup-retirement-approved-manifest.json`, `backup-retirement-dry-run.txt`
- `backup-retirement-step10-summary.txt` (summary accumulated after execution)

`backup-legacy-plan.json` is **zero bytes**, because the receiver-mode manager rejected the legacy-plan operation. **Do not cite it as a successful plan.** The independent UUID reconciliation and one-off guarded tool provided the approved backup preflight instead.

## Outstanding scope

This report does not establish completion of the `mars` root snapshot inventory, its deletion allowlist, hold/unique-history assessment, or the full Step 10 acceptance gate. Those remain outstanding unless established by separate evidence. The destructive `backup` operation is reported separately under Step 11.
