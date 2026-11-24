# 0028 — Step 1 post-0052 technical acceptance and Step 2 handoff

**Date:** 2026-11-23 (UTC)

**Status: STEP 1 TECHNICAL CHECKS PASSED; FORMAL STEP 1 CLOSURE NOT YET RECORDED.**

This note consolidates results actually submitted by the owner, not a claim
that deployment or a production database update has occurred.

## Accepted automated inputs

- Read-only production reconciliation at `20261123T143827Z-post0052-readonly`:
  2,331 Fragments; 72 legacy image occurrences; 71 reviewed conversions;
  one explicit `DEFER` (Fragment 1564); zero review blockers;
  expected post-0052 catalogue changes limited to Images 3 and 18;
  five regression tests passed.
- Prepared reviewed manifest at `20261123T144651Z-reviewed-manifest-prepared`:
  three CSVs, SHA-256 identities and a preparation receipt;
  71 `CONVERT_TO_IMAGE`, one `DEFER`, 30 preserved image links,
  22 preserved Marquees; seven preparation regression tests passed.
  Preparation status is `PREPARED_NOT_APPROVED`; `productionApplyAllowed=false`.
- The separate 0052-DEF image-content defect is formally closed and committed
  in the Diaries parent repository at `90c192b`.
- Review of Fragment 598, Hermitage, was recovered and explicitly confirmed
  without losing the 70 previous V2 review confirmations.

The source preparation expressly does **not** grant production apply authority.
The historic 0022 candidate CSV remains an acknowledged evidence limitation;
current production inventory is the technical migration baseline. The owner
has requested continuation of 0028 development, not separately approved a
production mutation or formal Step 1 gate closure. Keep Step 1 OPEN until
its explicit gate decision is recorded.

## Step 2 input contract

The authoritative private input directory is the **actual generated**
`20261123T144651Z-reviewed-manifest-prepared` folder in the Windows working
copy, not the older source bundle and not the incomplete draft `(92)`.

Use its `0028-dispositions.csv`, `0028-image-decisions.csv`,
`0028-v2-preservation-decisions.PRIVATE.csv` and `PREPARATION-RESULT.json`
together, with unchanged SHA-256 values. Source HTML and URLs remain private.

All 71 approved mutations are one-image **in-place** conversions; no approved
SPLIT, KEEP or destructive Marquee/link action is present. Therefore the first
implemented Java workflow is strictly limited to this exact manifest shape.
Any new SPLIT or unsupported action fails closed and requires a new review and
implementation acceptance, not a guess.

## Separate gates retained

1. Step 2: real Gradle compile/JUnit and restored-database integration tests;
   dry-run/postflight and transaction/resume/rollback evidence.
2. Step 3: separately approved restored rehearsal, backup confirmation,
   offline writer-stop, MQTT replay and owner-approved production execution.
3. Step 4: final regression/acceptance and formal closure decision.

Nothing in this report marks any implementation or production gate CLOSED.
