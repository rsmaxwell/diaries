# Step 2 — Reader TEXT contract candidate (2026-11-25)

**Status: candidate, not deployable.** Based on `diaries-sources-20261125-123246.zip`.

This increment decodes `type=TEXT` as a known type, projects page-associated TEXT without a Marquee as valid, and adds focused reader contract/projection tests. The historic `MARQUEE` interpretation is temporarily retained **only because current production retained payloads still use it**. This is not the final migration contract and must be removed/updated in the coordinated cutover.

**Not yet implemented:** `placement`, explicit Diary ownership of year-level Fragments, reader projection for Page-less PREAMBLE and POSTAMBLE, related HTML views, editor create/edit/order/lock operations, responder RPCs, retained-topic changes, schema migration, and Marquee Page-column retirement. Do not deploy this incremental reader code or run Step-2 SQL in isolation.

**Verification:** archive and source invariants checked locally; full Java 25 build/test unavailable in this environment (Java 21 installed). Run consolidated tests only after integration. This change is narrowly aimed at eliminating one false assumption, not closing Step 2.
