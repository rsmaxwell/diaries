# Step 15 manual production evidence

Run ID: ____________________
Date/time window: ____________________
Operator: ____________________
Step 14 run ID: ____________________
Playbooks commit: ____________________
Diaries/client commit or release candidate: ____________________

## Exact deployed images

Client image/tag: ____________________
Responder image/tag: ____________________
Reader image/tag: ____________________

## Disabled-gate production smoke

MARQUEE edit used (diary/date/Fragment ID, no transcription text): ____________________
Result: ____________________

Existing IMAGE view/edit fixture used, if present (Fragment ID only): ____________________
Result: ____________________

403 authoring action attempted while gate false: ____________________
Observed client message/status: ____________________
Responder/MQTT response evidence file or note: ____________________

## Pre-enable state

`production-pre-enable.txt`: ____________________
MQTT retained-state evidence reference: ____________________
Database evidence reference: ____________________
Files evidence reference: ____________________

## Deliberate enablement

Inventory file changed: ____________________
Inventory setting: `diaries_image_fragment_writes_enabled: true`
Deployment/playbook command used: ____________________
Rendered responder setting verified: ____________________
Responder restart/deployment result: ____________________

## Controlled ImageFragment lifecycle

Known test diary/date: ____________________
Test Image ID: ____________________
Test Fragment ID: ____________________

Create result: ____________________
Text/date/sequence edit result: ____________________
Replace/clear/reattach result, if exercised: ____________________
Delete-Image-while-referenced guard result: ____________________
Restart/replay result: ____________________
Client/reader agreement: ____________________
MQTT retained-state agreement: ____________________
Database agreement: ____________________
Files agreement: ____________________

## Cleanup

Was the Fragment created solely for verification? ____________________
Was the Image created solely for verification? ____________________
Cleanup action/result: ____________________
Final retained/database/Files reconciliation: ____________________

## Rollback readiness

Confirmed rollback setting: `diaries_image_fragment_writes_enabled: false`
Confirmed no database rollback is needed just to stop new Image-reference authoring: ____________________

## Operator acceptance

- [ ] I verified the client was first deployed with the responder gate false.
- [ ] I observed the expected disabled-gate 403 before enabling production authoring.
- [ ] I captured the pre-enable production state.
- [ ] I enabled authoring only through the explicit Playbooks inventory variable.
- [ ] I completed and reconciled the controlled IMAGE lifecycle.
- [ ] I verified restart/replay.
- [ ] I verified cleanup or deliberately retained the created production data.
- [ ] I verified the non-destructive rollback switch remains available.
