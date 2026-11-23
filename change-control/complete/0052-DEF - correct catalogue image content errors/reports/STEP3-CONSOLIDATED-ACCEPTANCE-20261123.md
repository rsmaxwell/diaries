# 0052-DEF — Step 3 consolidated acceptance review (23 November 2026)

**Feature:** Correct catalogue image content errors (Whitley Park Image 3; Hermitage Image 18).  
**Status:** **STEP 3 AUTOMATED VERIFICATION PASSED; ACCEPTANCE OPEN.**  
**Closure:** **NOT AUTHORISED.** Keep 0052 under `change-control/in-progress/` until the remaining acceptance is documented and explicitly approved by the content owner.  
**Scope:** Documentation of already-executed work; this report authorises no database, Files, MQTT, source-image, or fragment changes.

## Evidence and provenance

This review consolidates the supplied 23 November terminal logs, earlier recorded Step 2 results, and the existing 0052 acceptance criteria. The source bundle available for inspection (`diaries-sources-20261123-082352.zip`) contains an earlier 0052 directory name and predates the subsequently applied verifier corrections. This report intentionally adds a **new** file to the current feature folder, and does not replace the current README, implementation plan, or private evidence. Step 2 details noted below are carried forward from prior execution reports; their full raw receipts were not included in the terminal logs reviewed for this report.

Key private evidence in the Windows Diaries parent checkout:

- Step 2 controlled replacement/rollback receipts: `evidence/Step 2/private/20261123T102932Z/` (from the preceding Step 2 review; retain unchanged).
- First Step 3 check: `evidence/Step 3/private/20261123T124810Z-consumers/` (failed due to verifier's erroneous `type='MARQUEE'` assumption for legacy fragments).
- Corrected SQL run: `evidence/Step 3/private/20261123T125536Z-consumers/` (12 database assertions passed; obsolete public Reader fragment=84 URL returned 404).
- **Accepted automated Step 3 run:** `evidence/Step 3/private/20261123T130110Z-consumers/` (12 database assertions and all configured HTTP checks passed). Preserve `RESULT.txt`, `development-consumers.txt`, `production-consumers.txt`, request headers, `git-identity.txt` and generated SQL in that directory.

Corrective documentation already added to this feature:

- `reports/STEP3-LEGACY-TYPE-CHECK-CORRECTION-20261123.md`
- `reports/STEP3-READER-HTTP-TARGET-CORRECTION-20261123.md`

## Completed automated checks — 2026-11-23 13:01 UTC

| Assertion | Development | Production |
| --- | --- | --- |
| Image 18 has no direct typed IMAGE fragment consumers | PASS — `(none)` | PASS — `(none)` |
| Legacy Fragment 84 (Whitley map) present with expected date/content reference, null type | PASS | PASS |
| Legacy Fragment 598 (Hermitage) present with expected date/content reference, null type | PASS | PASS |
| Protected Fragment 606 references St Isaac image | PASS | PASS |
| Image 3 direct consumers | PASS — `2338` | PASS — `2332,2334` |
| Production-only IMAGE Fragment 2334 / Marquee 2272 relationship | PASS — correctly `NOT_PRESENT` | PASS — present, page 692 |

**Total: 12/12 read-only database assertions passed.** The script performs a metadata fingerprint query, but does **not** independently compare the current fingerprints to the pre-change baseline for text, sequence, links, or Marquee geometry. These integrity claims require prior Step 1/2 evidence comparison or targeted browser inspection.

Production public Reader HTTP checks from the same successful run:

| URL/path | Result and limit |
| --- | --- |
| `https://pluto.rsmaxwell.co.uk/diaries-web` | HTTP 200 — Reader index reachable |
| `https://pluto.rsmaxwell.co.uk/diaries-web/diaries/1/1828/03?fragment=2334` | HTTP 200 — page-owned Whitley Image 3 route reachable; **not a visual check** |
| `https://pluto.rsmaxwell.co.uk/diaries-web/diaries/1/1829/07` | HTTP 200 — July 1829 month reachable; **does not establish Hermitage Fragment 598 is rendered** |

**Reader projection boundary:** Legacy Fragments **84** and **598** have null `page_id`; the public Reader's page-owned projection cannot resolve them directly. Their existing embedded-image HTML belongs to the separate 0028-FEAT migration workflow. The initial Reader 404 for `?fragment=84` was an invalid verification target, not demonstrated image-content loss. Do not try to make 0052 pass by changing their ownership, types or markup.

## Image changes and already-reported visual checks

- Step 2 was previously reported as applied and verified in **both production and development**. The existing catalogue identities **Image 3** (Whitley Park) and **Image 18** (Hermitage) were preserved; file/catalogue/retained MQTT reconciliation and rollback evidence were reported. This report makes no new live file/hash assertion beyond those prior receipts.
- The Hermitage selected PNG identity is `img2900-image-hermitage.png`, 720 × 480, 935,720 bytes, SHA-256 `9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0`. The final deployed copy should continue to match the Step 2 evidence.
- Step 2 reported unrelated **Image 25 / St Isaac** and **Image 21 / Jordan Staircase** unchanged by hash. The current Step 3 SQL rechecks St Isaac **Fragment 606's reference**, but does not rehash either protected file or establish visual correctness.
- The content owner previously reported correct Whitley Park and Hermitage presentation in the **development Editor and Reader**, and correct updated production presentation in the **Editor**. Treat these as reported browser observations, not as new screenshot receipts nor as proof of all public Reader/protected-image scenarios.
- Because legacy Hermitage Fragment 598 has no page ownership, its future public Reader migration is a **0028 acceptance matter**, not an outstanding 0052 database repair. Acceptance of this explicit limitation must be confirmed before 0052 is closed.

## Remaining acceptance — record before closure

| Gate | Current evidence | Required closeout |
| --- | --- | --- |
| Correct Whitley Map in **production public Reader**, Image 3 preview/full image, with browser refresh | Route HTTP 200; production Editor and development visuals previously reported | Owner verifies the page-owned Whitley presentation visually, including map geography. Confirm preview and full image are correct; record observation/date. |
| Hermitage Image 18 in production/development, catalogue preview and applicable Editor/Day Reader | Prior Step 2 file/catalogue/MQTT checks and earlier browser observations | Verify the already-observed screens cover catalogue preview and post-refresh rendering. Record that legacy Fragment 598 itself is not public-Reader-projectable until 0028. No forced 0052 migration. |
| Protected St Isaac (Image 25, Fragment 606) and Jordan Staircase (Image 21) | Step 2 reported unchanged hashes; Step 3 confirms 606 reference | Owner performs a short visual sanity check and records result, or clearly documents accepted reliance on Step 2 integrity evidence. |
| Fragment text, link click-through, optional Marquee, order | Identity/relationship checks PASS; production 2334/2272 PASS | Compare Step 3 private metadata fingerprints with accepted Step 1/2 baseline where applicable, plus short targeted browser behaviour check; do not claim a complete text/geometry diff based on HTTP 200. |
| Reader/application health and cache | Production Reader routes HTTP 200; prior browser refresh/reconnect and responder/MQTT checks reported | Reuse those accepted health/cache receipts; only investigate a newly observed problem. |
| 0028 frozen-review impact | Image 18 corrected; legacy Fragment 598 is a known pending review candidate | Preserve original frozen 0028 inventory and draft (91). Create/record an updated **review** against current identity for affected candidates (especially 598) in 0028's own workflow; no migration/approval implied. See companion handoff report. |
| Owner acceptance / change-control closure | Not yet recorded | Record explicit visual/regression acceptance and owner approval; only then close Step 3 and move feature from `in-progress` to `complete`. |

### Short owner browser acceptance record (complete only after checking)

- [ ] Production public Reader, **20 March 1828**: map for page-owned Fragment **2334** looks correct after refresh; its click/highlight/Marquee behaviour remains usable.
- [ ] Production/development catalogue previews and relevant Editor/Day Reader views: Whitley **Image 3** and Hermitage **Image 18** display the approved distinct pictures; no stale copy remains.
- [ ] **St Isaac** and **Jordan Staircase** still show their correct, separate pictures; unaffected links/order acceptable.
- [ ] Legacy **84** and **598** remain preserved and are intentionally not treated as directly selectable public Reader fragments pending 0028.
- [ ] Accepted pre/post text/link/order/Marquee integrity evidence is identified, or any gap explicitly accepted by the owner.
- [ ] 0028 impacted-review handoff is acknowledged with original frozen review retained.
- [ ] **Content owner explicitly approves formal closure of 0052-DEF.**

**Disposition as of this report:** automated Step 3 passed; remaining acceptance items above are **OPEN / NOT YET RECORDED**. Do not mark the feature CLOSED or move its directory on the strength of this report alone.
