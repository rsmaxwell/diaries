# 0028 — Step 1/2 acceptance recommendation (not a closure record)

**Prepared 24 November 2026. Not an owner signature.**

## Step 1 technical case

The reviewed legacy 72-occurrence baseline contains 71 confirmed IMAGE conversions and one explicit deferral, Fragment 1564. Preserve 30 pre-existing links and 22 same-Page Marquees. The 23 November post-0052 read-only reconciliation and exact prepared manifest receipt passed. The historic 0022/0024 source-evidence availability gap is documented; the 23 November current-schema read-only production inventory is the actual reviewed baseline. Formal Step 1 owner acceptance is not yet recorded.

## Step 2 technical and observed GUI case

- Responder Gradle/JUnit and Java manifest validation passed.
- Isolated production-data PostgreSQL rehearsal proved 71/71 in-place IMAGE conversions, rollback per date, independent journal readback, repeat apply/idempotence, unchanged unrelated rows, and explicit unchanged Fragment 1564.
- MQTT retained replay: 71 Fragment topics and 22 Marquee topics verified, with source image/page/links/captions preserved.
- Reader and Editor integration, original image scans, isolated sign-in, Page/Fragment navigation and representative migrated IMAGE records 598, 606 and 1251 were observed working.
- The owner confirmed ordinary clicking the preserved link on Fragment 1251 opens the saved Google Maps URL. An additional Street View direction-arrow click is needed to reach the intended photograph; no unapproved URL edit should be included in 0028.
- The unrelated undo-to-original Fragment lock-release issue is logged as 0053-DEF. The owner confirmed the navigation-away workaround, so 0028's known locking observation can be accepted without claiming that 0053 is fixed.

Recommendation: accept Step 1 and Step 2 technical results as sufficient when the owner confirms, but retain Step 3 and Step 4 as **OPEN**. No production apply, snapshot mutation or feature closure is authorised by this recommendation.
