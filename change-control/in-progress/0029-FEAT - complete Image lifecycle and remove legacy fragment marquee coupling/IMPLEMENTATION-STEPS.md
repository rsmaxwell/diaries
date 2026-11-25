# 0029-FEAT — Implementation steps (hybrid model approved 2026-11-25)

**Status: IN PROGRESS.** The following is the agreed implementation plan, **not** evidence that the target model has been deployed. See [README.md](README.md) and the Diaries `ARCHITECTURE.md`. Use a few substantial implementation chunks and one consolidated verification cycle.

## Step 1 — Baseline, actual data and migration disposition (OPEN)

- [ ] Confirm the Windows parent/client/responder/web revisions, dirty working trees and submodule references before application edits; verify current deployed versions and Playbooks revision before deploying.
- [ ] Preserve and accept already collected 2026-11-25 database preflights: 22 development type fixes (complete), zero analogous production rows, 60 development vs 11 production Page-less, 71 journalled 0028 sources in production, reviewed Page candidates and content previews. Keep all raw evidence in this 0029 directory; do not rerun accepted checks without a reason.
- [ ] Reconcile 49 development-only Page-less embedded-image HTML records against 0028 evidence and migrated IMAGE records; no blind deletion or Page attachment.
- [ ] Validate 9 annual preamble Fragments and their explicit Diary/year identity; preserve links/HTML. Confirm 1738 and 2061 as DATED with verified Page 1005 and 1078 respectively; verify sequence without overwriting existing content.
- [ ] Audit fragment enum/type, year/date/diary fields, `page_id`, MQTT date aliases, reader projection and Angular Dayview assumptions, creation/edit RPCs, all Marquee references and Image catalogue protections. Determine minimal persistent Diary FK for annual content, its migration/default semantics and non-page editing UX.
- [ ] Record actual schema constraints, relevant DB/Files/MQTT reconciliation coverage and any residual exceptions before schema implementation.

**Gate:** validated data disposition, ownership contract and backup/rollback requirements documented; existing accepted evidence reused.

## Step 2 — Coherent hybrid ownership and integrity implementation

- [ ] Persist `TEXT`/`IMAGE` type and `PREAMBLE`/`DATED`/`POSTAMBLE` placement. `MARQUEE` is renamed `TEXT` in data and consumers; do not mistake a Marquee for a Fragment type.
- [ ] Implement exclusive ownership: DATED requires Page and derives Diary; annual placement requires explicit Diary + calendar year, NULL Page and no Marquee. Add appropriate nullable/required columns and conditional CHECK/FK constraints plus responder-level validation of cross-row rules and diary/year dates. Do not impose blanket `page_id NOT NULL`.
- [ ] Guarded migration: map ordinary Page-owned records to DATED, reviewed annual Fragments to PREAMBLE, 1738/2061 to verified DATED Pages; treat development-only legacy HTML separately. Preserve original HTML and useful hyperlinks; simplify decorative 1828 introductory HTML by reviewed transformation. No currently approved POSTAMBLE rows.
- [ ] Update responder JPA/entity, DTO/RPC, persisted validation, retained topic paths and startup normalisation so annual Fragments are addressable by **Diary/year** and do not acquire a fake Page; republish/delete obsolete retained aliases. Maintain derived `marqueeId` where needed.
- [ ] Update Angular editor (year-level pre/post sections without Page selection, create/edit/order and lock) and public reader projection (PREAMBLE before first heading; DATED grouped normally; POSTAMBLE after final heading), including Diary spanning multiple years and stable tie-breakers.
- [ ] Retire `marquee.page_id` and dependent Java paths only after validating that Marquee Page can be resolved through DATED Fragment; update constraints and rollback design together.
- [ ] Retain shared Catalogue Image caption/altText and per-occurrence optional link; support IMAGE/TEXT in any placement and optional DATED Marquee; add regression fixtures and tests for the new owner rules, POSTAMBLE and all date boundaries.
- [ ] Reuse existing 0024/0025 Image safeguards and reconciliation functionality; implement only demonstrated missing **read-only** reporting.

**Gate:** complete, internally consistent application/schema/migration package ready for consolidated regression. No arbitrary interim release or unnecessary compatibility layer.

## Step 3 — Consolidated verification and controlled production migration

- [ ] Build/test client, responder and reader; verify normal DATED editing/locks, TEXT and IMAGE, optional Page Marquees, links and catalogue captions.
- [ ] Verify 1828/1832 introductions above 1 January, other annual highlights, DATED 1738/2061, multi-year Diary presentation, synthetic POSTAMBLE, year-level edit/order and retained MQTT replay without fake date or Page relationships.
- [ ] Record current restorable PostgreSQL backup and relevant Files-root recovery, capture pre-migration rows and compatible rollback procedure; rehearse guarded SQL against development. Obtain appropriate approval before irreversible production operations.
- [ ] Deploy schema and compatible responder/editor/reader together, reconcile old/new retained topics, inspect logs and postflight, and run targeted production smoke tests.
- [ ] Capture final evidence/commit hashes/deployment versions; mark steps CLOSED only with accepted evidence. Move feature to `complete` only after explicit formal closure approval.

**Gate:** production ownership/integrity/reporting acceptance; no unresolved data exceptions concealed.

## Superseded 2026-11-25 decisions

Earlier in this same feature, mandatory Page ownership was proposed for all Fragments and 1828/1832 annual introductions were tentatively assigned to first-January Pages 685 and 972. **Those proposals are superseded** by approved hybrid ownership. The Page IDs remain useful as historical diagnostic context, **not** migration targets for PREAMBLE/POSTAMBLE. The existing 22-row development-only `MARQUEE` repair remains a completed intermediate fact; final `TEXT` conversion is not yet implemented.
