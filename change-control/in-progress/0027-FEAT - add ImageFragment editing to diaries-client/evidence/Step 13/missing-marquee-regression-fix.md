# Step 13 live regression — Day-reader MARQUEE selection loses the overlay

## Observation

During live Step 13 fixture setup, selecting Fragment 4 from the Day reader changed the selected Fragment and loaded the correct source page, but the Marquee rectangle was not selected/rendered. The source-page Marquee list itself was healthy: direct pointer selection of Marquee 1 subscribed to both `diaries/marquees/1` and `diaries/fragments/4`. Later Day-reader selection subscribed to `diaries/fragments/4` but did not subscribe to `diaries/marquees/1`.

A preceding route transition had invoked `ModelContext.cleanupTopicTree()`.

## Root cause

`ModelContext` owns a root-lifetime synchronization from `selectedFragment$ + marquees$` to `marqueeId`. The synchronization was incorrectly guarded by `takeUntil(this.destroy$)`, while `cleanupTopicTree()` called `destroy$.next()` and `destroy$.complete()`. The first route/topic cleanup therefore permanently killed that synchronization even though the root `ModelContext` instance continued to be reused.

At the same time, `DayviewComponent.goToFragment()` unconditionally called `setMarqueeId(null)`. Once the root synchronizer had died, there was no remaining code to restore the correct Marquee for a selected MARQUEE Fragment.

## Correction

- Remove the `destroy$`/`takeUntil` lifecycle coupling from the root Fragment→Marquee relationship synchronizer.
- Treat `cleanupTopicTree()` strictly as MQTT topic-tree/cache cleanup.
- Remove the direct `setMarqueeId(null)` call from `DayviewComponent.goToFragment()`.
- Keep `ModelContext` as the single relationship authority:
  - MARQUEE + authoritative page → match Marquee by `fragmentId + pageId`;
  - IMAGE → `marqueeId=null`;
  - unresolved/legacy page → `marqueeId=null`.

This intentionally does not derive relationship authority from `Fragment.marqueeId`, preserving the rolling-migration compatibility rule already frozen by 0027.

## Regression coverage

`model-context.spec.ts` now verifies both relationship outcomes after `cleanupTopicTree()`:

1. a MARQUEE Fragment still resolves its retained Marquee;
2. an IMAGE Fragment still clears a previously selected Marquee.

`dayview.component.spec.ts` now verifies that Day-reader navigation changes the Fragment/page route but never writes Marquee state directly.

## Live re-verification required

Before resuming the formal gate-disabled Phase A sequence:

1. run `npm test -- --watch=false --browsers=ChromeHeadless`;
2. reload the client;
3. select a MARQUEE entry in the Day reader and confirm its rectangle appears;
4. select the disposable IMAGE entry and confirm no rectangle is selected;
5. select the MARQUEE entry again and confirm the rectangle reappears.

Step 13 remains open until this smoke check and the two formal live phases complete.
