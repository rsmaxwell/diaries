# 0028 Step 1 — Interim production inventory findings (18 November 2026)

**State:** Step 1 OPEN; production inventory complete, read-only 0024 reconciliation pending.

## Verified execution evidence from terminal logs

- Windows and mango parent revision: `f6af92c703207557e2c25a469a60fbfabf8b5088`. Windows parent working tree clean; `mango` has unrelated untracked directories for 0042, 0043 and 0044. Preserve them. `mango` submodules uninitialised; no submodule update attempted.
- Read-only collector at `evidence/Step 1/private/20261118T093606Z`: 2,329 Fragment rows; 85 Image rows; 72 legacy candidate Fragments and exactly 72 `<img>` occurrences.
- `SHA256SUMS.txt` for five source inventory files verified on mango. The five existing `test_step1_inventory.py` offline tests passed.
- 141 reported exception entries, affecting 82 distinct Fragments: 81 NULL types and 60 missing explicit Page IDs.
- All **72** candidates have NULL type; **50** also lack explicit Page ID; **22** have a populated direct Page ID. None has zero exception entries.
- On `pluto`, five production Compose containers are healthy, including `diaries-responder:0.0.9-build-84` and `diaries-client:0.0.9-build-76`. The old `scripts/migration0024ImageCatalogue.sh` wrapper is missing; responder JSON configuration is present.

## Interpretation

The *0022 design* intentionally left embedded-image candidate types NULL until feature 0028 resolved each fragment. Therefore `UNEXPECTED_FRAGMENT_TYPE` is a **collector flag** rather than, by itself, evidence of corruption for these 72 rows. There remain nine other NULL-type rows not in the 72 candidate group; they are outside the automatic candidate set and should not be altered without separate review.

The 50 candidates missing direct `page_id` require resolution. The supplied collector snapshot includes zero/one/multiple Marquee associations and their `page_id`, so a **read-only aggregate classification is possible without repeating the production SQL inventory**. A Marquee Page ID is a potential link, not validation that the referenced Page row currently exists. The new helper produces this aggregate without disclosing private IDs.

The 0024 Java tool has a read-only `dry-run` entry point and accepts an optional legacy 0022-style candidates file. The feature-specific tools prepare a structurally compatible current-candidate input, run 0024 read-only inside the deployed responder image and bring resulting evidence back to this feature directory on mango. **Do not claim historic 0022 candidates were recovered**, and do not run `apply` even if the 0024 dry-run produces proposed Image CREATE rows.

## Next acceptance work

1. Apply/test the new feature-specific tools; use frozen inventory to produce current 0024-compatible candidate input and Page association breakdown.
2. Run the existing 0024 Java **dry-run only**, validate current Files-root status/checksums and 72 occurrence cross-reference results.
3. Review missing Page links, unexpected image paths or metadata mismatches, historic evidence drift, decisions for each Fragment/occurrence. No conversion choices are automatic.
4. Sign and hash approved manifest. **Step 1 remains OPEN** until reviewed evidence and dispositions are accepted.
