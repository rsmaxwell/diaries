# Step 2 — Angular annual Fragment contract candidate (25 November 2026)

Source baseline: `diaries-sources-20261125-123246.zip`, before any Step 2 application candidates.

This candidate introduces explicit `FragmentPlacement`, optional `diaryId` and a pure annual ownership/ordering utility. `MARQUEE` is still accepted by the old editor code while `TEXT` is recognised, so existing UI paths remain source-compatible. For new annual Fragments the utility rejects a Page or Marquee and requires a Diary/year. Stable ordering uses sequence followed by Fragment ID. Topic filters are scoped to a single Diary/year/placement.

**Scope limit:** This is *not* annual editing UI, MQTT subscription wiring or RPC implementation. No database migration or production changes. The new pure utility must be connected to ModelContext and a year-level Dayview workflow as part of the integrated release. The schema candidate and previous responder/reader candidates are not safe to deploy independently.

Verification: global TypeScript compiler passed for `fragment.ts` and `annual-fragments.ts` with strict mode, ES2022/DOM. Angular Karma/Jasmine suite was not available in this environment; the Jasmine spec is provided for execution on the Windows checkout. No Git metadata was included in the source bundle; verify Windows working-tree status before applying code.
