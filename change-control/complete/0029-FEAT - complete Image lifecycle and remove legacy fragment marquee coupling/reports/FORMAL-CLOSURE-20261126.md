# 0029-FEAT — Formal feature closure, 26 November 2026

**Decision:** CLOSED / COMPLETE — explicitly approved by feature owner 2026-11-26.  
**Feature:** Complete Image lifecycle and remove legacy Fragment/Marquee coupling.  
**Change-control location:** `change-control/complete/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/`.

## Accepted delivery

- Hybrid Fragment schema deployed: `TEXT`/`IMAGE` and `PREAMBLE`/`DATED`/`POSTAMBLE`; exclusive Page or Diary/year ownership; `marquee.page_id` retired.
- Both production SQL migrations committed successfully on 2026-11-26; post-migration integrity assertions PASS, then repeated read-only checks at 18:43:23 and 18:43:59 UTC PASS.
- 2,331 production Fragments: 2,249 DATED TEXT, 73 DATED IMAGE, 9 PREAMBLE TEXT. The nine annual PREAMBLE records retained their Diary/year ownership; historic Fragments 1738 and 2061 mapped to Pages 1005 and 1078, respectively.
- Production Client `0.0.9-build-81`, Responder `0.0.9-build-87`, Reader `0.0.9-build-10`; all five production containers healthy and `diaries-compose.service` active on post-cutover inspection.
- Production MQTT ACL contains `diaries/years/#` grants (read Client/Reader, readwrite Responder); source file permissions govern Ansible synchronisation. Original Mosquitto startup failure due to ACL mode was corrected and service recovered.
- Six local published-image browser tests and six production browser acceptance tests passed, confirmed by owner.
- Fresh pre-migration PostgreSQL dump and SHA-256/catalogue evidence retained locally in feature evidence; previous isolated database restore and rollback rehearsal passed. Backup Files restore on mars compared all 128 files (98 MB) with `diff -qr` PASS.
- Read-only recent Responder, Reader, and Mosquitto log summaries at the final check contained no matching errors.

## Owner-approved limitation

A separate **exhaustive retained MQTT topic-tree inventory/replay comparison against PostgreSQL was not demonstrated**. Healthy services, annual ACLs, startup behaviour and functional browser tests are operational evidence, but **not equivalent** to exhaustive retained-state reconciliation. The feature owner explicitly approved closure **including this limitation**. It is accepted, not falsely recorded as a passing test. If a retained-state discrepancy later appears, address it through a new defect/change-control item rather than reopening undocumented closure work.

## Git and evidence references

- Diaries parent published revisions leading to closure: `ff1f7aa` (acceptance reports), `c6d533c` (release scripts and raw cutover/integrity logs), `d2d0b30` (pre-migration dump checksum and `.toc`). Final move/closure commit to be captured by the user when applied.
- Playbooks `e1273b48b1cea2e175ea098a0a82ff8b0b184851`; controller `29c562f`.
- Submodules: Client `cc826a8254b0e6d989755dc880d3023dae9e3416`, Responder `a49c6abd0ce005d58eb516770f6515313e40cdf6`, Reader `363ca8f425b811eeedff47486092b1f63c403ab0`.
- Raw evidence: `evidence/step-3-production-cutover/production-cutover-20261126-172307.log`, `postcutover-integrity-20261126-184323.log`, `postcutover-integrity-20261126-184359.log`, `diaries-production-pre0029-20261126-172307.dump.sha256`, `.dump.toc`.
- Acceptance reports: `reports/STEP-3-FINAL-PRODUCTION-ACCEPTANCE-20261126.md` and `reports/STEP-3-PRODUCTION-CUTOVER-AND-ACCEPTANCE-20261126.md`.
- Binary `.dump` is excluded from Git and should remain protected in its feature evidence directory as long as required by recovery policy.

## Closure authority

The feature owner replied **“Yes, I approve”** to the explicit question whether to formally close 0029-FEAT, including acceptance of the retained-MQTT reconciliation limitation. This authorises the change-control move from `in-progress/` to `complete/`; it does not authorise deletion of recovery data or other production changes.

**Final acceptance:** 0029-FEAT COMPLETE following application and commit of this closure documentation and feature-directory move.
