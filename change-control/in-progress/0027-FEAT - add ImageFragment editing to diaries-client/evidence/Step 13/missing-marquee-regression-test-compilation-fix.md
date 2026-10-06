# Step 13 — missing-Marquee regression test compilation follow-up

Date: 2026-10-04

## Live result

After applying the missing-Marquee production fix, the focused browser check passed:

- selecting a MARQUEE Fragment from Day reader displayed its Marquee;
- selecting the disposable IMAGE Fragment removed the Marquee selection;
- selecting the MARQUEE Fragment again restored its Marquee.

This is the intended MARQUEE → IMAGE → MARQUEE state transition.

## Test compilation failure

The subsequent Angular test invocation reached TypeScript compilation but failed in the newly-added `ModelContext` regression test:

```text
TS2345: Argument of type '30' is not assignable to parameter of type 'Expected<null>'.
model-context.spec.ts:147
expect(selectedMarqueeId).toBe(30);
```

The shell command also used `ChromeHeadlesss` rather than `ChromeHeadless`; that typo was not the cause of this compile failure because compilation stopped before browser launch.

## Cause

The test initialized a callback-mutated local variable to `null`. TypeScript control-flow analysis does not assume an Observable subscription callback has executed before the later assertion, so Jasmine's generic expectation was inferred from the currently narrowed `null` state.

## Correction

The test now records all emitted Marquee IDs in `Array<number | null>` and asserts the most recent value:

```ts
const selectedMarqueeIds: Array<number | null> = [];
const subscription = context.marqueeId$.subscribe(id => selectedMarqueeIds.push(id));
...
expect(selectedMarqueeIds.at(-1)).toBe(30);
```

This changes test typing only. There is no production-code change and no change to the intended lifecycle assertion.

## Verification in packaging environment

- changed TypeScript test file parses successfully with TypeScript 5.8.3;
- full Angular/Karma execution remains to be rerun in the development workstation tree with installed dependencies.
