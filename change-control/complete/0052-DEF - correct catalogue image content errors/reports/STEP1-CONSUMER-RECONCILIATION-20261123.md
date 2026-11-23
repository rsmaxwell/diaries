# 0052-DEF — Step 1 consumer reconciliation (23 November 2026)

Status: **read-only consumer inventory completed**. This report supplements, but does not replace, `STEP1-INVENTORY-20261122.md` and the private logs collected at `evidence/Step 1/private/20261123T093129Z/`.

## Approved replacement sources

| Catalogue ID | Selected source | Size/dimensions | SHA-256 |
|---|---|---|---|
| 3 | `metadata/images-root/source/img2840-whitley-park-map/whitley-park-historical-map-large.png` | 543,005 bytes; 776 × 502 RGBA PNG | `d9f54457b8b4ac67a9a91df5e8c7c32c2767531dd2d6461c3f7faf9c31e4706a` |
| 18 | `metadata/images-root/source/img2900-image-hermitage.png` | 935,720 bytes; 720 × 480 PNG | `9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0` |

## Live inventory results

Production and development Image 3 both have the canonical relative path `diary-1828-and-1829-and-jan-1830/images/img2840-image-map-whitley-park.jpg`, version 0 and original checksum `0ec1199bb262f2c720737a6fcd71549549ea8727784d5b09e3602fcd6d2d69ba` (1060 × 718 JPEG). Production direct IMAGE consumers: Fragments **2332 and 2334**; Fragment **2334** has preserved Marquee **2272** (version 1, Page 692). Development direct consumer: Fragment **2338**. Both environments have legacy HTML reference Fragment **84**.

Production and development Image 18 both have the canonical relative path `diary-1828-and-1829-and-jan-1830/images/img2900-image-hermitage.png`, version 0, checksum `2097979bd1ca47370a55c0f6053167a96f541a5c04adfe4ff52dc564ccc97d5a` (1859 × 1084 PNG). Neither environment has a direct IMAGE Fragment for Image 18; legacy Fragment **598** references the old URL in both. Image 25 (St Isaac) shares the **old** Image 18 checksum, but must not be modified. Image 21 (Jordan Staircase) must remain untouched. Fragment 606 uses the old St Isaac URL and must also remain untouched.

Both selected replacement source files passed SHA-256 checks. Both live SQL queries completed under read-only transactions; both environment HTTP responses were equal to the respective NAS Files bytes. The missing Whitley intermediate `metadata/images-root/images/img2840-image-map-whitley-park.jpg` is documented and will be created with the corrected JPEG. It is not presently a served image. The source JPG exists and is subject to rollback protection.

## Implementation decision

Preserve existing catalogue **IDs 3 and 18** and canonical filenames/URLs. The selected Whitley PNG remains the source of record. Create a high-quality RGB **JPEG** copy from it (do not relabel PNG bytes), retaining the old `.jpg` URL used by legacy HTML. Preserve original files/DB rows and verify readability of small map labels before applying to production. For Hermitage, use the approved PNG bytes unchanged and update Image 18 in place.

No Fragment, Marquee, link, date/sequence, existing catalogue identity or 0028 frozen review decision is to be edited. Production and development are separate database/Files pairs and must be verified independently.

These checks are **not evidence of Step 2 deployment**. Step 1 can be considered technically inventoried, but formal step closure remains subject to acceptance under normal feature change control.
