# 0029 — Page-centred TEXT/IMAGE model decision (2026-11-25)

**Status: APPROVED TARGET / NOT YET IMPLEMENTED.**

## Decision

Every Fragment belongs to a Page and is of type TEXT or IMAGE. Either may have a zero-or-one Marquee locating original scanned material. The reusable Catalogue Image owns caption and alt text. An IMAGE Fragment has an independently optional occurrence-specific image-click link. Commentary not on original scanned Page still belongs to a Page.

## Evidence and blockers

2026-11-25 production: 11 Page-less Fragments, all containing text, none in 71-row 0028 source journal; 10 missing types. Development: 60 Page-less Fragments, including 49 not in production; 22 Marquee-associated untyped Fragments were corrected on development only. Fragment 1738 contains significant commentary and must be preserved. Before enforcing NOT NULL, identify/approve correct Page association for retained records, reconcile legacy embedded-image material and verify viewer behaviour.

Existing `Image.caption` and `Image.altText` confirm catalogue ownership in the supplied code; existing `Fragment.imageLinkUrl` confirms occurrence-specific link. Full MARQUEE→TEXT source, PostgreSQL and retained MQTT migration is pending, as are consolidated tests and deployment.

## Change-control

This report documents design decisions only; it is not migration success or a closed acceptance gate. No runtime code or SQL is modified by this documentation package.

## Supplementary decision — Placement (2026-11-25)

Approved target: `Fragment.placement` is `PREAMBLE`, `DATED`, or `POSTAMBLE`, independent of TEXT/IMAGE type and Marquee association. PREAMBLE appears before the first dated entry and its heading in the relevant diary year; POSTAMBLE appears after the final dated entry. No POSTAMBLE content exists yet. Ordinary existing Fragments migrate to DATED unless explicitly classified. The model retains mandatory Page ownership even for editorial material not visible on the physical page.

Approved initial PREAMBLE associations: 1828 Fragments 1, 2, 3 → Page 685 (`img2833`) before Jan 1 Fragment 4; 1832 Fragments 1563, 1564 → Page 972 (`img2982`) before Jan 1 Fragment 1565. The 1828 decorative HTML may be simplified while preserving text and useful hyperlinks. Implementation, migration and acceptance verification remain pending; no records have been changed by this report.
