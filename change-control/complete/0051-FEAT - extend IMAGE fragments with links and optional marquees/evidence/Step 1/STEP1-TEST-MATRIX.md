# 0051 — Step 1 baseline and downstream regression matrix

**20 November 2026.** Synthetic fixtures only. A test described below is **not passed** unless an attached runtime result confirms it. The read-only source audit is a separate activity, not a substitute for application tests. No 0028 private fragments/URLs belong in test fixtures.

## Synthetic fixture vocabulary

* Page P=11 (Diary D=1), different Page Q=12; Image A=91 and Image B=92; Fragment F=301 (type IMAGE, pageId 11), G=302 (IMAGE) referencing shared Image A, H=303 (MARQUEE), L=304 (type null legacy); Marquee M=401 (`fragmentId=301`, `pageId=11`, geometry 10,20,90,60, version 4).
* Safe destination U1=`https://example.invalid/maps/?x=1&y=%2F#photo`, U2=`http://example.invalid/old?ref=a%26b`, U3=`https://example.invalid/other?q=%C3%A9`. None requires any network fetch.
* Four primary combinations: `(link=null, marquee=null)`, `(U1,null)`, `(null,M)`, `(U1,M)`; add missing Image reference and same-catalogue-Image/different-link cases.

## Test IDs and expected outcomes

| ID | Area | Synthetic exercise | Required outcome/evidence | Stage |
|---|---|---|---|---|
| S01 | Existing data | IMAGE without link/Marquee | Plain image; original navigation and DB/retained unchanged | 1 baseline, 2–4 |
| S02 | Existing data | MARQUEE+legacy type-null & mixed IMAGE/MARQUEE day | Page selection, rectangle and chronology preserved | 1 baseline, 2–4 |
| S03 | Current exclusion | Attempt `ResolvedFragmentState.validateForWrite()` with IMAGE+M in unmodified sources | Current rejection documented, then accepted with same-Page in Step 2 | 1 baseline, 2 |
| S04 | Current UI | Day reader IMAGE A, imageId absent, MARQUEE and legacy | Existing `Image 91`/`No Image selected`, later `Image ID: 91` only on IMAGE | 1 baseline, 3 |
| U01 | Link set | Save U1 to F under valid version+lock | Exact URL in DB, RPC and both retained topics; image wrapped and focusable | 2–3 |
| U02 | Link preserve | Text/date/order/reference/lock/Marquee update omits URL | U1 unchanged, including after reconnect/replay | 2–4 |
| U03 | Link clear | `clearImageLinkUrl:true` and omitted URL | URL NULL in DB and retained; image plain, no stale link | 2–4 |
| U04 | Combined clear | `imageId:null`, `clearImageLinkUrl:true` | Adapter dispatches, both clear in one authorised transaction | 2 |
| U05 | Invalid | `javascript:`, `data:`, `//host`, relative, `http:///`, `%ZZ`, control, whitespace, userinfo, >4096 | Reject with no DB/retained mutation; error shown to editor | 2–3 |
| U06 | Encoding | U1/U2/U3 with `&`, `%XX`, `#fragment` and Unicode | Semantic URL preserved, HTML escaped once, no external fetch at write | 2–3 |
| U07 | Shared Image | F and G reference A but have distinct U1 and U2 | Occurrence-specific links, catalogue Image A untouched | 2–3 |
| U08 | Dormant link | F has U1 but `imageId:null` or unresolved metadata | URL editable in authoring; no false clickable media; later attach makes U1 visible | 2–3 |
| U09 | Auth/concurrency | Unauthorised, stale version, competing lock and failed transaction | Rejected; unchanged URL, lock policy and retained messages | 2 |
| M01 | Attach | Add M to IMAGE F with matching Page and lock/version | F stays IMAGE, A/U1 unchanged, exactly one linked M | 2–3 |
| M02 | Reconcile | M exists before IMAGE type migration | M id/version/coordinates/Page and established retained topic unchanged | 2, 4 |
| M03 | Geometry | Edit M under owner lock and correct version | Existing identity/Page unchanged, new geometry/version published | 2–3 |
| M04 | Remove | Delete M from IMAGE F with correct version/lock | F retains IMAGE, A, U1, Page; only M topics tombstoned | 2–3 |
| M05 | Bad association | Marquee has Page Q, duplicate for F, wrong Fragment or stale version | Rejected without reparent, geometry alteration or extra retained topic | 2 |
| M06 | Delete Fragment | Delete F with M while G still references A | F+M tombstoned after commit; G, Image A and bytes preserved; survivor sequence normalised | 2–4 |
| M07 | Legacy continuity | Existing MARQUEE create/update/delete RPC with old request shape | No regression or unplanned breaking API before old writers upgraded | 2–4 |
| R01 | MQTT ordering | Marquee before Fragment, Image metadata later, tombstone and reconnect | Eventually consistent projection; valid relationships recovered, not auto-deleted | 2–4 |
| R02 | Day reader | F with M/U1, Image metadata absent, replace/clear Image | `Image ID: N` after Position from `imageId` only; null fallback; ordering stable | 3 |
| R03 | Month/source web | All four combinations; click image vs source-page control | Click goes to link in same tab; highlight uses M separately; keyboard works | 3–4 |
| R04 | Missing media | Image file fails to load or metadata absent | Honest missing-media state and file fallback; no misleading external link | 3 |
| R05 | Responsive events | Mobile, pointer, tab/Enter, editor drag/reorder | No mixed selection/link navigation or scroll/zoom regression | 3–4 |
| D01 | Schema | Existing DB migration applied twice on isolated restored data | Repeatable add, preserved rows/constraints, old-data reads | 2, 4 |
| D02 | Activation/rollback | Upgrade writer/reader, leave existing IMAGE gate unchanged; use separate extension switch; fallback before/after first extension write | Existing IMAGE authoring continues; no extension writes with old consumers; rollback cutoff demonstrated | 4 |
| H01 | Migration handoff | Synthetic 0028 HTML anchor + IMAGE/Marquee preservation | URL decoded once; ID/geometry/HTML hashes retained; no production mutation/signoff | 4 |

## Evidence ledger

* **Completed before this ZIP:** Windows repo/submodule baseline and selected source-hash inventory in supplied evidence; an earlier private production-container baseline file is present but not live verified during this review.
* **Completed by this ZIP:** documented cross-component source audit and executable read-only static baseline checks with a local check report (historical characterisation, expected to fail once Step 2 deliberately removes old guards); see `evidence/Step 1/step1-static-baseline-results.txt`.
* **Step 1 CLOSED, 20 November 2026:** owner accepted the cross-component contract and existing-code testing boundary after live read-only schema/authoring inspection and selected Cygwin regression tests. All new-feature database/MQTT integration and deployment rows remain untested (Steps 2–4).
