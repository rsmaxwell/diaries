# 0052-DEF Step 3 — Legacy fragment verifier correction (23 November 2026)

## Context

The first run of `verify-0052-step3-consumers-readonly.sh` saved private evidence to
`evidence/Step 3/private/20261123T124810Z-consumers/` but stopped after the
legacy Fragment 84 check. Both development and production reported `FAIL` for
legacy Fragments 84 and 598. They nevertheless agreed on the corresponding
metadata fingerprints, and the Image 18 direct-consumer check passed.

## Diagnosis

The original SQL incorrectly assumed legacy fragments 84 and 598 have
`type='MARQUEE'`. The current responder entity explicitly permits a null type
for legacy image candidates pending 0028 review. The pre-correction output's
`fragment_fingerprint` uses `concat_ws`, which *omits null arguments*. Hence
`84|0|NULL|1828|...` reports fragment `id=84`, `version=0`, then the null
image ID sentinel; it does not mean fragment type `0`. The original verifier
also did not show null `page_id` values explicitly.

## Correction

- Require `f.type IS NULL` for the two preserved legacy fragments, without
  changing any database content or prematurely migrating 0028 records.
- Use explicit `NULL` placeholders for `type` and `page_id` in future
  fingerprint output, so positional fields stay unambiguous.
- Retain all other consumer expectations, the protected St Isaac test, and
  the two production Reader HTTP GET checks.

The output from the original check does not yet establish that the legacy
embedded-image filename `LIKE` predicates pass. The corrected read-only run
will test that rather than assuming it. The current result is **not Step 3
acceptance**. Visual checks and formal owner acceptance remain outstanding.

Only the one-off verification script under this defect's `tools/` directory
is replaced by this correction package. The previous private evidence remains
untouched for traceability.
