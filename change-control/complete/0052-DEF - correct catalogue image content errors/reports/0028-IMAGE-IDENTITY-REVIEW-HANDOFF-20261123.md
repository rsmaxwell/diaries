# 0052-DEF to 0028-FEAT — image-identity review handoff (23 November 2026)

**Status:** Review handoff only; **no 0028 migration, database write or frozen-record modification authorised.** Keep this document inside 0052 change-control until 0028 picks up the affected review candidates.

## Why a handoff is required

0052 corrected the bytes and metadata of the existing catalogue images **3 (Whitley Park)** and **18 (Hermitage)** in production and development. These are content corrections, not permission to convert legacy embedded-image fragments or to change catalogue identities. Prior 0028 review evidence was frozen before the repairs. The working 0028 v2 draft `(91)` was reported to have 71 of 72 review decisions accepted, with the remaining **Fragment 598** awaiting final Hermitage Image 18 verification. That reported count should be reconciled against the latest PRIVATE review export, not copied into an official approval claim.

Legacy Fragments **84** and **598** retain `type IS NULL` and `page_id IS NULL` and continue to reference the expected Whitley/Hermitage filenames in their legacy text. Because the public Reader resolves page-owned fragments, a direct `?fragment=84` or `?fragment=598` test is not a valid 0052 public Reader check. Future migration and public Reader projection of these legacy fragments belong to **0028-FEAT**.

## Action when resuming 0028

1. Preserve 0028's sealed original frozen inventory, HTML evidence and review export; preserve the current PRIVATE draft `(91)` and any newer export. Do not replace them in place.
2. Refresh only image-identity/review evidence affected by 0052 using the existing 0028 read-only review workflow. In particular, verify **Fragment 598 → Hermitage Image 18** against the corrected PNG and existing catalogue identity; also re-evaluate any Whitley Fragment 84 image-byte/reference assumptions that depended on the old Image 3 content.
3. Record the new image checksum(s), visual approval and resulting per-candidate review decisions in **0028's own feature evidence/reports**, not in this handoff alone. The selected Hermitage PNG identity from 0052 is SHA-256 `9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0`.
4. Do not treat 0052's successful retained-MQTT/HTTP/fragment relationship tests as approval of 0028 migration, new page ownership, new IMAGE fragments, altered transcription or Marquee recreation.
5. This handoff may be acknowledged as part of 0052 closure, but the entire 0028 migration is **not** a prerequisite for correcting the two existing catalogue images.

## Verified 0052 Step 3 handoff reference

`evidence/Step 3/private/20261123T130110Z-consumers/RESULT.txt` — 12/12 database assertions plus public Reader index, page-owned Whitley URL and July month HTTP 200. July month HTTP 200 **does not** establish public Reader rendering of Hermitage Fragment 598.
