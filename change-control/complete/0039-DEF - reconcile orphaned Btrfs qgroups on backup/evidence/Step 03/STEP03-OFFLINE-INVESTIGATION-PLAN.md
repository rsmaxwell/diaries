# 0039-DEF Step 03 — Offline investigation planner

**Status: IMPLEMENTED LOCALLY / regression verification pending on operator source; Step 03 remains IN PROGRESS.**

The planner `plan-qgroup-investigation.py` is a **non-executable, offline, read-only** report of historical unmatched unlimited level-zero qgroups. It consumes a previously captured `--full-manifest` JSON, independent filesystem identity text, and the accepted offline safety assessment JSON. It revalidates the manifest with the existing `validate-qgroup-manifest.py`, independently checks the assessment identity/fingerprint, dispositions, protected IDs, counts and ordered sample, and emits only a bounded sample (default 20, maximum 100). It refuses any inconsistent input.

Its `deletion_authorized`, `deletion_commands`, and `executable_actions` are always `false`, `[]`, and `[]`. `unmatched-investigation-only` is **not** a deletion eligibility designation. Limited qgroups, active and protected snapshots, pending deletes, related qgroups and ambiguous qgroups are excluded from the sample. A saved inventory is non-atomic and may be stale. Receipt validity, holds, relationship completeness and live identity remain **unproved**.

Run from **Windows Cygwin** after using Beyond Compare to apply the package, with paths to the existing Step 03 files determined locally (do not guess or recapture). Example invocation:

```bash
python3 'change-control/in-progress/0039-DEF - reconcile orphaned Btrfs qgroups on backup/evidence/Step 03/plan-qgroup-investigation.py' \
  --manifest "$MANIFEST" --identity "$IDENTITY" --assessment "$ASSESSMENT" \
  --expected-host backup --expected-uuid b915f967-7cb4-4c14-b11b-f52209637a22 \
  > "$OUTPUT"
```

Only `OUTPUT` is created by shell redirection; the program never writes files. No production Btrfs commands are invoked. Do not convert the sampled IDs into destructive commands. Future work requires a separately approved, exact-candidate live verification and execution design, bounded review, protected replication/receipt validation and stop conditions.

**Previously accepted evidence:** Gates A–D on disposable `mango` Btrfs passed and SHA256 evidence was verified in Cygwin. Those results do not authorise production deletion. This addendum does not mark Step 03 CLOSED.
