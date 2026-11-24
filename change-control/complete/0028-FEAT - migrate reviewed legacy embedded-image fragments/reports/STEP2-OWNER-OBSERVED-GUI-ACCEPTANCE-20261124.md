# 0028 — Step 2 owner-observed GUI acceptance status

**Prepared:** 24 November 2026. **Status: most visual checks PASSED; one preserved-link click test OPEN; formal Step 2 closure not declared.**

This report distinguishes real observed behaviour from code-level inference or future tests. It does not authorise a production apply.

## Passed observations (isolated migrated database / Angular Editor and Reader)

- 71/71 reviewed conversions and one DEFER (Fragment 1564) passed restored PostgreSQL 18 rehearsal on 23 November. Failure injection rolled back one date while preserving prior committed dates. Resume, postflight, repeated apply/idempotence, and unrelated-entity fingerprint checks passed. Evidence: `evidence/Step 2/private/20261123T185712Z-isolated-db-rehearsal`.
- 71/71 Fragment MQTT topics and 22/22 Marquee identities/associations passed isolated responder replay; Reader HTTP readiness and representative image URLs passed. Evidence: `evidence/Step 2/private/20261123T195519Z-mqtt-reader-replay`.
- Forty-one original page scans were privately staged with SHA-256 verification; `img2839` and `img2840` bytes matched via the isolated HTTP proxy. Original manuscript and selected Marquee highlighting were independently visually confirmed by the owner.
- The owner confirmed the three Whitley Park images are **separate production Fragments**: 84, 2334 and 2332; not a migration duplicate. Preserve all three.
- Isolated Editor's MQTT v5 WebSocket, runtime configuration and source-page routing passed. Its rehearsal-only JWT Base64 correction was applied, and the owner confirmed sign-in worked using an existing account. No production authentication change occurred.
- Owner confirmed navigation among Pages/Fragments and Marquee highlighting work.
- Owner's 24 November screenshots independently confirmed converted IMAGE fragments: **598 (Hermitage, Page 752, Image 18)**; **606 (St Isaac's Church, Page 755, Image 25)**; **1251 (White Swan at Alnwick, Page 893)**. Image, caption, source manuscript and surrounding chronology looked correct.

## Still open or separately tracked

- **Preserved image hyperlink click:** Fragment 1251 includes a reviewed original external link, but a successful Ctrl+click / destination check has not yet been reported by the owner. Do not mark this check passed simply because the image renders or 30 preserved link values passed the MQTT comparison.
- **0053-DEF:** The owner reproduced a general Editor lock-release failure on non-migrated transcription Fragment 1252: undo/delete back to saved text leaves a lock until navigating away. Two-session lock acquisition and navigation unlock worked. This defect is separately registered and intentionally **not** a 0028 conversion blocker; do not mark the undo test passed or change 0028 migration code.
- No isolated scratch Save/Delete run is claimed; do not require it unless explicitly added to acceptance scope.
- Step 1 formal signoff, Step 2 formal closure, current production freshness and production approval remain separate open gates.

## Concluding interpretation

The already-executed database, MQTT, Reader and representative Editor evidence supports the **71-conversion in-place implementation**. It does not yet support a claim that production has been migrated or that every interactive GUI case passed. The exact 71/1 manifest and all accepted media/Marquee link identities remain unchanged; do not initiate another review cycle without new source drift.
