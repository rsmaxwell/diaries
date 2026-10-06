# Step 13 live verification checklist

Run ID: `20261004-002349`  
Date: 2026-10-04 to 2026-10-05  
Dataset/database: `development-infrastructure` using `data/database/common`  
Files root: `\\nas\photo\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files-development-common`  
Tester: Richard Maxwell

## IDs used

- Phase A existing/disposable IMAGE Fragment ID: `2332`
- Phase A Image ID: `1`
- Phase B Image 1 ID: `89` (`test-2.jpg`)
- Phase B Image 2 ID: `90` (`test-1.png`, deleted at B13)
- Phase B IMAGE Fragment ID: `2333`
- Additional create/delete normalisation proof Fragment ID: `2334`
- Focused RPC-diagnostic disposable Fragment IDs: `2335`, `2336`

## Phase A — gate disabled

- [x] Responder started with `imageFragmentWritesEnabled=false` via Step 13 wrapper.
- [x] Existing IMAGE Fragment loaded with retained Image metadata.
- [x] IMAGE transcription text edit succeeded.
- [x] IMAGE date edit succeeded.
- [x] Mixed MARQUEE/IMAGE reorder succeeded.
- [x] Add Image Fragment returned 403; no Fragment was created.
- [x] Select/replace Image returned 403; `image_id` did not change.
- [x] Clear Image returned 403; `image_id` did not change.
- [x] Rejected mutation left no surviving Fragment lock.
- [x] Disposable IMAGE Fragment deletion succeeded.
- [x] Fragment deletion did not delete the catalogue Image/file/topic.
- [x] Browser console evidence was retained for the Phase A run.
- [x] Disabled-gate responder log was captured by the Step 13 wrapper.

## Phase B — gate enabled

- [x] Responder started with `imageFragmentWritesEnabled=true` via Step 13 wrapper.
- [x] Image 1 uploaded/catalogued; DB/topic/file agreed.
- [x] IMAGE Fragment created against Image 1; DB/topic/UI agreed.
- [x] Browser/responder restart restored the same relationship.
- [x] Text edit changed persisted text while preserving Image reference.
- [x] Date edit updated DB/retained/UI consistently and was restored afterwards.
- [x] Mixed reorder updated sequence/version while preserving Image reference.
- [x] Image reference replaced with Image 2.
- [x] Image delete guard was verified for referenced Image 90 with 409 Conflict.
- [x] Image reference cleared to null without deleting Image 90.
- [x] Image 90 reattached.
- [x] IMAGE Fragment 2333 deleted.
- [x] After Fragment deletion, Image 90 DB row/topic/file still existed.
- [x] Now-unreferenced Image 90 deleted through catalogue UI.
- [x] After Image deletion, DB row/topic/file were absent.
- [x] Browser console evidence was retained for the Phase B run.
- [x] Enabled-gate responder log was captured by the Step 13 wrapper.

## MQTT RPC evidence

- [x] Step 13 browser RPC diagnostics enabled only for focused evidence capture, then disabled afterwards.
- [x] `rpc-diagnostics.json` imported with `step13-import-rpc-diagnostics.ps1` into the active run.
- [x] `rpc-diagnostics-validation.txt` reported all five required representative pairs PASS.
- [x] `addImageFragment` -> 403 with gate disabled. Correlation ID `71938f00-c436-446a-96ec-3dbcdf957b41`.
- [x] Image-reference `updateFragment` -> 403 with gate disabled. Correlation ID `988c5859-f9e8-4e4d-bd4e-599aecf6ccc0`, explicit `imageId:null`.
- [x] `addImageFragment` -> 200 with gate enabled. Correlation ID `c2d1b1b7-36c5-43a2-8142-3a007a591d61`, committed Fragment `2336`.
- [x] `updateFragment` positive `imageId` -> 200. Correlation ID `4f09c858-165f-423a-adb2-99efc832efc7`.
- [x] `updateFragment` explicit `imageId:null` -> 200. Correlation ID `dd588fdc-0f74-4e6d-9244-b0add8930371`.
- [x] Validation confirmed that authentication/password keys and raw transcription text were absent from stored diagnostic evidence.

## Final invariant

- [x] At every accepted checkpoint, client UI, responder outcome/log, retained MQTT state, PostgreSQL state and physical Files state agreed.
- [x] Development responder returned to `imageFragmentWritesEnabled=false` after the test.
- [x] Diagnostic capture was disabled after evidence export/import.
- [x] Diagnostic Fragments `2335` and `2336` were removed; Image `89` remained catalogued.

## Step 13 integration corrections

- [x] Focused responder regression for delete-time sequence normalisation is green.
- [x] Focused responder regressions for MARQUEE and IMAGE create-time sequence normalisation are green.
- [x] Live create-time proof inserted Fragment `2334` into the middle of the mixed day and the chronology was immediately contiguous without responder restart.
- [x] IMAGE Fragment delete immediately normalised the surviving day in PostgreSQL.
- [x] Changed survivor Fragment canonical/date retained topics were republished immediately.
- [x] Live delete-time proof removed Fragment `2334`; the surviving day was immediately contiguous without responder restart.
- [x] No responder restart is needed to repair sequence gaps after create, update/reorder, or delete.

## Closure

- [x] Standard Angular/Karma suite green at `229/229` (`TOTAL: 229 SUCCESS`).
- [x] Focused responder suite covering `FragmentLifecycleContractTest`, `AddImageFragmentTest` and `AddFragmentContractTest` completed `BUILD SUCCESSFUL`.
- [x] `MANUAL-EVIDENCE.md` completed.
- [x] `FINAL-RUNTIME-CLOSEOUT.md` generated.
- [x] Step 13 acceptance criteria satisfied; proceed to Step 14.
