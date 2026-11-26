# Step 3 — Production rehearsal rollback correction (2026-11-26)

## Observed failure

The isolated production migration rehearsal at 12:47 UTC restored the production dump and passed the 11-row baseline, both forward migration stages, and Marquee Page-column reconstruction (2,270 Marquees). The hybrid Fragment rollback then failed at its first TEXT-to-MARQUEE update because `fragment_type_final_check` still rejected the legacy type; PostgreSQL reported Fragment 1981. This was an isolated local PostgreSQL container, not the live production database. The rehearsal did **not** reach the final rollback/reapply acceptance gates.

Evidence: `evidence/step-3-production-isolated-rehearsal/production-rehearsal-20261126-124735-12160.log`.

## Correction

Change only `tools/step2-hybrid-schema-rollback.sql`. After its existing guards and within the same transaction, remove the forward-only Fragment constraints, drop the new index, and restore `fragment.type` nullability **before** updating type or Page values. Then restore MARQUEE values, the two original null Page IDs and the ten original null types, re-add the old `fragment_type_check`, and remove hybrid columns.

The forward migration SQL, Marquee retirement SQL, and rehearsal runner remain unchanged. The rollback is appropriate for the reviewed baseline with **no intervening application edits**; the verified database backup is the recovery path if the live data has subsequently changed.

## Verification and acceptance

Source-level ordering checks for this patch passed. The full isolated production rehearsal **must be rerun** and must pass baseline restore, both forwards, both rollbacks, restored pre-migration gate, and reapplication before this gate can be accepted. No production mutation or service restart is authorised by this package.

Updated rollback SHA-256: `9c730377288482e38a2633aee078cbc47def064039083657f45bf1b4cf9812a7`.
