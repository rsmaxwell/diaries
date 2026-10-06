# Step 15 production deployment and authoring enablement checklist

Run ID: ____________________
Date: ____________________
Tester: ____________________
Step 14 PASSED run ID: ____________________
Playbooks commit used: ____________________
0027 client image deployed: ____________________
Responder image retained/deployed: ____________________
Reader image retained/deployed: ____________________

## Preconditions

- [ ] Step 14 final summary is `PASSED`.
- [ ] 0026 ImageFragment-capable reader is still deployed and healthy.
- [ ] 0025 responder capability is deployed and healthy.
- [ ] Production `imageFragmentWritesEnabled` is false before the 0027 client rollout.
- [ ] Production database and mutable Files root are the intended matched pair.
- [ ] No database migration or Files-root change is part of this deployment.

## Deploy 0027 client with the gate still false

- [ ] Playbooks source has `diaries_image_fragment_writes_enabled: false` by default.
- [ ] Exact published 0027 client image tag is recorded above and configured in Playbooks/inventory.
- [ ] Playbook deployment completed without volume removal or storage re-pointing.
- [ ] All production services are healthy after deployment.
- [ ] Rendered responder JSON still says `"imageFragmentWritesEnabled": false`.
- [ ] Existing MARQUEE editing smoke test passed.
- [ ] Existing IMAGE viewing and ordinary text/date/sequence editing passed where applicable.
- [ ] Add Image Fragment or attach/replace/clear Image reference received the expected 403 while the gate was false.

## Pre-enable evidence

- [ ] Production pre-enable capture passed.
- [ ] Retained `diaries/fragments/+` and `diaries/images/+` state was reviewed/captured without secrets.
- [ ] Database Image/ImageFragment inventory was reviewed.
- [ ] Files inventory/staging state was reviewed.
- [ ] No unresolved client/responder/reader mismatch remains.

## Deliberate enablement

- [ ] Production inventory explicitly sets `diaries_image_fragment_writes_enabled: true`.
- [ ] Playbook deployment/restart completed successfully.
- [ ] Rendered responder JSON says `"imageFragmentWritesEnabled": true`.
- [ ] Responder and reader/client services are healthy after enablement.

## Controlled lifecycle

- [ ] One known production test Image/day was chosen and recorded in `MANUAL-EVIDENCE.md`.
- [ ] IMAGE Fragment creation succeeded.
- [ ] Image reference replace/clear/reattach semantics were verified as applicable.
- [ ] Ordinary text/date/sequence editing preserved the Image reference unless deliberately changed.
- [ ] Retained Fragment/Image topics agreed with the client/reader view.
- [ ] Database rows agreed with retained state.
- [ ] Files state agreed with the catalogue and no unexpected physical delete occurred.
- [ ] Reference-aware Image delete guard behaved correctly while referenced.
- [ ] Restart/replay restored the same final relationship and chronology.

## Cleanup and rollback readiness

- [ ] Disposable verification Fragment/Image was removed if it existed solely for Step 15.
- [ ] Cleanup was reconciled across client, reader, MQTT retained state, database and Files state.
- [ ] The rollback command/path is recorded: set `diaries_image_fragment_writes_enabled: false` and redeploy/restart.
- [ ] No database rollback is required merely to disable authoring.

## Final acceptance

- [ ] `production-post-enable.txt` passed with expected gate `true`.
- [ ] Production authoring was enabled only after disabled-gate smoke and pre-enable capture passed.
- [ ] Disabling the Playbooks gate remains an immediate non-destructive authoring stop.
- [ ] Step 15 is ready to close and Step 16 may begin.
