# 0027 final acceptance matrix

| Completion criterion | Final evidence |
| --- | --- |
| Create an ImageFragment from a catalogued Image | Step 13 development lifecycle and Step 15 production Fragment 2331 creation |
| Attach / replace / clear an existing Image reference | Step 13; Step 15 Image 1 → 31 → null → 1 lifecycle |
| Ordinary text/date/sequence edits preserve Image reference | Step 13 RPC diagnostics/regressions; Step 15 ordinary edit preserved `imageId=1` |
| MARQUEE behavior unchanged | Step 13 Angular/responder regression; Step 15 disabled-gate MARQUEE smoke |
| Mixed Fragment reorder works | Step 9/12/13 regression and Step 14 integrated gate |
| Fragment lock/version rules respected | Step 8/9/11/13 client+responder tests and live lifecycle |
| Delete Fragment does not delete reusable Image | Step 10/13; Step 15 cleanup left Image 1 catalogue/topic/file intact |
| Delete Image blocked while referenced | Step 13 and Step 15 Image 1 delete guard |
| Disabled authoring gate handled correctly | Step 11 diagnostics; Step 13 Phase A; Step 15 disabled-gate 403 smoke |
| Development live-MQTT verification complete | Step 13 `FINAL-RUNTIME-CLOSEOUT.md` |
| Client/responder/reader regression complete | Step 14 run `20261006-093834` PASSED |
| Production rollout/post-enable verification complete | Step 15 run `20261006-133404` and `MANUAL-EVIDENCE.md` |
| Architecture/operating documentation complete | Step 16 durable docs and SHA inventory |
| Feature-only tooling kept out of live script dirs | Step 16 tooling classification/static validation |

All feature completion criteria are satisfied; 0027 is eligible for `change-control/complete`.
