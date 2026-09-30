# Step 11 focused coverage matrix

**Status: COMPLETE LOCALLY — 2026-09-29.**

| Required area | Existing coverage retained | Step 11 focused addition |
| --- | --- | --- |
| Retained Image metadata/tombstone/ID mismatch/additive fields | `decodesCanonicalImageMetadataAndIgnoresUnknownAdditiveFields`, `emptyPayloadIsATombstoneForExistingAndImageEntities`, `rejectsImageTopicPayloadMismatchJsonNullAndInvalidJson` | `step11KeepsRetainedImageAndFragmentCompatibilityBoundariesDistinct` |
| Legacy null vs unknown explicit Fragment type | `decodesTypedLegacyAndUnknownFragmentPayloadsWithoutCoercingUnknownType` | same Step 11 compatibility-boundary test includes explicit JSON `type:null` and future `VIDEO` |
| Image lifecycle / arrival order / shared references / reconnect | existing Step 5/6 `ProjectionServiceTest` lifecycle, arrival-order, shared-reference and reconnect cases | retained unchanged; concentrated degraded-state matrix added |
| Resolution and diagnostics | existing typed diagnostics and repair tests | `step11DistinguishesEveryDegradedRelationshipStateWithoutDroppingValidPageOwnedRows` |
| Files config / public vs internal / hostile URL data | Step 7 config and URL tests | Unicode+percent nested route acceptance; public-only URL assertion; absolute URL rejection |
| Sanitizer / media escaping / raw boundary | existing sanitizer tests and Step 8/9 HTTP escaping assertions | template audit proves only sanitized `fragment.html` uses `| raw` |
| HTTP mixed chronology / redirects / templates / GET-HEAD / CSP | existing `WebServerTest` | `step11CoversMixedChronologyDegradedMediaMissingOwnershipAndReadOnlyHttpBoundaries` |
| Browser overlay/history/file failure | Step 10 manual browser evidence | deterministic local content fixture for valid bytes, invalid bytes and 404 plus Step 11 checklist |

## Completion-condition distinctions

- **Reference absence:** IMAGE with null `imageId` => `NO_SELECTION`.
- **Missing metadata:** IMAGE references an absent retained Image => `MISSING_METADATA`.
- **Rejected metadata:** known retained Image ID rejected by decoder/projection generation => `INVALID_METADATA`.
- **Bad bytes:** valid projected Image metadata and URL, HTTP 200 body is not a decodable image => browser-only `FILE_LOAD_FAILED`.
- **Missing bytes:** valid projected Image metadata and URL, HTTP 404 => browser-only `FILE_LOAD_FAILED`.
- **Invalid cross-type link:** IMAGE linked to a Marquee remains IMAGE, exposes no selected Marquee, and increments diagnostics. MARQUEE with `imageId` remains MARQUEE and ignores Image media.
- **Missing Page ownership:** Fragment with null/missing Page cannot be resolved into a Diary chronology; diagnostics count the reason and HTTP does not fabricate ownership.


## Verification result

- Focused retained/projection/config/rendering/HTTP suite: **PASS** (`BUILD SUCCESSFUL in 11s`).
- Full `diaries-web` test/build gate: **PASS** (`BUILD SUCCESSFUL in 50s`).
- Browser normal IMAGE path, escaping, IMAGE no-Marquee selection and keyboard/focus: **PASS**.
- Browser-only media failure presentation: **PASS**, reusing the Step 10 manual `FILE_LOAD_FAILED` evidence; Step 11 adds deterministic 404 and invalid-byte fixture endpoints for reproduction.
- Production runtime source changed by Step 11: **NO**.
