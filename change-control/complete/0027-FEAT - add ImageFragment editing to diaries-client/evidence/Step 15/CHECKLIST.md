# Step 15 production deployment and authoring enablement checklist

Run ID: 20261006-133404
Date: 2026-10-06
Tester: Richard
Step 14 PASSED run ID: 20261006-093834
Playbooks commit used: Not separately recorded in the captured evidence; deployed production Playbooks source passed its permanent production-deployment regression after the ACL correction.
0027 client image deployed: `rsmaxwell/diaries-client:0.0.9-build-76`
Responder image retained/deployed: `rsmaxwell/diaries-responder:0.0.9-build-84`
Reader image retained/deployed: `rsmaxwell/diaries-web:0.0.9-build-8`

## Preconditions

- [x] Step 14 final summary is `PASSED`.
- [x] 0026 ImageFragment-capable reader is still deployed and healthy.
- [x] 0025 responder capability is deployed and healthy.
- [x] Production `imageFragmentWritesEnabled` is false before the 0027 client rollout.
- [x] Production database and mutable Files root are the intended matched pair.
- [x] No database migration or Files-root change is part of this deployment.

## Deploy 0027 client with the gate still false

- [x] Playbooks source has `diaries_image_fragment_writes_enabled: false` by default.
- [x] Exact published 0027 client image tag is recorded above and configured in Playbooks/inventory.
- [x] Playbook deployment completed without volume removal or storage re-pointing.
- [x] All production services are healthy after deployment.
- [x] Rendered responder JSON still says `"imageFragmentWritesEnabled": false`.
- [x] Existing MARQUEE editing smoke test passed.
- [x] Existing IMAGE viewing and ordinary text/date/sequence editing passed where applicable.
- [x] Image Catalogue `listFiles` completed and displayed its entries while the gate was false.
- [x] Add Image Fragment or attach/replace/clear Image reference received the expected 403 while the gate was false.

## Pre-enable evidence

- [x] Production pre-enable capture passed.
- [x] Retained `diaries/fragments/+` and `diaries/images/+` state was reviewed/captured without secrets.
- [x] Database Image/ImageFragment inventory was reviewed.
- [x] Files inventory/staging state was reviewed.
- [x] No unresolved client/responder/reader mismatch remains.

## Deliberate enablement

- [x] Production inventory explicitly sets `diaries_image_fragment_writes_enabled: true`.
- [x] Playbook deployment/restart completed successfully.
- [x] Rendered responder JSON says `"imageFragmentWritesEnabled": true`.
- [x] Responder and reader/client services are healthy after enablement.

## Controlled lifecycle

- [x] One known production test Image/day was chosen and recorded in `MANUAL-EVIDENCE.md`.
- [x] IMAGE Fragment creation succeeded.
- [x] Image reference replace/clear/reattach semantics were verified as applicable.
- [x] Ordinary text/date/sequence editing preserved the Image reference unless deliberately changed.
- [x] Retained Fragment/Image topics agreed with the client/reader view.
- [x] Database rows agreed with retained state.
- [x] Files state agreed with the catalogue and no unexpected physical delete occurred.
- [x] Reference-aware Image delete guard behaved correctly while referenced.
- [x] Restart/replay restored the same final relationship and chronology.

## Cleanup and rollback readiness

- [x] Disposable verification Fragment/Image was removed if it existed solely for Step 15.
- [x] Cleanup was reconciled across client, reader, MQTT retained state, database and Files state.
- [x] The rollback command/path is recorded: set `diaries_image_fragment_writes_enabled: false` and redeploy/restart.
- [x] No database rollback is required merely to disable authoring.

## Final acceptance

- [x] `production-post-enable.txt` passed with expected gate `true`.
- [x] Production authoring was enabled only after disabled-gate smoke and pre-enable capture passed.
- [x] Disabling the Playbooks gate remains an immediate non-destructive authoring stop.
- [x] Step 15 is ready to close and Step 16 may begin.
