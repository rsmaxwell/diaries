# 0023-FEAT - Make consumers use typed fragment page ownership

## Type

Feature

## Status

To do

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

- [ ] Extend Angular Fragment model with pageId/type.
- [ ] Add parsing/compatibility tests for old and new fragment payloads where appropriate.
- [ ] Audit `ModelContext` for Page inference through Marquee and replace with Fragment.pageId.
- [ ] Ensure selected marquee is still located by `fragmentId` for MARQUEE fragments.
- [ ] Make marquee controls explicitly conditional on fragment type/available marquee even though all production rows are still MARQUEE.
- [ ] Extend diaries-web FragmentItem decoder/model.
- [ ] Rewrite ProjectionSnapshot resolution to start from Fragment.pageId.
- [ ] Preserve date/sequence ordering unchanged.
- [ ] Replace `fragmentsWithoutMarquee` diagnostics with more precise type-aware diagnostics.
- [ ] Add projection tests for a MARQUEE Fragment with valid Page but missing Marquee: it remains in chronology and is flagged rather than discarded.
- [ ] Run client tests/build and diaries-web tests/build against a 0022 responder/topic-tree fixture.

## Acceptance Criteria

- [ ] Existing reader/editor behaviour is unchanged for healthy MARQUEE data.
- [ ] Both consumers treat Fragment.pageId as authoritative.
- [ ] diaries-web does not drop an otherwise valid Fragment merely because no Marquee is present.
- [ ] Page/Diary resolution no longer depends on `Marquee.pageId`.
- [ ] Existing date and sequence ordering is unchanged.
- [ ] All tests/builds pass.

## Dependencies

Requires 0022 responder/database contract.

## Deployment and Rollback

Client and diaries-web can be rolled back independently while 0022 continues to publish compatibility fields. Do not remove old responder fields yet.
