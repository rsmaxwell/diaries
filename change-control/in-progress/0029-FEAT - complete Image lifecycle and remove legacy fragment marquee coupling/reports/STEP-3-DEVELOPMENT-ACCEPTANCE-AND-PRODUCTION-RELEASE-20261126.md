# 0029-FEAT — Step 3 integrated development acceptance and production release readiness

**Prepared:** 2026-11-26. **Overall feature:** IN PROGRESS. **Step 2:** development acceptance CLOSED. **Step 3:** OPEN; production approval NOT granted.

## Evidence accepted from operator results (not re-executed)

| Gate | Accepted result | Evidence |
|---|---|---|
| Java application/test compilation | PASS, after adding missing `assertSame` JUnit import | `note(20261126-121507).txt` |
| Complete responder test suite | `BUILD SUCCESSFUL`, 7 seconds | `note(20261126-121607).txt` |
| Isolated PostgreSQL 18 migration and rollback | 2,269 Marquees; forward, rollback, forward PASS | `evidence/step-3-isolated-marquee-page-retirement/rehearsal-20261126-122004-11668.log` |
| Active development DB cutover | Verified custom-format recovery backup, `marquee.page_id` dropped; 2,269 Marquees retained | `evidence/step-3-live-development-marquee-retirement/development-retirement-20261126-122833-12037.log` |
| New responder startup and retained MQTT | 10,661 database and topic-tree objects; `synchronise: ok`, RPC subscribed; no missing-column error in supplied startup log | `note(20261126-123253).txt` |
| Editor + Reader browser verification | **All six 0029 Step 3 checks PASS**, reported by operator | 2026-11-26 operator acceptance in conversation (record browser screenshots if independently available) |
| Production ACL *source* | three `diaries/years/#` grants verified in Playbooks working tree on mango, not deployed | `note(20261126-120541).txt` |

Development Reader: `http://localhost:8080/diaries`; Editor: `http://localhost:4200/diary/1`.

**Acceptance boundary:** The six browser tests are operator-reported, not screenshots or machine-executed tests. Step 3 development is accepted; this does not certify production. POSTAMBLE has no historical production rows; keep synthetic coverage in the test acceptance evidence.

## Source and environment provenance / unresolved differences

- Source basis: `diaries-sources-20261126-114732.zip` and `playbook-sources-20261126-114726.zip` plus later applied 0029 Step 3 packages and operator logs. **These ZIPs are older than the successful local modifications**; use the actual Windows working trees and inspect `git diff` and submodule states before building or packaging release images.
- Windows parent Git `898f293ddff89731047a98c6f80a1d5343593759`; client `1f470618fcd475d871ced79fe9752a99b1111240`, responder `7aa6296e0c675b3d315e9a46bb0dd70202a8cd55`, reader `6d1b289bc5a7983cbf36fe771f8c11dc4725813b`. **Uncommitted** implementation changes exist in submodules, so these commits alone do not reproduce the accepted build.
- Mango `~/diaries` parent revision was `73ee1907...` with uninitialised submodules and unrelated 0028 modifications. **Do not build from that checkout** until deliberately synchronised, preserving its existing local changes.
- Ansible controller is `/home/richard/ansible-controller` (not retired `/home/richard/playbooks`), with `playbooks/` and `inventory/` submodules. Playbooks ACL source changes are uncommitted; other files are also modified. Preserve all unrelated local work.
- Production at last inspection: client `0.0.9-build-80`, responder `0.0.9-build-86`, reader `0.0.9-build-9` healthy. These are **pre-release** images; never infer that 0029 code is already deployed.

## Production preflight and data migration contract

`tools/run-step3-production-readonly-gate.sh` checks repository provenance, production container image/health, visible ACL permissions, systemd timer names and **read-only** production PostgreSQL guard. It never copies scripts into production, changes data, deploys Playbooks, or starts/stops containers. Output stays in `evidence/step-3-production-readiness/` in this feature.

The reviewed `tools/step2-hybrid-schema-and-data.sql` requires **exactly 11** Page-less production Fragments: `1,2,3,387,806,1177,1563,1564,1738,1926,2061`. It assigns nine PREAMBLEs by Diary/year and places the dated exceptions 1738 on Page 1005 and 2061 on Page 1078. The development-only 49-image conversion **must not be used in production**. Guard failure is NO-GO: investigate data, do not weaken or bypass checks.

After the production-shaped hybrid migration, `tools/step3-retire-marquee-page-id.sql` enforces matching Fragment ownership before atomically dropping redundant `marquee.page_id`. The *order* matters. The inverse `tools/step3-restore-marquee-page-id.sql` reconstructs the redundant column from Fragment ownership; it is not a replacement for the **full pre-cutover backup** and does not by itself revert Step 2 data/type/retained MQTT changes.

## Single coordinated production release — preparation sequence, not authorisation to execute

1. **Read-only gate:** run the supplied production baseline and inspect raw evidence. Verify exact 11-row inventory, current schema, active image tags/digests, actual deployed ACL and configured inventory overrides. Resolve any drift before proceeding.
2. **Immutable release candidate:** reconcile Windows parent and each dirty submodule with Git; preserve the accepted implementation, the added `assertSame` import and current deployment source changes. Build/test client, responder and reader once as one coherent revision set, publish distinct new image tags with provenance and digest receipts; verify effective Playbooks/inventory tags point to these exact new images. Do not guess Jenkins build numbers.
3. **Production backup and rehearsal:** identify the current `diaries-backup` complete-dataset publication and the underlying production DB/Files/MQTT recovery points; take and verify a fresh, **restorable** pre-cutover backup. Rehearse the exact two production SQL scripts against a fresh isolated copy of **current production**, including the 11-record guard, all Marquees, rollback and restoration procedure. Store receipts under this feature directory. A healthy snapshot timer or backup filename alone does not prove restorability.
4. **Approval:** obtain explicit operator approval for the specific release tags/digests, backup receipt, anticipated outage and rollback decision. **Do not deploy before this gate.**
5. **Coordinated cutover:** quiesce active clients/Reader and stop production responder writes. Deploy the reviewed annual-topic Mosquitto ACL together with the compatible stack; apply transactional Step 2 SQL followed by Step 3 column retirement against production DB while old responder is stopped. Restart/reconcile only with the matched new responder and Reader/Editor. Existing Compose is deployed via `ansible-controller/playbooks/diaries.yaml` and the Diaries role; role `copy.yaml` notifies `Restart diaries stack`. Avoid running broad Ansible tasks against production before cutover readiness; protect other services on shared Pluto.
6. **Consolidated postflight:** validate DB ownership constraints, 9 annual PREAMBLEs, dated 1738 and 2061, preserved Images and Marquees, zero `MARQUEE` Fragment types, zero orphaned Marquees, retained MQTT `diaries/years/#`, startup reconciliation, Editor/Reader GUI samples including 1828 and 1832, production image digests, backup/rollback receipts and absence of relevant browser/responder errors. No blanket deletion of MQTT retained state.

### Rollback boundary

If schema migration fails inside its transactions, abort and keep the old app stopped until its schema compatibility is verified. If either migration completed but the release fails, stop all writers again. Choose between a tested full-dataset point-in-time restore (preferred after any new writes) and guarded reverse SQL **only if** there have been no incompatible later writes, and coordinate old images, MQTT retained topic reconciliation and ACL as appropriate. Always verify restored DB and mutable Files belong to the same dataset. Record exact actions and outcomes; never assume the existence of a rollback script means recovery has succeeded.

### Go / no-go

**Current verdict: NO-GO for production writes.** Development is PASS, but the read-only production row-set verification, immutable release image creation, actual backup restoration evidence, publication/Files/MQTT recovery compatibility and explicit release approval are outstanding. Production ACL source is prepared and verified on mango; that is not the same as having it deployed.

Keep 0029 under `change-control/in-progress/` until all Step 3 gates are accepted and formal feature closure is expressly authorised.
