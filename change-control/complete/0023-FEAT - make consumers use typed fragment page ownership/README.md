# 0023-FEAT - Make consumers use typed fragment page ownership

## Type

Feature

## Status

In progress

## Priority

High

## Opened

2026-09-07

## Summary

Update `diaries-client` and `diaries-web` to consume `Fragment.pageId` and `Fragment.type` as the authoritative Page/type relationship while preserving existing MARQUEE behaviour. This deliberately lands before ImageFragments can be created so the system can prove the new ownership model without changing visible content semantics.

## Background

After 0022, retained Fragment payloads contain additive `pageId` and `type=MARQUEE`, but existing consumers still use marquee-centric assumptions.

The largest risk is `diaries-web` `ProjectionSnapshot`, which currently drops fragments without a valid `marqueeId` and discovers Page/Diary through the Marquee. The Angular client also models `marqueeId` directly on Fragment and some navigation/control logic assumes a selected Fragment implies a Marquee.

## Expected Behaviour

- existing MARQUEE fragments render and edit exactly as before;
- consumer models understand `pageId`, `type`, and future `imageId` safely;
- Page membership of a Fragment comes from `fragment.pageId`;
- diaries-web no longer requires a Marquee merely to resolve Page/Diary and chronological membership;
- a MARQUEE fragment with a temporarily absent marquee remains a valid fragment object and can produce a controlled unavailable-marquee state;
- no IMAGE fragment is authored yet.

## Scope

### Diaries Client

Update `src/app/model/fragment.ts`:

```text
pageId: number
type: 'MARQUEE' | 'IMAGE'
imageId?: number | null   // allow forward-compatible parsing if desired
```

Retain `marqueeId` during compatibility, but stop using it as the Page relationship.

Review `ModelContext` and Fragment workspace selection logic. Page -> Fragment navigation must be expressible independently of a Page -> Marquee lookup. Keep existing selected-marquee derivation by `Marquee.fragmentId` where useful.

Type-aware code must default conservatively for old retained messages during rolling deployment. If a fragment payload genuinely lacks `type` while old retained state is still possible, treat it as legacy MARQUEE only during the documented compatibility window.

### Diaries Web

Update:

```text
model/FragmentItem.java
projection/ResolvedFragment.java
projection/ProjectionSnapshot.java
projection/RelationshipDiagnostics.java
MQTT decoding/contract tests
```

Resolve:

```text
Fragment.pageId -> Page.diaryId -> Diary
```

independently from Marquee.

For `type=MARQUEE`, attach Marquee if available and verify `marquee.fragmentId == fragment.id`. Absence/inconsistency is diagnostic/render-state information, not a reason to erase the Fragment from date/month indexes.

Prepare `ResolvedFragment` for subtype-specific optional relationships, e.g. optional Marquee now and optional Image in 0026.

### MQTT Compatibility

No responder contract removal. Consumers accept 0022 additive fields and should ignore unknown future fields.

## Detailed Implementation Steps

- [x] Extend Angular Fragment model with pageId/type.
- [x] Add parsing/compatibility tests for old and new fragment payloads where appropriate.
- [x] Audit `ModelContext` for Page inference through Marquee and replace with Fragment.pageId.
- [x] Ensure selected marquee is still located by `fragmentId` for MARQUEE fragments.
- [x] Make marquee controls explicitly conditional on fragment type/available marquee even though all production rows are still MARQUEE.
- [x] Extend diaries-web FragmentItem decoder/model.
- [x] Rewrite ProjectionSnapshot resolution to start from Fragment.pageId.
- [x] Preserve date/sequence ordering unchanged.
- [x] Replace `fragmentsWithoutMarquee` diagnostics with more precise type-aware diagnostics.
- [x] Add projection tests for a MARQUEE Fragment with valid Page but missing Marquee: it remains in chronology and is flagged rather than discarded.
- [x] Run client tests/build and diaries-web tests/build against retained-contract fixtures.

## Acceptance Criteria

- [x] Existing reader/editor behaviour is unchanged for healthy MARQUEE data in automated coverage.
- [x] Both consumers treat Fragment.pageId as authoritative.
- [x] diaries-web does not drop an otherwise valid Fragment merely because no Marquee is present.
- [x] Page/Diary resolution no longer depends on `Marquee.pageId`.
- [x] Existing date and sequence ordering is unchanged.
- [x] All automated tests/builds pass.

## Implementation Result

Implemented on 2026-09-11. The Angular client now models migration-safe typed
Fragment ownership, navigates from `Fragment.pageId`, derives Marquees from
`Marquee.fragmentId` plus Page agreement, and prevents Marquee actions for
IMAGE or inconsistent selections. The read-only web projection now resolves
Fragment -> Page -> Diary before considering an optional Marquee, retains
Page-owned fragments in chronology when their Marquee is absent, and exposes
the more precise relationship diagnostics through its readiness response.

Compatibility is deliberately additive: a null/absent `type` is treated as
MARQUEE in one helper per consumer, null/absent `pageId` remains unresolved,
and `marqueeId` remains decoded and sent by the existing update RPC but is not
used as Page or Marquee relationship authority. Explicit IMAGE payloads decode
safely without enabling IMAGE authoring or first-class IMAGE rendering.

Automated evidence:

- diaries-client: 65 Angular tests passed;
- diaries-client: production build passed;
- diaries-web: tests passed;
- diaries-web: full build passed;
- `git diff --check` passed in the parent repository and both consumer repositories.

The full-stack/runtime smoke checks and deployment evidence in
`IMPLEMENTATION.md` remain manual release gates; they were not claimed by this
source implementation.

## Dependencies

Requires 0022 responder/database contract.

## Deployment and Rollback

Client and diaries-web can be rolled back independently while 0022 continues to publish compatibility fields. Do not remove old responder fields yet.
