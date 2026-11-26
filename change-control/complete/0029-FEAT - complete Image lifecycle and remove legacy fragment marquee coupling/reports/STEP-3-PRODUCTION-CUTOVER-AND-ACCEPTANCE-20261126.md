# 0029-FEAT — Production cutover acceptance and final integrity review (26 November 2026)

**Status (updated 2026-11-26 18:44 UTC):** Production migration, all six browser tests and repeated post-cutover SQL structural integrity PASS. Independent retained MQTT/database reconciliation is not demonstrated. Feature remains IN PROGRESS pending evidence acceptance and formal closure.

## Accepted evidence (reported from the production execution logs)

- Fresh pre-0029 production database recovery archive created and verified by SHA-256 plus catalogue: `evidence/step-3-production-cutover/diaries-production-pre0029-20261126-172307.dump` (Windows Diaries feature directory). Preserve it, its `.toc` and SHA-256 evidence; do not include dump bytes in Git.
- Migration `step2-hybrid-schema-and-data.sql`: committed; distribution `DATED/IMAGE 73`, `DATED/TEXT 2249`, `PREAMBLE/TEXT 9` (2331 Fragments total).
- Migration `step3-retire-marquee-page-id.sql`: committed; post-migration integrity script reported PASS.
- Initial Ansible restart failed because the synced Mosquitto ACL was unreadable to UID 1883. Source ACL was corrected to mode 0644 on mango and Playbooks rerun. No need for per-file mode override in the role; source permissions are authoritative for sync.
- Production `docker compose ps` subsequently showed all five containers healthy: Client `0.0.9-build-81`, Responder `0.0.9-build-87`, Reader `0.0.9-build-10`, PostgreSQL 18 and Mosquitto 2.
- Owner confirmed **all six production browser acceptance checks passed**, including editor, annual PREAMBLE, dated TEXT/IMAGE, historical images, Reader and normal editing/navigation.
- Recovery rehearsal accepted earlier: isolated production DB restoration, guarded migration/rollback, and full 128-file (98 MB) independent Files restore and content comparison on mars.
- Published source commits: parent Diaries `216413468fbaae21dbfbfe36e92c05cd87cba907`, client `cc826a8254b0e6d989755dc880d3023dae9e3416`, responder `a49c6abd0ce005d58eb516770f6515313e40cdf6`, web `363ca8f425b811eeedff47486092b1f63c403ab0`, Playbooks `e1273b48b1cea2e175ea098a0a82ff8b0b184851`, Ansible controller `29c562f`.

## Remaining acceptance evidence

Run `tools/run-step3-production-postcutover-readonly.sh` **once** on Windows Cygwin from Diaries repository root, and retain its generated terminal log under `evidence/step-3-production-cutover/`. The script verifies actual final database relationships and schema, exact historic assignments, container health and ACL; it also displays recent errors for manual review. This is a new post-migration query and must not reuse the pre-migration baseline script.

The 0029 plan separately requires retained MQTT state reconciliation with the database; container health and ACL grants alone do not prove retained-topic consistency. Identify whether existing reconciliation reports establish that gate, or record it as outstanding. The SQL report does not claim to test MQTT retained-state equality.

After accepting postflight output, record final deployment receipt and owner approval. Do not mark the feature complete or move directories until formal closure approval.


## 18:43 UTC post-cutover integrity update

Both read-only runs passed: `evidence/step-3-production-cutover/postcutover-integrity-20261126-184323.log` and `postcutover-integrity-20261126-184359.log`. All five containers healthy, systemd active, annual MQTT ACL present, 2331 Fragments distributed as 73 DATED IMAGE + 2249 DATED TEXT + 9 PREAMBLE TEXT, IDs 1738 and 2061 assigned to Pages 1005/1078, ownership/schema assertions PASS. Six production browser tests are owner-confirmed PASS. See `reports/STEP-3-FINAL-PRODUCTION-ACCEPTANCE-20261126.md` for evidence and outstanding retained-topic reconciliation.
