# 0052-DEF Step 1 — Replacement selection and live-inventory continuation, 23 November 2026

**Status:** Step 1 remains OPEN. Owner's Whitley Park replacement is selected and its file identity was captured. The live production/development database, HTTP and Files inventories still require execution and review. This supplements, and does not replace, `STEP1-INVENTORY-20261122.md`.

## Whitley Park — approved source-image identity

The owner specified the replacement PNG on the NAS in the folder:

`diaries/diary-1828-and-1829-and-jan-1830/metadata/images-root/source/img2840-whitley-park-map/`

| Property | Verified 23 November 2026 |
| --- | --- |
| Filename | `whitley-park-historical-map-large.png` |
| Size | **543,005 bytes** |
| Encoding | **PNG, 8-bit RGBA, non-interlaced** |
| Dimensions | **776 × 502 pixels** |
| SHA-256 | `d9f54457b8b4ac67a9a91df5e8c7c32c2767531dd2d6461c3f7faf9c31e4706a` |
| Source | Owner's Cygwin `ls`, `sha256sum` and `file` output, `note(20261123-091909).txt` |

The existing catalogue target is **Image 3**, currently described by `img2840-image-map-whitley-park.jpg`. The replacement is **PNG**, not JPEG: never merely rename PNG bytes to `.jpg`. The choice between generating a JPEG at the existing canonical path versus changing the catalogued path/consumer URLs must be informed by the *live* reference inventory. Preserve Image ID 3 if the inventory permits it and avoid changing unrelated consumers.

The three previously inventoried candidates in the 22 November report remain historical evidence; the owner's latest selected `*-large.png` is a separate, fourth file.

## Hermitage — agreed controlled correction

**Image 18, `img2900-image-hermitage.png`: Option 1 (in-place).** Retain the actual verified production Image ID 18, canonical relative path and consumers, updating the served Files PNG and applicable catalogue metadata together. Development may have different Image IDs; resolve by canonical path there before writing.

Previously recorded selected PNG: **935,720 bytes**, **720 × 480**, SHA-256 `9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0`. Verify source and metadata copies again. Preserve **Image 25 St Isaac** and the **Jordan Staircase** image unchanged. The content correction must be accepted before final confirmation of 0028 Fragment 598; do not run 0028 migration under 0052.

## Read-only inventory collector

The feature-local script `tools/collect-0052-step1-readonly.sh` and SQL file `tools/step1-live-catalogue-readonly.sql` provide one consolidated evidence capture, including:

- Windows parent Git status/revisions and submodules.
- Selected and old NAS source/processed/production/development Files hashes, with protected-image baselines.
- Read-only SQL from each live database: catalogue metadata, all direct consumers, embedded legacy URLs, reported Fragments 84/2332/2333/598/606, optional links, Marquees and text fingerprints.
- Served HTTP response SHA-256 for current production/development image URLs, compared with the NAS Files hashes where both are available.

Run as a **separate Bash process in Windows Cygwin**, from the Windows repository (do not run `set -e` in the interactive shell):

```bash
feature='change-control/in-progress/0052-DEF - correct catalogue image content errors'
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash "$feature/tools/collect-0052-step1-readonly.sh" both
```

`both` attempts the **production** database via `ssh pluto` / `docker exec` and the active **development** database via local Docker. Use `production` or `development` if only one environment is running. It auto-selects a database container only when exactly one expected name is running; ambiguous or inaccessible containers result in a **FAIL/PARTIAL**, never an assumed success. No passwords or Docker environment dumps are recorded. The optional `DIARIES_NAS_CONTENT_ROOT` variable can override the default mapped NAS content root.

**Raw output is private:** the script writes `.log` files under `evidence/Step 1/private/<UTC>/` (ignored by the parent repository's Git rules). The logs include sensitive Fragment HTML and are for owner's review, not public commit. Console output gives a summary and evidence directory. HTTP/SSH/Docker failures remain visible as failed checks; do not interpret partial collection as Step 1 acceptance.

The retained MQTT Image publication is **not** read by this collector because it needs a separately authorised broker connection. Inspect the relevant `diaries/images/<id>` retained topics using the existing MQTT Explorer read-only access after resolving live IDs; compare against the database rows.

The SQL begins with `BEGIN TRANSACTION READ ONLY` and selects only metadata/Fragment data. It cannot alter catalogue rows. The current Image entity defines `id, version, relative_path, mime_type, original_filename, width, height, checksum, caption, alt_text`; **there is no byte-size database column**. Capture byte size from the filesystem, and update only actual schema fields later.

## Step 1 remains outstanding until

- Review the actual catalogue IDs, paths, versions, checksums, and *all* Image 3 and Image 18 direct/legacy consumers in **both** databases.
- Verify served Files root and HTTP hashes, including source/processed/protected image baselines.
- Agree and document the Whitley Park PNG/JPEG path/format handling, leaving unrelated references intact.
- Record deployment/recovery-point identities before any writes, then proceed to consolidated Step 2 implementation and Step 3 acceptance.

No database, NAS, MQTT or production content changes were made to prepare these tools and this report.
