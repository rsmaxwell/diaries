# 0026 final acceptance-to-evidence matrix

| Final acceptance criterion | Result | Evidence |
| --- | --- | --- |
| Read-only web consumes all five canonical retained entity families with minimum ACLs. | PASS | Step 4 exact filters/ACL integration; Step 12 real MQTT/ACL; Step 15 production ACL and runtime capture. |
| Image metadata and tombstones participate in immutable snapshots and atomic reconnect replay. | PASS | Steps 5–6 projection lifecycle; Step 12 replay/tombstone/reconnect; Step 13 responder/web restart. |
| Every otherwise valid Page-owned IMAGE remains in date/month/source-page chronology, including missing media. | PASS | Steps 6, 8, 9 and 11; Step 13 missing-metadata/file fixture. |
| `Fragment.pageId` remains the ownership authority; ordering is unchanged. | PASS | Steps 6 and 8; Step 13 mixed Page/date fixture. |
| IMAGE shows Page context, text and optional referenced Image, with no selected Marquee. | PASS | Steps 8–10; Step 13 browser verification. |
| MARQUEE rendering and legacy null-type compatibility remain intact. | PASS | Steps 3, 6 and 9–11; Step 14 regression; Step 15 production MARQUEE smoke. |
| Invalid cross-type relationships and unknown explicit types have distinct diagnostics and safe rendering. | PASS | Steps 3, 6 and 11. |
| Runtime configuration alone determines Files URLs; paths are validated and encoded safely. | PASS | Step 7 focused tests; Step 11 security coverage; Step 15 `filesPath=files` and Files-route production smoke. |
| Caption/alt text are escaped, aspect ratio is preserved, and unavailable media has accessible text. | PASS | Steps 2, 9 and 11; Step 13 browser verification. |
| Keyboard selection, focus, deep links and browser history work across both types. | PASS | Step 10 focused behavior; Steps 11 and 13 browser verification. |
| Shared Images, updates, tombstones and late metadata affect every reference without catalogue duplication. | PASS | Steps 5–6, 11–13. |
| HTML sanitization, CSP and GET/HEAD-only behavior remain effective. | PASS | Steps 7, 9 and 11; full regression in Step 14. |
| Full web tests/build, real MQTT/ACL integration and controlled browser deployment checks pass. | PASS | Step 12 MQTT integration; Step 13 controlled run; Step 14 final regression/artifact gate. |
| Exact published reader artifact/configuration is verified before production authoring enablement. | PASS | Step 14 exact candidate; Step 15 deployed tag/image IDs/config hashes on `pluto`. |
| Production gate/rollback state and 0027/0028 handoff are recorded; no unrelated legacy conversion/destructive cleanup occurred. | PASS | Step 15 gate/zero IMAGE rows/rollback evidence; Step 16 handoff. |
| Change-control evidence contains reproducible commands, source/artifact identities and actual results. | PASS | Evidence Steps 1–16; Step 14 commands/results; Step 15 capture scripts and checksums; Step 16 release identity. |

## Regression/test summary used for close-out

- Step 14 `diaries-web`: clean full test/build and fat-JAR generation passed.
- Step 14 `diaries-responder`: full test/build passed.
- Step 14 `diaries-client`: 132/132 unit tests passed and production build passed.
- Step 14 fresh Step 13 cross-component verification: passed against exact responder/web candidate artifacts.
- Step 15 production deployment: all five services healthy; reader readiness/root/about/MARQUEE/File-route checks passed; authoring gate remained disabled.

No Step 16 runtime test rerun is required because Step 16 changes only close-out documentation/state and downstream handoff text; the exact runtime candidate was already frozen/tested in Step 14 and deployed/verified in Step 15.
