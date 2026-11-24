# 0028-FEAT — Public Reader visibility handoff from 0052-DEF (23 November 2026)

**Status:** Acceptance requirement recorded; 0028 conversion and final acceptance **not yet executed or established** by this note.

## Observed baseline, production public Reader

The content owner has confirmed that the current Reader displays the corrected new-style Whitley Park IMAGE Fragments **2332** and **2334**. It does **not** display legacy embedded-image Fragments **84** (Whitley Park) or **598, 599, 600** (Hermitage). The owner accepts that temporary omission for 0052 on the **condition that these images appear correctly after 0028 migration**.

## Existing 0028 review intent — verify against current review state before apply

The supplied 0028 v2 PRIVATE draft `(91)` in the 2026-11-23 morning source bundle contains the following candidate dispositions; this is **review intent**, not proof of an applied migration:

| Legacy Fragment | Draft disposition | Approved Page | Review content / qualification |
| --- | --- | --- | --- |
| **84** | `CONVERT_TO_IMAGE` | **692** | Whitley Park; catalogue Image 3; preserve original caption and sequence before Fragment 85; v2 confirmation YES in supplied draft |
| **598** | `CONVERT_TO_IMAGE` | **752** | Hermitage; catalogue **Image 18**, corrected `img2900-image-hermitage.png`; obtain final v2 confirmation (blank in supplied draft) |
| **599** | `CONVERT_TO_IMAGE` | **752** | Hermitage / Jordan Staircase; catalogue **Image 21** (Jordan Staircase), *not* Image 18; v2 confirmation YES in supplied draft |
| **600** | `CONVERT_TO_IMAGE` | **752** | Hermitage from the front; catalogue **Image 20** (front/exterior view), *not* Image 18; v2 confirmation YES in supplied draft |

Do not conflate all three Hermitage illustrations with catalogue Image 18: the reviewed mappings are **598→18, 599→21 (Jordan Staircase), 600→20 (front view)**. Preserve the three separate catalogue identities, reviewed captions and sequence. Image 21 is also one of the protected catalogue items verified unchanged during 0052; its *use* by migrated Fragment 599 is intended, but its source image must not be overwritten. Reconcile the current (possibly newer) PRIVATE review export before approving or applying migration, especially for **598**. Preserve frozen review artifacts.

## Mandatory post-migration acceptance

After an authorised 0028 application, verify in **both the Editor and public Reader** that:

1. Each intended converted fragment **84, 598, 599, 600** is page-owned, rendered and directly attributable to the correct catalogue image or approved source; confirm the migration's actual resulting Fragment IDs if any split occurs.
2. **84** shows the approved updated Whitley Park map on the intended Page 692, with caption and chronological placement preserved; existing new-style Fragments 2332 and 2334 still work and are not replaced accidentally.
3. **598** shows corrected Hermitage **Image 18** on Page 752; **599** shows **Image 21 (Jordan Staircase)**; and **600** shows **Image 20 (Hermitage from the front)**. Each must retain its reviewed caption, with no substitution or duplication.
4. Captions, text, sequence/ordering, links and optional Marquee behaviour follow the approved per-candidate disposition; St Isaac **Image 25** and the catalogue source for Jordan Staircase **Image 21** remain unchanged (while Fragment 599 intentionally uses Image 21).
5. Development rehearsal and production postflight evidence include the database/retained-MQTT relationships and a real browser visual check. HTTP 200 of a month route or of the Reader homepage does **not** prove a fragment appears.

A failed or omitted image after migration is an **0028 acceptance failure**, even though its pre-migration absence is accepted for closure of 0052. No change to database, source files, MQTT, or 0028 decisions is authorised by this note.

**Provenance:** Owner's 2026-11-23 public Reader observation; 0052 Step 3 check `20261123T130110Z-consumers`; 0028 v2 PRIVATE draft `(91)` and `DESIGN-AND-INTERFACE-CONTRACT.md` from the 2026-11-23 08:23 source bundle. The draft may not represent latest live review status.
