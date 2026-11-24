# 0028 Step 2 — Owner decision: tolerate Marquee placement drift (23 November 2026)

## Owner decision

The owner has been repositioning and resizing Marquees from initial default rectangles to more accurate locations. **Changes only to x, y, width or height are acceptable**; an ordinary Marquee version increase from such edits is also acceptable. **Presence/absence, identity, Fragment ownership and Page ownership must remain exact and fail closed if changed.** This decision supersedes the strict frozen-geometry/version equality clauses in the earlier 0028 design contract for the 71 reviewed in-place conversions. It does **not** grant approval to remove or insert Marquees, discard image links, or change the reviewed Image, Page, caption, date, chronology, original HTML or Fragment version.

## Implementation

`MigrationStore.checkMarqueeSafety` is invoked during both preflight/source inspection and postflight. For an original preserved Marquee it requires the same Marquee ID, Page, owning Fragment and valid finite geometry, with Marquee version not less than the reviewed version. If a Marquee was absent, any newly attached Marquee fails. If previously present, disappearance or replacement fails. SQL joins ensure a Marquee's Fragment ownership is taken from its actual database association; the same-PAGE check is enforced against the reviewed destination.

The frozen Marquee geometry/version SHA-256 is retained for audit and produces an informational message when it differs. It is **not** a migration blocker. The migration does not write Marquee geometry, position or size; existing values are kept. The date transactions lock preserved Marquees before conversion and now compare the **immediate pre-conversion** Marquee values with the values read after the Fragment update, failing and rolling back the date transaction if any Marquee field (including geometry or version) changes during migration. Postflight checks retain the structural identity/presence/Page validations while allowing owner edits made since the review.

This is a limited policy correction, not a new review or a regenerated migration manifest. Previous evidence, approved source-image checksums and 71/1/30/22 manifest scope remain unchanged. Existing Step 2 geometry-hash canonicalisation is retained for historical-hash diagnostics but no longer gates user-edited placement.

## Verification and next action

All 14 policy/geometry Java regression cases passed using isolated Java compilation stubs; the actual responder Gradle/JUnit build and isolated PostgreSQL rehearsal against the Windows checkout are still required. In particular, rerun the existing `--resume-restored` rehearsal using `DIARIES_0028_SOURCE_FILES_ROOT` set to the verified NAS Files directory. Reuse the accepted 23 November isolated PostgreSQL restore; do not repeat the production dump. No production apply is authorised.

**Status: 0028 Step 2 IN PROGRESS, production migration NOT authorised.**
