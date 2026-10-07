# Step 15 manual production evidence

Run ID: 20261006-133404
Date/time window: 2026-10-06 13:34-23:26 BST
Operator: Richard
Step 14 run ID: 20261006-093834
Playbooks commit: Not separately recorded in the captured evidence; production Playbooks source was deployed from `mango` and its permanent production-deployment regression passed after the ACL correction.
Diaries/client commit or release candidate: Git identities are recorded in the run-local `begin.txt`; the deployed release-candidate identity for closure is the exact image set recorded below.

## Exact deployed images

Client image/tag: `rsmaxwell/diaries-client:0.0.9-build-76`
Responder image/tag: `rsmaxwell/diaries-responder:0.0.9-build-84`
Reader image/tag: `rsmaxwell/diaries-web:0.0.9-build-8`

## Disabled-gate production smoke

MARQUEE edit used (diary/date/Fragment ID, no transcription text): Fragment 2330 on diary 1 / page 686 / 1828-01-01.
Result: PASSED - ordinary MARQUEE editing succeeded while the ImageFragment authoring gate was false.

Existing IMAGE view/edit fixture used, if present (Fragment ID only): Fragment 2331 after the retained-Image ACL correction, with the production gate returned to false.
Result: PASSED - the IMAGE Fragment and retained Image metadata resolved correctly; ordinary Fragment editing remained available, while Image-reference mutation remained blocked by the disabled authoring gate.

Image Catalogue opened/listFiles result while gate false: PASSED - Image Catalogue opened successfully and `listFiles` returned 200 OK after the timing correction.
403 authoring action attempted while gate false: Add Image Fragment / Image-reference mutation.
Observed client message/status: PASSED - the responder returned 403 forbidden with the disabled-environment message and no unauthorized Image-reference mutation was committed.
Responder/MQTT response evidence file or note: Browser/responder evidence captured during the Step 15 run; canonical disabled-gate production captures are `production-post-client-disabled.txt`, `production-rollback-disabled.txt` and `production-pre-enable.txt` in this run.

## Rolled-back attempts / corrections

Failed attempt/cause, if any: Two production defects were exposed and corrected without destructive rollback. First, NAS-backed `listFiles` completed successfully in about 11.8 seconds while the client used the generic five-second RPC timeout. Second, after successful IMAGE Fragment creation, the Angular client could not receive retained `diaries/images/<id>` metadata because the Ansible-managed production client ACL lacked `topic read diaries/images/+`.
Rollback-disabled capture: PASSED; the latest canonical `production-rollback-disabled.txt` records the responder gate false after rollback and correction work.
Correction/rebuilt image tags: `diaries-client:0.0.9-build-76`, `diaries-responder:0.0.9-build-84`, `diaries-web:0.0.9-build-8`. The MQTT ACL correction was a Playbooks-only deployment and required no additional Docker rebuild.
Fresh disabled-gate smoke after correction: PASSED - Image Catalogue listing completed, retained Image metadata resolved in the client, ordinary IMAGE Fragment editing worked, and Image-reference authoring remained rejected while the gate was false.

## Pre-enable state

`production-pre-enable.txt`: PASSED; latest canonical capture for run `20261006-133404`.
MQTT retained-state evidence reference: Operator MQTT Explorer review confirmed the relevant Fragment/Image retained topics and later confirmed cleanup removed the disposable Fragment topics while preserving `diaries/images/1`.
Database evidence reference: Database inventory in the production capture plus targeted PostgreSQL checks of Fragment 2331 and Image 1 before, during and after the controlled lifecycle.
Files evidence reference: Files inventory in the production capture plus direct verification that the Image 1 physical file remained present throughout delete-guard and cleanup testing.

## Deliberate enablement

Inventory file changed: `/etc/ansible/host_vars/pluto/diaries.yaml`
Inventory setting: `diaries_image_fragment_writes_enabled: true`
Deployment/playbook command used: `cd ~/playbooks/scripts && ./diaries.sh`
Rendered responder setting verified: PASSED - `production-post-enable.txt` captured `imageFragmentWritesEnabled: true`.
Responder restart/deployment result: PASSED - production stack returned healthy with client build 76, responder build 84, reader build 8, PostgreSQL and Mosquitto healthy, and the shared nginx route active.

## Controlled ImageFragment lifecycle

Known test diary/date: diary 1 / page 686 / 1828-01-01
Test Image ID: 1 (`Lucia_Elizabeth_Vestris_by_Robert_William_Buss.jpg`, pre-existing catalogue Image)
Test Fragment ID: 2331 (created solely for Step 15 verification)

Create result: PASSED - IMAGE Fragment 2331 was created referencing Image 1 once the production authoring gate was deliberately enabled.
Text/date/sequence edit result: PASSED - an ordinary Fragment edit advanced the Fragment version while preserving `type=IMAGE` and `imageId=1`; client, retained MQTT state and PostgreSQL agreed.
Replace/clear/reattach result, if exercised: PASSED - Image reference was changed from Image 1 to Image 31, cleared to null, then reattached to Image 1. Each checkpoint agreed across the client, retained Fragment topic and PostgreSQL while preserving the other Fragment fields.
Delete-Image-while-referenced guard result: PASSED - deletion of Image 1 was refused while Fragment 2331 referenced it. The catalogue row, retained Image topic and physical file remained intact.
Restart/replay result: PASSED - after a full production stack stop/start, all services were healthy and Fragment 2331 recovered as version 5, `type=IMAGE`, `imageId=1`; Image 1 remained available and the same relationship was reconstructed.
Client/reader agreement: PASSED - the editor and 0026 reader displayed the same Fragment/Image relationship and chronology after restart/replay.
MQTT retained-state agreement: PASSED - `diaries/fragments/2331` and `diaries/images/1` agreed with PostgreSQL and the UI during the lifecycle; cleanup later removed the disposable Fragment retained topics while preserving Image 1.
Database agreement: PASSED - targeted PostgreSQL checks agreed with the retained/client state at create, ordinary edit, replace, clear, reattach, delete guard, restart/replay and cleanup checkpoints.
Files agreement: PASSED - the pre-existing Image 1 physical file remained present; no unexpected physical delete occurred.

## Cleanup

Was the Fragment created solely for verification? Yes - IMAGE Fragment 2331 was disposable Step 15 verification data. MARQUEE Fragment 2330 was also disposable disabled-gate smoke-test data.
Was the Image created solely for verification? No - Image 1 was pre-existing catalogue data and was deliberately retained.
Cleanup action/result: PASSED - Fragments 2330 and 2331 were deleted through the normal client path. PostgreSQL then reported zero rows for those IDs and the remaining 1828-01-01 fragments were renormalised to contiguous sequences 1 through 5.
Final retained/database/Files reconciliation: PASSED - PostgreSQL contains neither test Fragment, MQTT Explorer contains neither test Fragment retained topic, the January 1828 reader contains neither test Fragment, `diaries/images/1` remains retained, Image 1 remains catalogued, and its physical file remains present.

## Rollback readiness

Confirmed rollback setting: `diaries_image_fragment_writes_enabled: false`
Confirmed no database rollback is needed just to stop new Image-reference authoring: Yes - this was exercised during Step 15; setting the Playbooks gate false and redeploying stopped Image-reference authoring without removing existing Image/Fragment data or changing the database/Files dataset.

## Operator acceptance

- [x] I verified the client was first deployed with the responder gate false.
- [x] I observed the expected disabled-gate 403 before enabling production authoring.
- [x] I captured the pre-enable production state.
- [x] I enabled authoring only through the explicit Playbooks inventory variable.
- [x] I completed and reconciled the controlled IMAGE lifecycle.
- [x] I verified restart/replay.
- [x] I verified cleanup or deliberately retained the created production data.
- [x] I verified the non-destructive rollback switch remains available.
