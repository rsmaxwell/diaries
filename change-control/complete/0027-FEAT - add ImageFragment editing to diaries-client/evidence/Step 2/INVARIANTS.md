# Step 2 — Frozen ImageFragment Invariants

These invariants are mandatory for all later 0027 implementation steps.

| ID | Invariant | Client consequence | Responder remains authoritative for |
|---|---|---|---|
| UX-INV-001 | An IMAGE Fragment never gains a Marquee through `diaries-client`. | No create/update Marquee action is offered for IMAGE; no IMAGE request synthesizes `marqueeId`. | Stored Fragment type and cross-type validation. |
| UX-INV-002 | A MARQUEE Fragment never gains an Image reference through `diaries-client`. | Image chooser/mutation actions are unavailable for MARQUEE. Ordinary Fragment updates continue to omit `imageId`. | Cross-type request validation. |
| UX-INV-003 | Fragment `type` is immutable after creation. | Update workflows never offer or send a type conversion. | Rejecting conflicting supplied type. |
| UX-INV-004 | Fragment `pageId` is immutable after creation. | Image reference edits never move a Fragment to another Page. | Rejecting conflicting supplied pageId. |
| UX-INV-005 | An IMAGE Fragment references zero or one Image by positive catalogue ID. | Chooser returns one `imageId`, never a raw URL/path or multi-select collection. | Image existence/reference integrity. |
| UX-INV-006 | One Image may be reused by multiple IMAGE Fragments. | Choosing an already-used Image is valid; the client does not force duplicate upload. | Delete guard while references exist. |
| UX-INV-007 | Ordinary IMAGE text/date/sequence edits preserve the current Image reference. | Ordinary update serialization omits `imageId`. | Omitted `imageId` means preserve. |
| UX-INV-008 | Image replacement is explicit. | Only the Image-reference edit path sends a positive `imageId`. | Lock, version, gate and Image existence checks. |
| UX-INV-009 | Image clearing is explicit. | Only confirmed **Clear Image** sends `imageId: null`. | Lock, version and authoring-gate checks. |
| UX-INV-010 | Selecting/changing an Image does not implicitly change text/date/sequence. | Reference edit carries current authoritative values but does not manufacture other edits. | Normal update/version/normalisation semantics. |
| UX-INV-011 | Browsing or cancelling the Image chooser does not hold a Fragment lock. | Lock is acquired only after a completed selection and context revalidation. | Lock ownership/release. |
| UX-INV-012 | Delete Fragment and Delete Image are separate lifecycle operations. | IMAGE Fragment deletion never calls `deleteImage`; clearing an Image never calls `deleteImage`. | Reference-aware Image deletion. |
| UX-INV-013 | Fragment ordering remains one mixed chronology. | MARQUEE and IMAGE use the same `sequence`; no IMAGE-only ordering model. | Sequence normalisation. |
| UX-INV-014 | The responder is the final authority. | Client enablement/validation improves UX but never bypasses 401/403/lock/version/reference failures. | Authentication, authorisation, gate, locks, versions, persistence. |
| UX-INV-015 | Runtime presentation URL is derived, not persisted as Fragment identity. | Fragment state stores `imageId`; display URL is derived from Image metadata/runtime Files configuration. | Image metadata persistence. |
| UX-INV-016 | Legacy null/absent Fragment type remains MARQUEE-compatible during migration. | Existing MARQUEE behaviour and guards continue to use `effectiveFragmentType`. | Stored migration compatibility. |

## Tri-state Image update rule inherited from Step 1

```text
imageId omitted       -> preserve the current Image reference
imageId positive      -> attach/replace the Image reference
imageId null          -> explicitly clear the Image reference
```

Later refactoring must not collapse these three states into a single optional/nullable serializer that cannot distinguish **preserve** from **clear**.
