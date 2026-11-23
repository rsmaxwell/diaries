# 0052-DEF — Implementation steps: correct catalogue image content errors

**CLOSED — 23 November 2026.** Steps 1, 2 and 3 closed with the content-owner’s explicit approval. The existing acceptance qualifications and the mandatory 0028 handoff are recorded in [formal closure](reports/FORMAL-CLOSURE-20261123.md).

**Status:** CLOSED — 23 November 2026 (owner approved; Steps 1–3 closed; 0028 dependency remains open).

**Decision (23 November 2026):** Replace the incorrect Hermitage content **in existing catalogue Image 18 (Option 1)**, retaining Image ID 18, its canonical relative path and all consumers. Do not create a new Image record, redirect Fragment 598 to a new Image ID or delete the original entry. The Whitley Park correction concerns Image 3; select and approve the correct replacement after confirming all consumers.

**Existing Step 1 evidence:** `reports/STEP1-INVENTORY-20261122.md` records the three named Whitley Park PNG candidates, pre-change NAS Whitley hash and earlier Hermitage evidence. Preserve this report and `evidence/README.md`; supplement rather than repeat or overwrite the accepted read-only findings.

Implement the Whitley Park and Hermitage corrections after completing the read-only inventory, recording the approved Whitley Park candidate and reverifying the already selected Hermitage PNG. Keep before/after manifests and rollback actions distinct for each image and environment. Consolidate functional and integrity verification rather than introducing unnecessary intermediate deployment stages.

## Step 1 — Inventory and approve the replacement

- Record the current Windows Diaries parent checkout branch/revision/status and application submodule revisions; preserve unrelated work. Record relevant `pluto` deployment and backup identities.
- Inventory the source directory over the NAS, using the already identified `img2840-whitley-park-map/` candidate directory (`map2026-11-21_085923.png`, `whitley-park-historical-map.png`, `whitley-park-modern-map.png`) and current `img2840-image-map-whitley-park.jpg`; capture SHA-256, MIME type, resolution, and full-size visual comparisons. Do not assume a prefix is a complete filename.
- Read-only trace `fragment` entries 84, 2332 and 2333, especially fragment type, image ID, HTML embedded image URLs, page/date ownership, Marquee relationship and click URL; read the Image catalogue entry for ID 3 and locate the **actual served file**, thumbnails/derivatives, and any additional fragments that share Image ID 3.
- Review the historical/modern map context with the content owner and record the selected file and expected affected consumers. Identify whether replacing the shared Image 3 is appropriate or if a narrower file/reference correction is required.
- For Hermitage, recheck the selected `img2900-image-hermitage.png` against the filename, PNG format, dimensions, size and SHA-256 recorded in the README. Inventory its source, processed metadata image and actual served Files copies in production and development; do not use one of the superseded replacement variants.
- Resolve the Hermitage Image row by its canonical relative path in each database; record its ID, actual metadata fields, version, all fragment/legacy references, derived images and retained Image projection. Verify the client URL, responder/static routing and mounted Files path. Do not infer IDs or copy one environment's database identity into another.
- Identify affected 0028 frozen checksum/review expectations and record the required review refresh without changing historical evidence or running migration. Record baseline hashes for St Isaac and the separate Jordan Staircase image to demonstrate they remain untouched.

**Evidence:** dated inventory and candidate-choice report under `reports/`, raw read-only logs and hashes under `evidence/`.

## Step 2 — Apply the controlled correction

- Identify the exact database/Files pair and verify the applicable recovery points for each environment. Preserve the original file, catalogue row and any affected references for each correction, with hashes and a rollback record.
- Plan a controlled in-place repair unless the deployed responder provides a supported replacement operation. The local responder upload path rejects an existing catalogue path even with overwrite enabled. Rehearse in development before writing to production. For each image, verify the expected old file hash and catalogue row/version immediately before writing, coordinate concurrent writes, stage and verify the replacement, and preserve the existing Image ID where applicable. Document and rehearse recovery for a failure between file replacement, database commit and retained publication, including restoration of the prior file and metadata and republishing the restored state.
- Replace the Hermitage served image with the verified 935,720-byte PNG in each environment's own Files store, using the rehearsed procedure. Update **the existing catalogue Image 18 row in place**, including its applicable checksum, size, MIME/format, dimensions and version/cache fields consistently with the file; **retain Image 18 ID, relative path and all existing consumers**. Do not create a new catalogue image, redirect Fragment 598 to a new ID or delete Image 18. Stop and seek an explicit decision if live inventory conflicts with the assumed Image 18 identity. Record file byte size in the manifest and update only metadata fields present in the deployed schema.
- Reconcile committed Image metadata with responder state and retained MQTT publications through the supported refresh/replay path; regenerate any required derivatives and invalidate stale caches. A successful file copy alone is not evidence of catalogue completion. Preserve the already-correct source image and leave St Isaac and Jordan Staircase untouched.
- Preserve legacy fragment HTML except for the specific approved image URL/content change. Preserve all fragments' transcription, ordering, optional links and Marquees. Do not run the separate 0028 migration.
- Record exact files, catalogue/database records, commands, hashes and whether any cached thumbnails or retained topics were refreshed.

**Evidence:** before/after manifest, execution log and rollback record under this defect.

## Step 3 — Consolidated acceptance and closure

- Confirm on **20 March 1828** that Fragments **84, 2332 and 2333**, as applicable to their actual references, present the approved map; confirm Image ID **3** thumbnail/full-size rendering and existing text/highlight/link behaviour in the production Editor and public Reader.
- Verify the approved map bytes over the actual HTTP URLs and compare the applicable catalogue checksum and retained MQTT metadata. Check browser refresh and confirm the observed set of changed Image ID 3 consumers matches the approved inventory.
- For Hermitage, verify the actual HTTP response bytes match the selected SHA-256 in both environments, and catalogue metadata and retained Image state agree. Check the catalogue preview and every affected Editor/Day Reader/public Reader presentation after refresh/reconnect, including optional link and Marquee behaviour. Confirm unchanged IDs, references, ordering and the two unrelated image hashes.
- After the in-place Image 18 repair is verified in production, resume the preserved **0028 V2 draft (91) checkpoint**, review **Fragment 598** against the corrected catalogue Image 18 in the Editor and Reader, and only then enter its final confirmation through 0028's normal workflow. Preserve earlier frozen evidence and do not represent the content correction as migration approval.
- Recheck application health and relevant logs. Capture user-approved screenshots or image identity checks without copying confidential content into public change-control evidence.
- Obtain explicit owner acceptance, record before/after proof, and only then mark this defect CLOSED and move it from `in-progress/` to `complete/` using normal change-control practices.

**Do not** claim Steps 1–3 passed until their execution logs and owner acceptance exist.
