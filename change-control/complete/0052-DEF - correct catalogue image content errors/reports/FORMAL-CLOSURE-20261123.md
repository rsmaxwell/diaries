# 0052-DEF — Formal closure decision (23 November 2026)

**Owner decision:** FORMAL CLOSURE APPROVED on **23 November 2026**. **Steps 1–3: CLOSED** on the basis of the recorded evidence and explicit content-owner acceptance. The approved archive location is `change-control/complete/0052-DEF - correct catalogue image content errors/`. 0028-FEAT remains **IN PROGRESS**; this closure does not approve or perform its migration.

## Closure authority and accepted qualifications

The content owner explicitly stated on **23 November 2026**: **“Yes I am satisfied on both of the above items, and I approve of the formal closure of 0052-DEF.”** This answers the two questions in `reports/STEP3-CLOSURE-READINESS-20261123.md`:

1. **Protected images:** the owner accepts the existing unchanged-hash evidence for **St Isaac Image 25** and **Jordan Staircase Image 21**, without another visual inspection.
2. **Other content and behaviour:** the owner accepts the available regression evidence for existing text, links, Marquees, and ordering. This is an explicit acceptance of the documented limits; it is **not** a claim that a complete independent before/after metadata-fingerprint diff or every browser interaction was rerun.
3. **Formal decision:** the owner explicitly approves **0052-DEF closure**, retaining the four missing legacy Reader fragments as mandatory 0028 acceptance work.

## Completed 0052 work and evidence

| Component | Accepted outcome | Evidence/provenance |
| --- | --- | --- |
| Whitley Park catalogue **Image 3** | Approved updated map reported served in production and development; source/catalogue/Files/MQTT reconciliation and rollback information previously recorded | Step 1–2 inventory and execution evidence; `reports/STEP3-CONSOLIDATED-ACCEPTANCE-20261123.md` |
| Hermitage catalogue **Image 18** | Approved distinct Hermitage PNG reported served in production and development, without changing catalogue identity | Step 2 receipts; Hermitage selected PNG SHA-256 `9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0` |
| Development and production consumer/relationship checks | **12/12 PASS** | `evidence/Step 3/private/20261123T130110Z-consumers/RESULT.txt`, `development-consumers.txt`, `production-consumers.txt` |
| Production public Reader HTTP checks | **PASS**: index, page-owned Whitley Fragment 2334 route, July 1829 month route | Same Step 3 run. HTTP 200 is a route check, not proof of image rendering |
| Production public Reader visual observation | Owner confirmed corrected Whitley map shown by new-style Fragments **2332 and 2334** | `reports/STEP3-OWNER-READER-OBSERVATION-20261123.md` |
| Other UI checks | Owner previously confirmed corrected Whitley and Hermitage images in development Editor/Reader and production Editor | Existing owner browser observations carried into `reports/STEP3-CLOSURE-READINESS-20261123.md` |
| Protected files and other content | Previously reported unchanged image hashes, passing St Isaac legacy-reference check, and existing text/link/Marquee/sequence evidence **accepted by owner** | `reports/STEP3-CLOSURE-READINESS-20261123.md`; complete fingerprint baseline comparison was not independently performed in this closure review |

The previous Step 2 raw evidence and rollback receipts under `evidence/Step 2/private/20261123T102932Z/` were **not independently re-audited** during the documentation-only closeout. Keep them, all Step 1–3 raw records and prior failed verifier traces intact as historical evidence. The first Step 3 legacy-type check and obsolete legacy Reader URL produced false failures; subsequent corrections and the successful run are separately documented. No new live repairs, restarts, database writes or MQTT changes are authorised by this record.

## Accepted 0028 dependency — do not lose this gate

The production public Reader currently **does not display** legacy Fragments **84, 598, 599, 600**. This limitation is **accepted for 0052 only**, on the condition that after 0028-FEAT converts those fragments, all four images appear correctly in both the Editor and the public Reader. The existing review draft (subject to reconciliation before 0028 execution) maps:

- **84 → Image 3 (Whitley Park), Page 692**; preserve the updated map and existing new-style 2332/2334.
- **598 → Image 18 (Hermitage), Page 752**; final v2 review confirmation was pending in the supplied draft.
- **599 → Image 21 (Jordan Staircase), Page 752**; do not conflate with Hermitage Image 18.
- **600 → Image 20 (Hermitage front), Page 752**.

0028 must preserve approved captions, links, order and applicable Marquees, and independently verify real rendering after migration. A month HTTP 200 alone is insufficient. The explicit 0028 handoff record is at:

`change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/reports/0052-READER-VISIBILITY-ACCEPTANCE-HANDOFF-20261123.md`.

Original 0028 frozen review evidence remains authoritative as historical evidence; refresh the affected review identities in 0028 without rewriting frozen records. This approval is **not** an approval or execution of 0028, nor of 0029.

## Administrative disposition

- **Step 1 — Inventory and approve replacement:** CLOSED (accepted earlier evidence).
- **Step 2 — Controlled catalogue corrections:** CLOSED (accepted prior deployment, verification and rollback evidence).
- **Step 3 — Consolidated acceptance:** CLOSED (2026-11-23 13:01 UTC read-only checks passed; owner visual and regression acceptance, and explicit closure approval recorded 2026-11-23).
- **Defect 0052:** **FORMALLY CLOSED, owner approved 2026-11-23.** The feature folder is to be moved intact from `change-control/in-progress/` to `change-control/complete/` by `tools/close-0052-formally.sh` on the authoritative Windows checkout. The actual filesystem move is evidenced only by that command's output and the resulting Git working tree, **not by the existence of this report alone**.
- Preserve all reports, tests, tools, logs, private evidence, rollback material, and uncommitted work. Do not auto-commit, push, prune or delete evidence. No source/application/Playbooks deployment is part of this administrative move.

**Sources for the decision:** content-owner acceptance in this conversation (23 November 2026); successful verifier output timestamp `20261123T130110Z`; `reports/STEP3-CLOSURE-READINESS-20261123.md`, `reports/STEP3-OWNER-READER-OBSERVATION-20261123.md`, `reports/STEP3-CONSOLIDATED-ACCEPTANCE-20261123.md`, and the 0028 handoff. The Windows checkout post-move must be inspected before the archive publication is considered physically applied.
