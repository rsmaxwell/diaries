# 0052-DEF — Correct catalogue image content errors (Whitley Park and Hermitage)

**CLOSED — 23 November 2026.** Steps 1–3 accepted and formally approved by the content owner. See [formal closure](reports/FORMAL-CLOSURE-20261123.md). The public Reader omission of legacy Fragments 84, 598, 599 and 600 is accepted **only pending 0028-FEAT migration and post-migration visual verification**.

## Type / status

- **Type:** Defect (incorrect diary image content).
- **Status:** CLOSED — 23 November 2026 (owner approved; Steps 1–3 closed; 0028 dependency remains open).
- **Priority:** Medium — user-visible factual/content error.
- **Owner/review:** Diaries content owner approves Whitley Park replacement and accepts both final visual results.
- **Agreed implementation (23 November 2026):** Correct existing **Image 18 in place**; retain its catalogue entry, identity, canonical relative path and consumers rather than creating a new Image ID. The final Whitley Park replacement must still be selected and checked against all Image 3 consumers.
- **Repository:** Diaries parent, `change-control/complete/0052-DEF - correct catalogue image content errors/`.

## Problem

This defect covers two independent catalogue-image content errors: the Whitley Park map (**Image 3**) and the Hermitage illustration (**Image 18**). Both require consistent correction of actually served image data, catalogue metadata and retained Image state while preserving unrelated diary content.

The Whitley Park map currently shown in the diary for **20 March 1828** depicts Whitley Park in the wrong location. The incorrect map is visible in the legacy image rendering and the new IMAGE fragment rendering. Replacing the file used as the map must not inadvertently alter the diary transcription, fragment ownership, image-catalogue identity or optional Marquee and external-link metadata.

### Known affected references (as reported by the owner)

| Object | Identity | Issue |
| --- | --- | --- |
| Diary date | 1828-03-20 | Incorrect Whitley Park map appears |
| Legacy fragment | **84** | Embedded map requires review/correction; do not assume conversion to IMAGE |
| Fragment | **2332** | Displays map associated with catalogue Image ID 3 |
| Fragment | **2333** | Reported affected; inspect its actual type, link and image/Marquee relationships before applying changes |
| Image catalogue entry | **Image ID 3** | Map representation/source relationship requires verification and correction |

The identities above are the owner's report, **not** a fresh database inventory. The actual source references, stored catalogue file path and any additional consumers of Image ID 3 must be established read-only before replacement.

## Source files

The image currently believed to be wrong is:

```text
\\nas\photo\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\diaries\diary-1828-and-1829-and-jan-1830\metadata\images-root\source\img2840-image-map-whitley-park.jpg
```

The owner requests replacing it with **one of the images** in the same `source` directory whose name begins:

```text
\\nas\photo\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\diaries\diary-1828-and-1829-and-jan-1830\metadata\images-root\source\img2840-whitley-park-map
```

The second path is a **filename prefix, not a verified full filename**. Enumerate matching files, inspect the originals at full resolution and record the **specific chosen filename**, dimensions, format and SHA-256 before changing data. Do not guess the file extension or assume the correct candidate from a cropped preview. The source NAS directory was not accessible when this defect was first registered. The **22 November Step 1 SSH inventory** subsequently identified `img2840-whitley-park-map/` as a **directory** containing `map2026-11-21_085923.png`, `whitley-park-historical-map.png` and `whitley-park-modern-map.png`; their sizes and SHA-256 hashes are preserved in [`reports/STEP1-INVENTORY-20261122.md`](reports/STEP1-INVENTORY-20261122.md). No candidate has yet been approved. The final choice still needs format/dimension and full-size visual confirmation.

## Additional task — replace the Hermitage image in the catalogue

The owner has selected a new, distinct Hermitage illustration and copied the genuine PNG `img2900-image-hermitage.png` into both `metadata/images-root/source/` and `metadata/images-root/images/` for `diary-1828-and-1829-and-jan-1830`. The task is to carry that correction through to the **served Files image and its Image catalogue metadata** using the **approved in-place Option 1**: retain the existing Image 18 catalogue record, canonical relative path and all existing Image 18 references. Do **not** create a replacement catalogue entry, redirect Fragments to it or delete Image 18. Copying the source/metadata image alone does not complete this task.

The replacement directory is:

```text
\\nas\photo\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\diaries\diary-1828-and-1829-and-jan-1830\metadata\images-root\images\img2900-image-hermitage.png
```

The catalogue-relative file path to locate is:

```text
diary-1828-and-1829-and-jan-1830/images/img2900-image-hermitage.png
```

Recorded replacement identity (22 November 2026): **PNG, 720 × 480 pixels, 935,720 bytes**, SHA-256:

```text
9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0
```

At the last read-only check, the corresponding production `files/` and development `files-development-common/` copies beneath `diaries-content/` still held the old **3,840,009-byte, 1859 × 1084 PNG**, SHA-256:

```text
2097979bd1ca47370a55c0f6053167a96f541a5c04adfe4ff52dc564ccc97d5a
```

Recheck these identities before execution. The protected 0028 V2 draft (91) identifies **Image 18** as the intended catalogue identity for legacy Fragment **598**. However, **live** production/development Image IDs and all consumers have not yet been inventoried; resolve the actual existing row from its canonical path in each environment rather than assuming IDs match across databases. The approved repair must preserve the verified existing Image 18 identity, or stop and obtain a separately documented decision if the live inventory disagrees. Preserve their transcription, positions, ownership, optional Marquees and clickable links. Do not change `img2903-image-st-isaac-church.png` or the separate Jordan Staircase image `img2900-image-the-jordan-staircase-state-hermitage-museum-st-petersburg-russia-B2KPFE.jpg`.

Historical checks found the old Hermitage and St Isaac files had identical bytes, but did not establish when or how the duplication happened. The replacement corrects the content; it must not be described as a proven recovery of the original file. See [evidence notes](evidence/README.md) for the prior checks and their limits.

## Expected behaviour

- The accepted map accurately depicts the intended **Whitley Park, Whitley Bay** geography relevant to the diary entry, rather than a misleading location.
- The relevant 20 March 1828 Editor and public Reader views consistently display the approved map; the catalogue thumbnail and full-size IMAGE rendering are consistent.
- The correction is reflected in Fragments **84, 2332 and 2333**, to the extent each actually references the map. Each fragment's role and type remain unchanged unless separately approved.
- **Image ID 3** continues to resolve correctly, with file/catalogue metadata (such as path, format, dimensions and checksum) updated consistently by the supported mechanism. Do not assume that replacing a file under `metadata/images-root/source/` automatically changes the file served by the Image catalogue.
- Existing transcription, date/sequence, source-page links, optional IMAGE click URLs and Marquees remain intact.
- No other shared references to Image ID 3 are silently altered; inventory and approve the impact if its use extends beyond the three reported fragments.

## Scope and safety

**In scope:** inspect and choose the correct Whitley Park candidate; correctly replace the Hermitage image in the catalogue using the owner's selected PNG; trace legacy embedded-HTML references and catalogued file identities for both images; update necessary served/derived/cached images and catalogue metadata; perform consolidated verification in the existing Editor/Reader workflows. Treat production and development as separate database/Files pairs and record the outcome for each.

**Out of scope:** 0051 feature implementation and activation; 0028 legacy-fragment conversion; wholesale Image catalogue migration; 0029 lifecycle/schema cleanup; unrelated historic map replacement.

Do not overwrite/delete the current NAS source image, published Files image or Image catalogue record until the current version and the replacement are backed up with hashes and a tested rollback route. A new picture with the same filename may need cache invalidation in browsers/CDNs and derived thumbnail regeneration. Prefer the supported catalogue-aware replacement process; if none exists, document the minimal controlled repair and reconcile PostgreSQL, stored files and MQTT retained Image metadata without pretending a plain file swap is sufficient.

The production DATE/fragment/Image identity used here is not a licence for exploratory writes. No data, NAS files, database records, or MQTT topics are changed by this defect registration.

## Acceptance criteria

- [ ] **Image 18 is corrected in place**: the existing catalogue record and Image 18 ID/path/consumers are preserved, its served PNG and metadata are made consistent, and no new Image is inserted or old entry deleted.
- [ ] The unchanged Image **25** (St Isaac church) and separate Jordan Staircase reference retain their recorded original hashes and metadata.
- [ ] Full filename of the selected replacement, reason for selection, format/dimensions and SHA-256 are recorded.
- [ ] Pre-change inventory records actual paths, file hashes, catalogue metadata, embedded references, all Image ID 3 consumers, and the state of Fragments 84/2332/2333.
- [ ] An original-image/metadata rollback copy and applicable recent database/Files recovery point are verified before modifying the served content.
- [ ] The correct map is visible at 20 March 1828 in the Editor and public Reader, including the IMAGE fragment image, Image ID 3 preview and legacy embedded image where applicable.
- [ ] Fragment text, Marquees, links, ownership and ordering remain unchanged, except for specifically approved image-reference updates.
- [ ] Restart/refresh and cache checks demonstrate that the old map is not still being displayed for these affected references.
- [ ] Post-change database/Files/catalogue/MQTT checks have no unexpected discrepancies; rollback information and evidence are saved in this defect directory.
- [ ] Hermitage Image identity and all affected catalogue/fragment/legacy references are inventoried separately in production and development; the selected PNG is rehashed before use and rollback copies are retained.
- [ ] Both environments serve the selected Hermitage PNG; applicable catalogue checksum, byte size, format, dimensions and version/cache metadata match it, and retained Image state is reconciled through the supported mechanism. The existing Image 18 identity, canonical path and consumers are preserved as explicitly approved; no Image 18 replacement/new-ID workflow is permitted without a further owner decision. Image 3 handling follows its separately approved consumer inventory.
- [ ] The Hermitage catalogue preview and affected Editor/Day Reader/public Reader views display the new image after refresh/reconnect; links, Marquees and ordering still work. St Isaac and the separate Jordan Staircase image remain unchanged.
- [ ] Any 0028 review/checksum expectations affected by either correction are identified and refreshed through its review workflow, retaining the original frozen evidence; this defect does not execute migration or silently approve changed image identities.
- [ ] The content owner approves the visual result and formally accepts defect closure.

## Dependencies and links

- [0051 — IMAGE links and optional Marquees](../../complete/0051-FEAT%20-%20extend%20IMAGE%20fragments%20with%20links%20and%20optional%20marquees/README.md): keep new IMAGE presentation and link/Marquee contracts unchanged.
- [0028 — reviewed legacy embedded-image migration](../../in-progress/0028-FEAT%20-%20migrate%20reviewed%20legacy%20embedded-image%20fragments/README.md): do **not** implicitly migrate Fragment 84 or change its approved disposition.
- [0029 — Image lifecycle completion](../0029-FEAT%20-%20complete%20Image%20lifecycle%20and%20remove%20legacy%20fragment%20marquee%20coupling/README.md): coordinate supported Image replacement/reconciliation policy if required.

See [Implementation Steps](IMPLEMENTATION-STEPS.md). Evidence, logs, manifests and any one-off scripts belong **inside this defect's folder** in the Diaries parent repository, not in Playbooks or a host home directory.
