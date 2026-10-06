# Step 13 live defect — Fragment create did not normalise chronology

## Observation

During gate-enabled Phase B, IMAGE Fragment `2333` was created successfully against Image `89`. When the responder was restarted for the retained-state verification, startup normalisation adjusted additional Fragment sequence numbers. This proved that creation had committed a chronology that still depended on startup repair.

The same lifecycle omission existed in both creation handlers:

- `addImageFragment` persisted the requested fractional/gap insertion sequence and published the new Fragment only;
- legacy MARQUEE `addFragment` persisted the requested insertion sequence and published the new Fragment/Marquee only.

`updateFragment` already normalised affected dates, and the earlier Step 13 delete fix added the same invariant to `deleteFragment`.

## Required invariant

Every successful Fragment chronology mutation must leave the database and retained topic tree normalised immediately:

- create MARQUEE Fragment;
- create IMAGE Fragment;
- update date or sequence / drag-drop reorder;
- delete Fragment.

A responder restart must never be required to close a gap or replace a fractional insertion sequence with the canonical contiguous sequence.

## Implementation

RPC creation now uses two handler-facing `DiaryContext` operations:

- `saveMarqueeFragmentAndNormalise(...)`;
- `saveImageFragmentAndNormalise(...)`.

Each operation owns one transaction. It validates the new Fragment shape, creates the Fragment (and Marquee for MARQUEE, or locks/resolves the Image reference for IMAGE), runs `FragmentSequenceNormaliser.normaliseDate(...)`, and commits only if the whole operation succeeds.

After commit, the created Fragment is reloaded so its returned sequence/version exactly match the database. `FragmentCreationResult` carries that committed created state plus every Fragment renumbered by normalisation. `FragmentSequenceNormaliser.publishCreation(...)` de-duplicates by Fragment id and republishes the final created Fragment plus every changed survivor to both canonical and date retained topics. MARQUEE creation then publishes the new Marquee hierarchy as before.

The older `saveMarqueeFragment(...)` and `saveImageFragment(...)` persistence helpers are intentionally retained unchanged for test/seeding callers; the live RPC handlers use the new atomic create+normalise operations.

## Regression coverage

`FragmentLifecycleContractTest` now covers both create paths by inserting into the middle of a mixed chronology. Each test requires:

- one transaction / one commit;
- the new Fragment and every later survivor to have contiguous canonical sequences immediately;
- changed sequence rows to receive incremented versions;
- canonical and date retained Fragment payloads to agree;
- IMAGE creation to leave the catalogue Image untouched;
- MARQUEE creation to retain the normal Fragment + Marquee topic contract.

The existing delete-time regression remains in the same suite, so create and delete chronology closure are checked together.

## Development validation

Run from the Diaries project root:

```powershell
.\gradlew.bat :diaries-responder:test `
  --tests com.rsmaxwell.diaries.responder.handlers.FragmentLifecycleContractTest `
  --tests com.rsmaxwell.diaries.responder.handlers.AddImageFragmentTest `
  --tests com.rsmaxwell.diaries.responder.handlers.AddFragmentContractTest `
  --no-daemon
```

Then restart the gate-enabled responder, create a disposable IMAGE Fragment in the middle of the Phase B day, and capture state immediately before any responder restart. The date must already be contiguous in PostgreSQL and retained MQTT state.

## Focused-test alignment correction — 2026-10-05

The first development focused-test run exposed a test-fixture type mismatch in
`addingMiddleMarqueeFragmentNormalisesAndPublishesSurvivingChronology()` before
it could exercise the new MARQUEE creation normalisation path. The test supplied
`sequence` as the String `"2.5000"`, whereas the established `AddFragment`
contract reads sequence through `Utilities.getBigDecimal(...)`, which requires a
`Number`. The IMAGE handler deliberately accepts either a Number or a String, so
its corresponding test was valid.

The MARQUEE lifecycle test now supplies `new BigDecimal("2.5000")`, matching the
existing `AddFragment` RPC argument contract. No production source was changed
by this correction; it is test-contract alignment only.
## Final validation — 2026-10-05

After the focused-test alignment correction, the development workstation command covering `FragmentLifecycleContractTest`, `AddImageFragmentTest` and `AddFragmentContractTest` completed `BUILD SUCCESSFUL in 5s`.

The live proof then inserted disposable IMAGE Fragment `2334` / Image `89` into the middle of the mixed 1828-01-01 chronology. The entire day was immediately contiguous before any responder restart. Deleting `2334` also immediately left the surviving day contiguous. Final status: **PASS**.
