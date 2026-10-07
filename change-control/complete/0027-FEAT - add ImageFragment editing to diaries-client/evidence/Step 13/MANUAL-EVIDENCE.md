# Step 13 manual evidence notes

Do not store MQTT passwords, access tokens, refresh tokens or complete responder configuration JSON in this file.

## Dataset and setup

Run ID: `20261004-002349`

Effective database/data directory: `C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries\data\database\common`

Effective Files root: `\\nas\photo\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files-development-common`

Preflight passed with PostgreSQL and Mosquitto healthy, Angular dependencies installed, the `diaries-client` retained-Image ACL present, and the effective Files root available. The initial warning was the expected absence of an IMAGE fixture.

A disposable IMAGE fixture was seeded with the gate enabled and Phase A then ran with the gate disabled. The Phase A fixture was Fragment `2332` referring to Image `1`.

Raw live-run artifacts were written under ignored `build/0027-step13/runs/20261004-002349`. They are deliberately not copied wholesale into source bundles because they include large browser/responder logs and state-capture directories. This file and `FINAL-RUNTIME-CLOSEOUT.md` are the permanent source-controlled summary.

## Phase A browser observations

Existing IMAGE Fragment ID: `2332`

Image ID: `1`

Text edit: succeeded after correcting ordinary `updateFragment` to omit responder-authoritative `marqueeId` and `imageId`. The earlier 400 was traced to `marqueeId:null` being rejected by mqtt-rpc `Map.copyOf(args)` before the responder handler.

Date edit: succeeded from 1828-01-01 to 1828-01-02 and was restored to 1828-01-01. Both affected days reconciled correctly after the correction.

Mixed reorder: succeeded and was restored; retained/date state and PostgreSQL agreed.

Add Image Fragment 403: verified with the authoring gate disabled; no Fragment was created.

Replace Image 403 and post-failure unlock: verified; the Image reference was unchanged and the Fragment did not remain locked.

Clear Image 403 and post-failure unlock: verified; the Image reference was unchanged and the Fragment did not remain locked.

IMAGE Fragment delete / surviving Image: Fragment `2332` was deleted. Image `1` remained in PostgreSQL, retained `diaries/images/1` remained, and the physical file remained with matching checksum. The delete initially exposed a surviving-day sequence gap, which led to the delete-time normalisation correction described below.

## Step 13 redacted RPC diagnostic capture

Validated diagnostic JSON in run directory: `build/0027-step13/runs/20261004-002349/rpc-diagnostics.json`

Validation summary in run directory: `build/0027-step13/runs/20261004-002349/rpc-diagnostics-validation.txt`

Phase A `addImageFragment` -> 403 correlation ID: `71938f00-c436-446a-96ec-3dbcdf957b41`

Phase A Image-reference `updateFragment` -> 403 correlation ID: `988c5859-f9e8-4e4d-bd4e-599aecf6ccc0` (`imageIdState=null`)

Phase B `addImageFragment` -> 200 correlation ID / committed Fragment ID: `c2d1b1b7-36c5-43a2-8142-3a007a591d61` / Fragment `2336`

Phase B `updateFragment` positive `imageId` -> 200 correlation ID: `4f09c858-165f-423a-adb2-99efc832efc7`

Phase B `updateFragment` `imageId:null` -> 200 correlation ID: `dd588fdc-0f74-4e6d-9244-b0add8930371`

Diagnostic capture disabled after evidence: yes.

Importer result: 5 entries; all five required representative pairs PASS; no forbidden authentication/password keys or raw `text` field found.

## Phase B browser observations

Image 1 ID: `89` — `diary-1828-and-1829-and-jan-1830/images/test-2.jpg`, checksum `6622043e635f8c5eaee7307ec7aa99fdc1251e4f4bec0ed4fdcf37837c7f048c`.

Image 2 ID: `90` — `test-1.png`; deleted only after its final Fragment reference was removed.

IMAGE Fragment ID: `2333`

Upload/catalogue: Image `89` was uploaded/catalogued and reconciled across DB/topic/file state.

Create: Fragment `2333` was created as IMAGE referring to Image `89`. The first run exposed create-time sequence normalisation relying on startup repair. The responder create paths were corrected, focused tests made green, and the live create proof was repeated with disposable Fragment `2334`: insertion into the middle of the mixed 1828-01-01 chronology was immediately contiguous without a responder restart.

Restart/replay: after the corrected responder restart, Fragment `2333` restored as IMAGE referring to Image `89`; the retained relationship and text were restored correctly.

Text edit: persisted successfully; the formal Phase B text became `Hello testing! Phase B4` while the Image reference remained `89`.

Date move: Fragment `2333` moved to 1828-01-02 and both source/destination dates normalised immediately; it was then restored to 1828-01-01.

Mixed reorder: Fragment `2333` was moved to a middle position; the mixed MARQUEE/IMAGE day remained contiguous immediately without restart.

Replace Image: Fragment `2333` changed from Image `89` to Image `90`; both catalogue Images remained present.

Delete guard / final-reference behaviour: deleting referenced Image `90` was rejected with 409 Conflict while Fragment `2333` referenced it.

Clear: Image reference was explicitly cleared to `null`; Fragment `2333` remained type IMAGE and both Images remained catalogued.

Reattach: Image `90` was reattached successfully; Fragment `2333` reached version 10 with `image_id=90`.

Delete Fragment / Image survives: Fragment `2333` was deleted while sitting in the middle of the chronology. Survivors were immediately normalised to contiguous positions without responder restart, and Image `90` remained present. The separate live correction proof also deleted Fragment `2334` and again observed immediate contiguous sequence state.

Delete now-unreferenced Image: Image `90` was then deleted through the catalogue UI; its database row, retained Image state and physical file were absent. Image `89` remained untouched.

## Final reconciliation

Any mismatch between UI, responder log, retained topic, DB or file state: no unresolved mismatch. Step 13 discovered four integration issues during live execution — missing MARQUEE relationship synchronisation, explicit `marqueeId:null` on ordinary IMAGE update, delete-time sequence closure, and create-time sequence closure. Each was corrected, regression-covered and rerun before closure.

Cleanup performed: disposable lifecycle Fragment `2333`, create/delete proof Fragment `2334`, and focused diagnostic Fragments `2335`/`2336` were removed. Image `90` was deleted after becoming unreferenced. Image `89` remains catalogued as the surviving disposable Image fixture. The final 1828-01-01 chronology contained only the original five surviving Fragments at contiguous sequences 1..5.

Responder returned to gate disabled: yes.

Final client regression: `TOTAL: 229 SUCCESS`.

Final focused responder regression: `FragmentLifecycleContractTest`, `AddImageFragmentTest`, and `AddFragmentContractTest` — `BUILD SUCCESSFUL`.
