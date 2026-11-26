# 0029-FEAT — Step 3 production release metadata handoff (2026-11-26)

**Feature remains IN PROGRESS; production deployment is not authorised.**

## Evidence already accepted

- Development responder source/test compilation and full test suite passed.
- Development Marquee page-column retirement preserved **2,269** Marquees; retained MQTT synchronisation reconciled **10,661** objects; six browser acceptance checks passed.
- Production read-only gate on 2026-11-26 passed: **2,331** Fragments, **2,270** Marquees and exactly the reviewed **11** Page-less Fragments.
- Isolated production migration rehearsal passed at 12:53 UTC, including both forward SQL stages, both reverse SQL stages, original-baseline verification and reapplication. Evidence: `evidence/step-3-production-isolated-rehearsal/production-rehearsal-20261126-125311-12482.log`. Corrected rollback checksum: `9c730377288482e38a2633aee078cbc47def064039083657f45bf1b4cf9812a7`.
- Production ACL permissions were added to the Playbooks source and verified; live deployment remains pending.

## Release blockers and checks

1. **Reproducible source:** Windows parent and three submodules have uncommitted changes. Preserve all; establish exactly which changes belong to 0029 and commit each submodule independently before updating parent pointers. Do not infer image provenance from a local working tree or an old parent commit.
2. **Effective Playbooks configuration:** Ansible controller is `/home/richard/ansible-controller`, Playbooks submodule `/home/richard/ansible-controller/playbooks`, inventory submodule alongside. Image role defaults in 11:47 source bundle were client `0.0.9-build-80`, responder `0.0.9-build-86`, reader `0.0.9-build-9`. Actual host/group variable overrides must be verified independently; `ansible-inventory --host` does **not** include role defaults.
3. **Backup recovery:** Confirm latest database backup is current and independently restorable, and identify mutable NAS Files recovery point and consistency window. A successful live timer or the isolated read-only `pg_dump` rehearsal does not establish backup restoration readiness or Files recoverability.
4. **Images:** Build new compatible Client, Responder and Reader images from recorded committed revisions; collect exact tags and immutable image digests, Jenkins build evidence and smoke-test results. Do not change production image tags yet.
5. **Deployment sequence:** Freeze production writes, capture a fresh verified DB backup and Files recovery point, record pre-migration row samples, apply both SQL stages and matching MQTT ACL and application images in one controlled window, reconcile retained MQTT state, and run Editor/Reader smoke tests. Provide a tested rollback procedure that stops writers and reverses both SQL stages only where no post-cutover edits make data rollback unsafe.
6. **Approval:** obtain explicit production deployment approval after readiness evidence is inspected. Keep 0029 in progress until formal closure.

## Read-only audit package

Run `tools/run-step3-production-release-metadata-audit.sh` from Windows Cygwin in the Diaries parent repository. It records Git status, effective inventory host overrides (allowlisted fields only, not raw secret-bearing inventory), role default tags, live Docker image IDs, published-backup metadata, timer/service state and live Mosquitto ACL. Output is written under `evidence/step-3-production-release-readiness/`.

**No backups are triggered or restored, and no images or services are changed by this audit.** `RESULT: METADATA COLLECTION PASS` means *collection only*: it does not mean the release or backup restore is accepted. Some production paths may need correction after first evidence run.

## Protection of existing work

Do not clean, reset, force checkout, auto-commit or deploy from either dirty repository. `README-STEP3-*` files at the parent root reported by the recent Git status are package handoffs and should be reviewed before any later tidy-up. Preserve 0028 feature edits on mango.
