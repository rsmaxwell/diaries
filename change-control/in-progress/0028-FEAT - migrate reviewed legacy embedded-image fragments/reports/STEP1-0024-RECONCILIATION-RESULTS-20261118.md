# 0028 Step 1 — Current inventory and 0024 reconciliation results

**State:** Evidence collection and source-to-catalogue dry-run checks have passed; human review and Step 1 acceptance remain **OPEN**.

## Executed results (18 November 2026)

- Original read-only current-schema inventory: `evidence/Step 1/private/20261118T093606Z/`. SHA256 verification passed for all five inventory files. Found **2,329 Fragments**, **85 Images**, **72** unreviewed legacy Fragments and **72** `<img>` occurrences.
- Structural flags: **141** entries over 82 distinct Fragments: 81 NULL Fragment types and 60 missing direct `page_id` values. All 72 candidates have NULL type (consistent with intentional 0022 legacy state); 50 candidates have no direct Page ID.
- Prepared 0024 input and Page association report: `evidence/Step 1/private/20261118T100019Z-0024/`. Five offline preparation tests passed. **22** candidates have a direct Page and a Marquee with a Page (both populated, no mismatch reported by the helper); **50** have neither direct Page nor a Marquee. This is not a verified Page foreign-key check.
- 0024 production Files-root reconciliation ran in **dry-run**, using the existing deployed responder JAR in a disposable Compose container. No database updates, catalogue writes or service restarts. All six 0024 evidence hashes verified and production scratch evidence was removed following verified transfer to `mango`.
- 0024 source-to-catalogue cross-reference: **71 `MATCHED_ONE_IMAGE`** with `UNIQUE_LOCAL_SUFFIX` and `CATALOGUED_MATCH` file integrity; **1 `AMBIGUOUS_PATH`** also with `UNIQUE_LOCAL_SUFFIX`. **No `EXACT` matches**.
- All occurrence identities and source hashes were rechecked between the frozen inventory and 0024 cross-reference; they agree. Both derived and 0024 `SHA256SUMS.txt` manifests passed re-verification.
- On `pluto`, Compose health check showed five healthy services including `rsmaxwell/diaries-responder:0.0.9-build-84`; the historical 0024 wrapper was not installed. The Java dry-run nevertheless succeeded.

## Interpretation and limitations

**None of the 71 suffix-based catalogue matches is an approved migration mapping.** Each needs independent review of the exact original source, mapped relative path, Image ID and current checksum. The one ambiguous source must be explicitly resolved or left legacy/deferred. The 50 candidates with neither `page_id` nor a Marquee must receive explicit ownership treatment before any write. Do not create guessed Page assignments.

The source bundle contains a historical 0022 review ledger, but the *generated historical 0022 candidate CSV* has not been recovered or independently reconciled. No historical 0022 drift result may be claimed yet. The current 0024 dry-run input is **derived from 0028**, not that historical candidate CSV.

The new `tools/step1_make_review.py` prepares a **private review-aid CSV and inert HTML dossier** from the two already collected evidence sets. It never fills approval columns or rewrites the frozen source. It validates evidence manifests, 0028-to-0024 source hashes, candidate coverage, catalogue metadata and file checksums. `review_blockers` call out suffix matching, Page unknowns and other exceptions. This is **not** a migration manifest, a conversion recommendation or a validated Page FK assertion.

## Step 1 still needed

1. Run the offline private review assembler; verify its newly generated evidence hashes and review the 72 rows. Do not commit private files.
2. Independently validate all proposed suffix mappings; resolve the ambiguous source or approve `DEFER`/`KEEP_LEGACY` as appropriate.
3. Determine appropriate disposition and Page ownership for 50 Page-less candidates, considering the existing explicit Page/type contract; no speculative repairs.
4. Recover/historically compare the original 0022 candidate CSV if available; otherwise record the evidence gap and agree on the required disposition coverage.
5. Produce and explicitly sign off all 72 Fragment and occurrence decisions, text/caption allocations, hashes and reconciliation report. **Step 1 remains OPEN until acceptance evidence is approved.**
