# 0028 — Step 1 content review (2026-11-18)

**Status: PROPOSED ONLY; Step 1 OPEN.** This report is a non-private summary of analysis of the source bundle `diaries-sources-20261118-112949.zip`. The original private evidence and individual recommendations are NOT stored in Git by this report. No database or MQTT changes were performed.

## Source and checks

The bundle includes the 2026-11-18 09:36 UTC frozen production inventory, 10:00 UTC 0024 dry-run, 10:15 UTC review worksheet and HTML dossier, 11:02 UTC context triage, and working CSV. The frozen, 0024, triage, and review worksheet hashes verify, and the working CSV is byte-identical to the verified triage CSV. Across all 72 candidates, the original Fragment HTML SHA-256, embedded `src` SHA-256, occurrence identities, and the resolved Image metadata match their evidence records.

**Integrity exception:** The HTML dossier embedded in the **exported source ZIP** has SHA-256 `7027b07d657c4637eaed7ec98eb669278d44146833e96d9e50199d02e576457e`, but its evidence manifest specifies `6cf9a11c205a2763da7fd77b025061d2e6ec5ffe2733ba53d67cfa0a43e79ec0`. The two dossier copies in that ZIP are identical to each other. Its cause is unknown; the 10:15 terminal run verified the original on `mango`. Re-check the canonical `mango` dossier before Step 1 acceptance. Analysis here uses the checksum-verified *frozen fragment HTML*, not the mismatched dossier. Do not silently rewrite historical hashes.

## Confirmed content types and blockers

| Evidence property | Count | Consequence |
|---|---:|---|
| Legacy image-bearing Fragments | 72 | One embedded image each; `type=NULL` was intentionally retained in 0022 |
| 0024 unique Image matches with catalogued file integrity | 71 | All use `UNIQUE_LOCAL_SUFFIX`; **review required**, not exact source URL approval |
| Ambiguous image (also has substantial non-caption prose) | 1 | Recommend `DEFER` until the image and text are resolved |
| Figure with `figcaption` | 69 | Caption markup/text requires explicit allocation |
| Bare image, no caption | 3 | Approve empty IMAGE text or alternative label explicitly |
| Image wrapped in a clickable external hyperlink | 30 | Must preserve external click/URL semantics or explicitly accept/defer change |
| Hyperlinked image with direct Page/Marquee | 22 | Also approve whether the Marquee is a historical anchor and can be removed |
| Hyperlinked image without Page/Marquee | 8 | Also needs authoritative Page ownership |
| Missing Page and Marquee | 50 | 36 have only one date-neighbour Page hint; 14 have multiple; neither proves ownership |
| Stray text outside otherwise simple figure | 2 | Literal quotation mark outside figure: require reviewed text allocation |
| Distinct links in original 0022 historical ledger | 2 | Helpful context only; does not approve conversion |

**No candidate is authorised for conversion.** In particular, all 22 existing Page-owned candidates wrap their image and caption in an external `<a href>` link; the current `diaries-web` `month-reader.peb` and `source-page.peb` render first-class IMAGE media using an unlinked `<img>` plus caption. Do not assume the original click behaviour survives a type conversion. All 50 unowned candidates also require Page resolution. The `ProjectionSnapshot` currently excludes Page-less Fragments from the reader projection; assigning Page ownership may change public visibility and must be reviewed.

## Suggested—not approved—review outcomes

- **71 conditional `CONVERT_TO_IMAGE` candidates:** original content is a single figure+caption or bare image, and 0024 identifies a valid Image. None may be applied until suffix Image ID/path/checksum, target Page, source text/caption/href, and Marquee effects are explicitly approved. A reviewed `SPLIT_MARQUEE_AND_IMAGE` may be preferable where preserving source geometry is required, but a redundant empty MARQUEE must not be created by default.
- **1 proposed `DEFER`:** ambiguous source Image, no authoritative Page, and substantive prose outside the image figure. Do not remove or rewrite its HTML.
- `KEEP_LEGACY` remains an appropriate human choice for images whose original click behaviour, figure markup or Page ownership cannot be preserved.

The separately supplied private proposed-review CSV contains one row per occurrence, all original `review_*` fields unchanged and empty, plus clearly identified `proposal_*` columns with file/page/text/link review blockers. The output is **not** an executable or approved manifest; no values from `proposal_*` should be automatically copied into a migration `apply` manifest.

## Acceptance items still open

1. Verify the dossier hash on `mango`, and investigate/export if it differs.
2. Review all 30 clickable image links: define how their exact target URL and click behaviour are retained or record explicit approved exceptions. Consider a separately designed supported IMAGE link representation rather than silently dropping anchors.
3. Establish authoritative Page IDs from actual Page/source provenance for the 50 orphaned candidates; do not promote date-neighbour hints.
4. Independently review all 71 suffix-based Image resolutions, including visual comparison where needed.
5. Review caption/extra text preservation, particularly the one prose-rich and two stray-quote cases; confirm optional empty text for three bare images.
6. Decide and approve the 22 Marquee deletions versus a well-defined split while preserving source-page geometry and reader behaviour.
7. Produce reviewed disposition and occurrence manifests with reviewer identity, evidence hashes and signed approval. Keep Step 1 **OPEN** until accepted.

## Privacy

Private CSVs, HTML, raw image paths and fragment text remain under `evidence/Step 1/private/` and must not be committed or included in a public ZIP. The newly uploaded *source bundle* contains those private files, despite the feature `.gitignore`. Exclude private evidence from any source bundle intended for wider distribution.
