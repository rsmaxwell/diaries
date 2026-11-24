# 0028-FEAT — Step 3 preparation and production execution gates

**Prepared:** 24 November 2026. **Status: OFFLINE READINESS PLAN, not authorisation to touch production.**

## Fixed migration scope and existing accepted evidence

The frozen reviewed source has **72 occurrences in 72 Fragments**: 71 approved in-place `CONVERT_TO_IMAGE` actions, one explicit `DEFER` (Fragment 1564), 30 exact preserved image links, and 22 preserved existing Marquees. All 71 conversions have one embedded image each. The implementation intentionally does not support speculative multi-image splitting for this reviewed batch; encountering an unreviewed action must fail closed.

The restored-production 0028 database rehearsal, rollback/restart/idempotence, isolated MQTT replay, Reader HTTP/scan verification, Editor startup/sign-in and representative owner GUI observations have passed. Treat their existing private evidence as accepted technical tests; **do not repeat the expensive restore or replay** for the sole purpose of refreshing a report.

**Separate known issue:** 0053-DEF is the Editor's undo-to-original lock release defect; it has an observed navigation workaround and no demonstrated causal connection to the image conversions. It remains open.

## Phase A — offline readiness and owner GUI completion (no production access)

1. Confirm the external hyperlink on reviewed Fragment 1251 from the **isolated** Editor in the Day reader (Ctrl+click), ensuring the expected destination opens without modifying link state. Record only a pass/fail description; do not reproduce sensitive URLs or browser tokens in public reports.
2. Run `tools/audit-0028-step3-production-readiness.sh` from the Windows Cygwin Diaries root. It records parent + all three submodule revisions/status and revalidates the three frozen manifest CSVs against the receipt and preservation policy. It makes **no remote calls or database writes**; its `PASS` is **not** a production freshness check or formal Step 1 signoff.
3. Review the resulting private checkout record. Keep local uncommitted work; identify which responder commit/revision and parent submodule pin will become the production migration code. Never assume the source ZIP includes `.git` history or that `mango` matches Windows.
4. Obtain/record the explicit Step 1 signoff and Step 2 technical/GUI acceptance, with 0053 as a known separate issue. Preserve historical 0022 inventory evidence gap as a documented limitation; the actual 23 November read-only production inventory is the frozen baseline.

## Phase B — production preflight and recovery preparation (read-only until separately approved downtime)

5. Establish the **current** production deployment identities for client, responder and Reader and verify 0051 IMAGE/link/Marquee compatibility. Check deployed responder Java code supports the conversion schema. Record exact image tags/digests and Git revisions. Do not deploy or rebuild production as a side effect of this audit.
6. Re-run **one fresh read-only production inventory and catalogue checksum comparison**, not a new bulk restore. Compare all 72 source IDs/versions/HTML hashes/Page associations and Image checksums with the signed-reviewed manifest. Detect newly added/deleted/changed legacy candidates and active locks. Geometry/size drift in preserved Marquees is permitted **only** if the Marquee ID, owning Fragment and Page still match; the migration must preserve current geometry unchanged. Unapproved source text, link, identity or catalogue drift must stop the production plan and trigger a focused review—not an inferred conversion.
7. Plan a maintenance period with the ability to block Editor and other RPC writers while still retaining an operator route for read-only and postflight checks. Verify which current locks and active sessions need resolution. Do not assume stopping a frontend alone blocks all MQTT RPC writers. Coordinate actual deployment, broker, Postgres and service commands for the current Playbooks/inventory layout; do not create speculative host commands.
8. Confirm the **existing approved** production backup and Files-root recovery processes; record a fresh verified database backup and a corresponding Files snapshot/recovery point immediately before any authorised migration. Do not create, delete, prune or overwrite recovery snapshots from this offline plan. Identify restore authority and rollback window beforehand.

## Phase C — separately authorised production maintenance (NOT YET APPROVED)

9. Once the source, media, runtime and backup checks pass, record **explicit owner approval for the exact production plan and change window**. The Java `apply` path independently requires an approval JSON with production scope, matching plan/input/database/Files identities, backup and rehearsal receipt hashes, approved by/at, acknowledged writer-stop state, plus the explicit `--permit-production-apply YES` switch. Rehearsal approvals must never be reused in production.
10. With the writer-stop gate independently verified, run final read-only `analyse` and `dry-run` against the current production deployment and compare the exact 71-conversion plan and no-op deferral with the accepted reviewed scope. Do not reuse the isolated database's plan because the plan is bound to DB identity and Files-root.
11. Only on approval: install the separately reviewed production journal schema, run once, capture date receipts, then run DB postflight; restart a compatible responder to replay retained MQTT state, reconcile all 71 Fragment topics and 22 preserved Marquees, verify original page scans and image URLs in both UIs, and reopen writers **only after** postflight and owner smoke acceptance.
12. On failure stop at the recorded gate, preserve durable journals, and follow the previously reviewed recovery/restore plan. Never claim partial apply as success. A failed date can roll back while earlier dates remain committed; recovery must account for those commits rather than assuming all-or-nothing global rollback.

## Phase D — final acceptance and closure (still OPEN)

Update Step 3 and Step 4 evidence, commit reviewed application changes in the `diaries-responder` submodule before updating the parent pin, preserve local modifications, and request **separate, explicit owner approval** for 0028 feature closure. `0053-DEF` remains independent.

## Safety limits of the included readiness tool

The audit script neither connects to `pluto` nor to a broker, Docker, production DB or NAS. It does not assert backups or lock-free production. Its offline result **must not** be described as Step 3 PASS or as authorisation to apply. All generated evidence is written under the feature's ignored `evidence/Step 3/private/` directory. The script never changes application code, Git state or any production service.
