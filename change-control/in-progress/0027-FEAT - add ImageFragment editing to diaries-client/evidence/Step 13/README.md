# Step 13 — live MQTT/responder verification with authoring disabled and enabled

**Status: COMPLETE — 2026-10-05.**

The repeatable live-verification harness was exercised on the development workstation under run `20261004-002349`. Both gate-disabled and gate-enabled phases are complete, the final Angular suite is green at 229/229, the focused responder chronology/creation suite is green, the five representative redacted RPC pairs validate, disposable Fragments were cleaned up, and the responder finished with `imageFragmentWritesEnabled=false`. See `FINAL-RUNTIME-CLOSEOUT.md`, `CHECKLIST.md` and `MANUAL-EVIDENCE.md`.

## Implemented tooling

Feature-specific tooling is kept under this evidence directory rather than in the live `scripts/` tree, in line with the completed-feature tooling-cleanup policy:

- `tooling/step13-begin.ps1` creates an ignored `build/0027-step13/runs/<timestamp>` evidence run;
- `tooling/step13-preflight.ps1` verifies development infrastructure, Angular dependencies, effective Files root and the required client Image-topic ACL;
- `tooling/prepare-step13-gate-config.ps1` creates disposable gate-enabled/disabled responder base configs under ignored `build/0027-step13/` without modifying `%USERPROFILE%\.diaries\responder.json`;
- `tooling/run-responder-step13.ps1` launches the normal direct-development responder with the selected gate and tees responder output into the current run;
- `tooling/step13-capture-state.ps1` captures focused PostgreSQL, exact retained Fragment/Image topics and physical file state without copying transcription text verbatim;
- `tooling/step13-run-path.ps1` prints the active run directory;
- `tooling/step13-import-rpc-diagnostics.ps1` validates a browser-exported redacted RPC diagnostic file and imports it into the active run only when all five required representative pairs are present;
- `validate-step13-tooling.py` statically verifies the Step 13 harness and client ACL prerequisite.

`RUNBOOK.md`, `CHECKLIST.md` and `MANUAL-EVIDENCE.md` define the two live phases and required evidence.

## Final live close-out — 2026-10-05

Step 13 is closed. Run `20261004-002349` proved the full disabled/enabled lifecycle across UI, responder, MQTT RPC, retained state, PostgreSQL and Files. Phase A used Fragment `2332` / Image `1`; Phase B used Image `89`, Image `90` and Fragment `2333`. Additional Fragment `2334` proved create/delete sequence closure without restart after the responder corrections. Focused RPC diagnostic Fragments `2335`/`2336` were removed after the five required request/reply pairs were imported and validated. Image `90` was deleted only after becoming unreferenced; Image `89` remains catalogued.

The raw run remains under ignored `build/0027-step13/runs/20261004-002349`; the permanent source-controlled summary is `FINAL-RUNTIME-CLOSEOUT.md`.

## Integration prerequisite corrected in Step 13

The live review found that the `diaries-client` MQTT identity did not yet have read permission for `diaries/images/+`. That permission is necessary for the first-class retained Image projection added in Step 3. Step 13 therefore adds only:

```text
topic read diaries/images/+
```

to the existing `diaries-client` ACL block. This is narrow metadata access. Image bytes continue to be served over HTTP/static Files routes. The local Mosquitto README now documents the client projection and the requirement to restart/reload Mosquitto after changing ACLs.

## Step 12 prerequisite closed

The normal development Angular/Karma run completed with `TOTAL: 222 SUCCESS` on 2026-10-04. The captured output is stored in `../Step 12/development-angular-test-green-20261004-001033.txt`. Step 12 is therefore closed before live Step 13 execution begins.

## Live execution progress — 2026-10-04

The development preflight run `20261004-002349` passed. PostgreSQL and Mosquitto were healthy, Angular dependencies were installed, the `diaries-client` Image-topic ACL was present and the effective Files root existed. The only warning was the expected absence of an existing IMAGE Fragment fixture; a disposable fixture is to be created with the gate enabled before Phase A. The captured output is `preflight-development-20261004-002349.txt`.

Starting the Angular client then exposed a strict template-type compilation error in the Step 11 Space-key accessibility binding. This is recorded in `client-ng-serve-template-type-failure-20261004-064046.txt` and corrected by changing the `onFileSpace` event parameter from `KeyboardEvent` to `Event`; see `client-ng-serve-template-type-fix.md`. No ImageFragment contract or runtime behaviour changes.


## Redacted RPC diagnostic capture added during live evidence consolidation

The functional Phase A/B lifecycle left one evidence gap: normal `RpcService` logging intentionally omits request `args`, so an exported browser console cannot by itself prove the positive-versus-null `imageId` wire shape. Step 13 now includes an opt-in `Step13RpcDiagnostics` capture in the client RPC layer. It is instantiated only in Angular development mode and records only `addImageFragment` / `updateFragment`, allow-lists non-secret Fragment/Image fields, records `imageIdState` as `omitted` / `positive` / `null`, and stores only text length rather than transcription text. Authentication values are never captured. Successful `addImageFragment` replies are reduced to a committed Fragment summary without raw text.

The browser helper `window.__diariesStep13RpcDiagnostics` can enable/clear/export/download the session-scoped evidence. `step13-import-rpc-diagnostics.ps1` validates the downloaded JSON for the five required 403/200 representative pairs and rejects files containing authentication/password keys or raw `text`. See `step13-rpc-diagnostic-capture.md`.

Package/static/runtime validation for this diagnostic increment is recorded in `step13-rpc-diagnostic-capture-validation.txt`; file hashes are in `step13-rpc-diagnostic-capture-source-files.sha256`.

## Safety model

The gate helper clones the developer-owned responder JSON into ignored `build/0027-step13`. Those generated files inherit local secrets and must never be copied into Git or change-control evidence. The harness records only gate state, runtime logs and business-state evidence. The runbook explicitly returns the responder to `imageFragmentWritesEnabled=false` after testing.

## Completion gate

Satisfied on 2026-10-05. Both phases in `RUNBOOK.md` were executed and the captured evidence reconciled client UI, responder outcome, retained MQTT state, database rows and physical Files state through the complete lifecycle.


## Live regression found and fixed — missing MARQUEE overlay

During gate-enabled fixture setup, selecting entries from the Day reader exposed a real client lifecycle regression: a MARQUEE Fragment could become selected while its rectangle was not selected/rendered on the source page. Browser logging showed the Fragment retained object arriving successfully, while no corresponding `diaries/marquees/<id>` subscription followed the Day-reader selection. Directly clicking the rectangle still selected both entities, proving the retained Marquee itself was present.

Two client behaviours combined to cause the failure:

1. `ModelContext.cleanupTopicTree()` completed the `destroy$` used by the root Fragment→Marquee synchronizer. Because `ModelContext` is a root singleton, that permanently disabled relationship synchronization for the remainder of the application session.
2. `DayviewComponent.goToFragment()` unconditionally called `setMarqueeId(null)`, even for a MARQUEE Fragment.

The correction makes `cleanupTopicTree()` transport/topic cleanup only and leaves the root relationship synchronizer alive. Day-view navigation now sets only the Fragment and authoritative page route; `ModelContext` derives the Marquee centrally from retained Fragment + page-Marquee state. This preserves the legacy fallback where `Fragment.marqueeId` itself may be null/stale while the Marquee is still discoverable by `fragmentId + pageId`. IMAGE selection still derives `null` and therefore never shows a Marquee.

Focused regression tests now prove that, even after `cleanupTopicTree()`, a MARQUEE Fragment resolves its retained Marquee and an IMAGE Fragment clears Marquee selection. Day-view tests also assert that navigation never writes Marquee state directly. See `missing-marquee-regression-fix.md`.

Before continuing Phase A, rerun the normal Angular suite and perform the live browser smoke sequence: MARQUEE → IMAGE → MARQUEE from the Day reader. The rectangle must appear, disappear, then reappear respectively.

The browser smoke sequence passed and the normal Angular/Karma suite then completed with **224/224 tests passing** (`TOTAL: 224 SUCCESS`), including the two new `ModelContext` lifecycle regressions. The captured run is `missing-marquee-regression-angular-green-20261004-085452.txt`. After the later Step 13 RPC diagnostic regression tests were added, the final normal Angular/Karma run completed with **229/229 tests passing** (`TOTAL: 229 SUCCESS`).

Phase A then exposed a second live integration defect: ordinary transcription save on IMAGE Fragment `2332` acquired its lock but `updateFragment` returned 400 and the client rolled the edit back. The client request still serialized `marqueeId:null`; mqtt-rpc 0.0.8 builds its immutable argument map with `Map.copyOf(args)`, which rejects explicit null values before `UpdateFragment.handleRequest()` is reached. `UpdateFragmentRequest` now omits the responder-authoritative `marqueeId` field entirely (as it already omits `imageId` for preserve semantics). `UpdateImageFragmentRequest` inherits the same null-free base, so positive replacement is fixed as well; explicit `imageId:null` clear continues through the existing null-preserving responder adapter. See `image-fragment-ordinary-update-null-marquee-fix.md`. Phase A must rerun the text-save operation after applying this correction.

The first post-fix Angular run compiled the corrected production request model but exposed two stale assertions in `image-fragment-rpc.spec.ts`: the ordinary IMAGE update and positive Image replacement contract tests still expected `marqueeId:null` in the outbound request. Those expectations described the pre-fix wire shape and contradicted the corrected contract. The RPC-contract tests now assert that `marqueeId` is absent from ordinary, replacement and clear update payloads, while the retained/returned `ImageFragment` model may still legitimately contain `marqueeId:null`. See `ordinary-update-rpc-contract-test-alignment.md`.

## Live regression found and fixed — delete left a sequence gap

Phase A deletion of disposable IMAGE Fragment `2332` exposed a responder lifecycle defect when the responder was restarted for the gate-enabled phase: startup normalisation changed the sequence numbers of the Fragments after the deleted position. The earlier drag/drop reorder path had normalised correctly; the gap was introduced by `DeleteFragment`, which committed the deletion without normalising the surviving date.

`DeleteFragment` now calls the existing `FragmentSequenceNormaliser.normaliseDate(...)` inside the same transaction as the delete. After commit it tombstones the deleted Fragment as before and republishes every survivor whose sequence/version changed, keeping PostgreSQL and both canonical/date retained Fragment topics immediately consistent. A handler regression models the exact mixed chronology around Fragment `2332`. See `delete-fragment-sequence-normalisation-fix.md`.

The package environment could not run Gradle because the wrapper distribution was unavailable, but the focused test was subsequently run on the development workstation and completed `BUILD SUCCESSFUL`. Live deletion of Fragments `2334` and `2333` also proved immediate survivor normalisation without responder restart.

## Live regression found and fixed — add left a fractional/unclosed chronology

Phase B creation of IMAGE Fragment `2333` exposed the create-side analogue of the earlier delete defect. `addImageFragment` committed the caller-supplied insertion sequence, and a subsequent responder restart normalised additional Fragments. The legacy MARQUEE `addFragment` path had the same lifecycle omission.

The handler-facing creation paths now create the new Fragment (and Marquee, for MARQUEE) and call `FragmentSequenceNormaliser.normaliseDate(...)` in the same transaction. The committed created Fragment is reloaded, then it and every Fragment renumbered by that add are republished to canonical and date retained topics. The lower-level `saveMarqueeFragment` / `saveImageFragment` helpers remain available for test/seeding code; RPC creation uses the new atomic create+normalise paths. Focused handler coverage inserts both IMAGE and MARQUEE Fragments into the middle of a mixed chronology. See `create-fragment-sequence-normalisation-fix.md`.

The focused responder suite covering `FragmentLifecycleContractTest`, `AddImageFragmentTest` and `AddFragmentContractTest` subsequently completed `BUILD SUCCESSFUL` on the development workstation. Live insertion of Fragment `2334` then proved immediate contiguous create-time normalisation, and its deletion proved immediate delete-time normalisation, both without responder restart.
