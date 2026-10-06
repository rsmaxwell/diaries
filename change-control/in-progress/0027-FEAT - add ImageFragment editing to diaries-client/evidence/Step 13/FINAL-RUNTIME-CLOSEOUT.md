# Step 13 final runtime close-out

Date: 2026-10-05  
Run ID: `20261004-002349`

## Outcome

Step 13 — **Run live MQTT/responder verification with authoring disabled and enabled** — is complete.

The development run exercised the Angular editor, Java responder, MQTT RPC/status replies, retained Fragment/Image topics, PostgreSQL state and physical Files state with `imageFragmentWritesEnabled=false` and `true`. The final reconciled behaviour matches the Step 13 contract, the temporary authoring diagnostics are disabled, and the responder has been returned to the gate-disabled state.

## Regression baseline

The final Angular/Karma run completed successfully:

```text
Executed 229 of 229 SUCCESS
TOTAL: 229 SUCCESS
```

The focused responder suite covering the chronology fixes and creation contracts also completed successfully:

```text
:diaries-responder:test
FragmentLifecycleContractTest
AddImageFragmentTest
AddFragmentContractTest
BUILD SUCCESSFUL
```

The earlier failing MARQUEE create-normalisation focused test was a test-fixture contract mismatch (`sequence` supplied as String rather than Number/BigDecimal), not a production failure. After aligning the test input, the focused suite was green.

## Phase A — authoring gate disabled

Using disposable IMAGE Fragment `2332` / Image `1`, the run proved that existing IMAGE state could be loaded and ordinary type-neutral editing continued to work while Image-reference authoring remained disabled:

- transcription and date edits succeeded;
- mixed MARQUEE/IMAGE reorder succeeded;
- Add Image Fragment returned 403 and created nothing;
- replace and clear Image-reference operations returned 403 and released their locks;
- deleting the IMAGE Fragment preserved the reusable Image row, retained Image topic and physical file.

Phase A exposed two integration defects which were corrected before closure: the MARQUEE relationship synchronizer was being permanently torn down by topic cleanup, and ordinary IMAGE `updateFragment` was serialising `marqueeId:null`, which mqtt-rpc rejected before handler dispatch. Both corrections are regression-covered and were reverified live.

## Sequence-normalisation corrections proved live

Phase A deletion showed that `DeleteFragment` could leave a sequence gap until responder startup normalisation repaired it. `DeleteFragment` now normalises the affected date in the same transaction and republishes changed survivors after commit.

Phase B creation then showed the corresponding create-side gap. `addFragment` and `addImageFragment` now use create+normalise transaction paths and republish the committed created Fragment plus every renumbered survivor.

After those corrections:

- the focused responder suite was green;
- disposable Fragment `2334` was inserted into the middle of the mixed 1828-01-01 chronology and the day was immediately contiguous without responder restart;
- deleting Fragment `2334` immediately left the surviving day contiguous without responder restart;
- later deletion of Phase B Fragment `2333` again left the surviving day contiguous immediately.

Startup synchronisation is therefore no longer needed to repair create/update/delete sequence gaps.

## Phase B — authoring gate enabled

Image `89` (`test-2.jpg`) was catalogued and used to create IMAGE Fragment `2333`. The run then proved:

- retained restart/replay restored the Fragment→Image relationship;
- transcription edit preserved the Image reference;
- date move normalised both affected dates and was safely restored;
- mixed reorder remained contiguous;
- Image reference replacement from Image `89` to Image `90` succeeded;
- deleting referenced Image `90` was correctly rejected with 409 Conflict;
- explicit `imageId:null` clear preserved the Fragment and reusable Image;
- Image `90` could be reattached;
- deleting Fragment `2333` preserved Image `90` and immediately normalised survivors;
- deleting now-unreferenced Image `90` removed its DB row, retained state and physical file while Image `89` remained.

## Representative RPC proof

The development-only redacted Step 13 RPC diagnostic capture was used only for the focused evidence sequence, then disabled. The importer validated exactly five required request/reply pairs:

```text
PASS addImageFragment                       -> 403  71938f00-c436-446a-96ec-3dbcdf957b41
PASS updateFragment imageId:null            -> 403  988c5859-f9e8-4e4d-bd4e-599aecf6ccc0
PASS addImageFragment                       -> 200  c2d1b1b7-36c5-43a2-8142-3a007a591d61  committed Fragment 2336
PASS updateFragment positive imageId        -> 200  4f09c858-165f-423a-adb2-99efc832efc7
PASS updateFragment imageId:null            -> 200  dd588fdc-0f74-4e6d-9244-b0add8930371
```

The validator also confirmed that no forbidden authentication/password keys or raw transcription text were present in the stored diagnostic JSON.

## Cleanup and final state

Focused diagnostic Fragments `2335` and `2336` were removed after evidence import. The final database check showed neither row remained, the 1828-01-01 chronology was contiguous at positions 1..5, and Image `89` remained catalogued.

The responder finished with `imageFragmentWritesEnabled=false` and the browser diagnostic capture disabled.

## Evidence retention

The large live artifacts remain under the ignored workstation run directory:

```text
build/0027-step13/runs/20261004-002349
```

That run contains the preflight, gate-specific responder logs, browser console exports, labelled DB/MQTT/Files state captures, `rpc-diagnostics.json`, and `rpc-diagnostics-validation.txt`. They are intentionally not copied wholesale into source bundles. The completed `CHECKLIST.md`, `MANUAL-EVIDENCE.md`, validation records and this close-out are the permanent change-control summary.

## Acceptance decision

Step 13 acceptance criteria are satisfied. No further Step 13 lifecycle mutation is required.

Proceed to **Step 14 — run full regression and deployment/rollout rehearsal**.
