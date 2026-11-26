# 0029 Step 2 — 49 embedded-image source reconciliation manifest

Status: **READ-ONLY PREPARATION; NO MIGRATION AUTHORIZED**.

## Basis
Development diagnostics (2026-11-25) identified 60 Page-less Fragments: 11 previously reviewed by 0029, plus 49 legacy HTML image Fragments, all NULL type. Each of the 49 has a unique filename match to the Image catalogue; only one source matches a dated IMAGE Fragment on the same date. No 0028 journal tables are present.

The existing `Migration0028ReviewedFragments` Java program is scoped to **71 reviewed conversions and one deferral (Fragment 1564)**, and validates a signed-off reviewed manifest, source HTML SHA-256, destination Page, catalogue image checksum and approved plan. It must **not** be retargeted to these 49 records without a fresh review and formal approval.

## This package

The SQL generates a **candidate review CSV only**; no INSERT, UPDATE, DELETE or DDL occurs. The source HTML MD5 column is an inexpensive *drift fingerprint*, not acceptable as an image authenticity proof. `page_candidates_same_day` is contextual evidence only. Filename matches are candidates; do not delete the legacy Fragment on their basis.

The runner checks 49 sources, their NULL type / lack of Image ID, and the uniqueness of candidate matches. It uses Docker Compose for development-infrastructure; evidence is kept in the 0029 feature directory.

## Required review before rehearsal

For every candidate: confirm source image byte checksum against the existing catalogue image file; approve the destination Diary and Page; decide text/caption/link treatment and stable sequence placement; check whether a dated IMAGE Fragment already represents it; capture original HTML SHA-256, expected version, image checksum and review receipt. Check corrected Images 18 (Fragment 598) and 25 (Fragment 606) against their current files, not historical hashes. Cross-check earlier 0028 acceptance receipts and avoid double migration.

No database write, schema migration, MQTT republish or production deployment is part of this package. An isolated restored development database, rollback evidence and approved reviewed manifest remain prerequisites to the eventual rehearsal.
