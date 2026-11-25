# 0029-FEAT — Approved hybrid Diary-year Fragment ownership (2026-11-25)

**Decision:** Owner approved replacing the earlier mandatory-Page-for-all-Fragments model with exclusive ownership determined by placement. This decision supersedes the Page-centric 0029 design recorded earlier on 2026-11-25. It does **not** undo the approved TEXT/IMAGE type model, optional DATED Marquees or Catalogue Image captions.

## Rationale

The digital edition includes annual introductions and possibly concluding notes not printed on a physical Page. Attaching them to a first-January Page misrepresents ownership and risks rendering them *under* a date heading. A physical Page remains authoritative for ordinary DATED material, while annual material belongs to a particular Diary and calendar year.

## Decision table

| Placement | Owner | Page | Marquee | Display |
|---|---|---|---|---|
| PREAMBLE | Diary + year | NULL | prohibited | Above first date heading |
| DATED | Page (implies Diary) | Required | 0..1 | Under actual diary date heading |
| POSTAMBLE | Diary + year | NULL | prohibited | After last dated entry |

Types TEXT and IMAGE are independent of placement. Catalogue Image owns caption and alt text; IMAGE Fragment owns optional click link. Explicit Diary reference is required for annual content; `year` alone is not a unique Diary identity. The exact column/DTO representation must be audited and decided in the coherent implementation.

## Known record disposition

Preamble: 1828 IDs 1,2,3; 1829 387; 1830 806; 1831 1177; 1832 1563,1564; 1834 1926. These **stay Page-less** and must be linked to the verified Diary/year. DATED: 1738 → candidate Page 1005; 2061 → candidate Page 1078, both subject to guarded checks. Development-only extra 49 Page-less records require 0028 reconciliation. No real POSTAMBLE content is currently recorded; acceptance needs synthetic coverage.

Previous suggestion to attach 1/2/3 to Page 685 and 1563/1564 to Page 972 is **withdrawn/superseded**. Their desired reading order before 1 January is unchanged. Decorative 1828 introduction HTML may be simplified only with content/link preservation and original evidence archived.

## Status and change control

This report and accompanying architecture/README/plan edits document the **approved target**, not implemented schema/code, completed migration or production acceptance. Historical decisions are preserved as evidence rather than rewritten. No application code or production data is changed in this documentation package.
