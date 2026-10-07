# Step 13 live verification runbook

This runbook verifies `0027-FEAT` against the real development MQTT broker, responder, PostgreSQL database, retained topic tree and Files root. Use a disposable development/integration dataset. Do **not** enable production authoring as part of Step 13.

## 0. Apply the Step 13 source drop-in

The Step 13 drop-in adds the one MQTT permission required by the new client Image projection:

```text
topic read diaries/images/+
```

under the existing `diaries-client` ACL block. Restart/reload the development Mosquitto broker after applying the package so the running broker sees the updated ACL. The narrow permission exposes Image metadata only; Image bytes remain on the HTTP/static Files route.

From the Diaries project root, either start development infrastructure or restart the broker if it is already running:

```bat
scripts\windows\development-infrastructure\start.bat
```

or:

```bat
docker restart diaries-development-mqtt
```

Then verify:

```bat
scripts\windows\development-infrastructure\status.bat
```

## 1. Start an evidence run and preflight

From a PowerShell prompt at the Diaries project root:

```powershell
$step13 = '.\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 13\tooling'
& "$step13\step13-begin.ps1"
& "$step13\step13-preflight.ps1"
```

The tooling writes live evidence under ignored `build/0027-step13/runs/<timestamp>/`. It never copies the responder JSON, MQTT passwords, access tokens or refresh tokens into change control.

If preflight reports that the development database contains no IMAGE Fragment, create one as disposable setup while the gate is enabled, then stop the responder and restart it with the gate disabled before beginning Phase A. Record that seeding action in `MANUAL-EVIDENCE.md`; it is setup, not Phase A evidence.

## 2. Start the Angular client

In a separate command prompt:

```bat
cd diaries-client
npm start
```

Use the normal editor account and keep the browser console open. Clear the console before each phase. Do not close the browser between individual lifecycle transitions unless the runbook explicitly calls for reload/restart evidence.

## 3. Phase A — authoring gate disabled

Stop any responder already running. In a separate PowerShell prompt at the project root run:

```powershell
$step13 = '.\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 13\tooling'
& "$step13\run-responder-step13.ps1" -Gate disabled
```

This creates a temporary base config under ignored `build/0027-step13/gate-disabled/`, sets `imageFragmentWritesEnabled=false`, and launches the normal direct-development responder. `%USERPROFILE%\.diaries\responder.json` is not modified.

Choose one existing IMAGE Fragment and note its Fragment ID and current Image ID. Capture the baseline, replacing the example IDs:

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-a-00-before' -FragmentIds 84 -ImageIds 101
```

Verify each item below in the UI. After a state-changing operation, capture state again using a new label.

1. Existing IMAGE Fragment loads and its Image metadata/preview resolves.
2. Edit transcription text; save succeeds.
3. Change the Fragment date; save succeeds.
4. Reorder it among a mixed MARQUEE/IMAGE day; normalisation succeeds.
5. Attempt **Select/replace Image**; responder rejects with 403 and the Fragment becomes unlocked again.
6. Attempt **Clear Image**; responder rejects with 403 and the Fragment becomes unlocked again.
7. Attempt **Add Image Fragment**; responder rejects with 403 and no new Fragment appears.
8. Delete a disposable IMAGE Fragment; Fragment deletion succeeds while its Image remains catalogued, and the surviving day is immediately renumbered to a contiguous sequence without restarting the responder.

Suggested capture labels:

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-a-01-after-text'      -FragmentIds 84 -ImageIds 101
& "$step13\step13-capture-state.ps1" -Label 'phase-a-02-after-date'      -FragmentIds 84 -ImageIds 101
& "$step13\step13-capture-state.ps1" -Label 'phase-a-03-after-reorder'   -FragmentIds 84 -ImageIds 101
& "$step13\step13-capture-state.ps1" -Label 'phase-a-04-after-replace-403' -FragmentIds 84 -ImageIds 101
& "$step13\step13-capture-state.ps1" -Label 'phase-a-05-after-clear-403' -FragmentIds 84 -ImageIds 101
```

For rejected reference mutations, confirm `database-image-fragments.txt` shows no changed `image_id` and no surviving lock (`lock_user_id` null and `has_lock_session=false`). The retained Fragment JSON must agree.

Save the Phase A browser console to the current run directory. To print the run directory:

```powershell
& "$step13\step13-run-path.ps1"
```

Name the file `browser-phase-a.txt` or `browser-phase-a.log`.

## 4. Phase B — authoring gate enabled

Stop the disabled-gate responder with Ctrl+C. Then start the enabled-gate responder:

```powershell
& "$step13\run-responder-step13.ps1" -Gate enabled
```

The generated gate config is again under ignored `build/0027-step13`; it sets `imageFragmentWritesEnabled=true`, and the developer-owned responder config remains untouched.

Use disposable Images/Fragments and record their IDs in `CHECKLIST.md`.

### B1. Upload/catalogue an Image

Upload an Image through the existing Files UI and confirm the returned/listed entry has a positive catalogue `imageId`.

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-01-uploaded' -ImageIds <IMAGE1_ID>
```

Expected agreement: Image DB row exists, retained `diaries/images/<id>` exists, physical file exists with the same relative path.

### B2. Create an IMAGE Fragment

Use **Add Image Fragment**, select Image 1, and record the returned Fragment ID.

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-02-created' -FragmentIds <FRAGMENT_ID> -ImageIds <IMAGE1_ID>
```

Expected: Fragment type `IMAGE`, `marqueeId`/Marquee relationship absent, `image_id=IMAGE1_ID`, retained Fragment and DB agree.

### B3. Prove retained restore

Reload the browser. For stronger evidence, stop and restart the responder with `-Gate enabled`, then reload the client. Confirm the same IMAGE Fragment/Image relationship reappears from database + retained replay. Capture:

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-03-after-restart' -FragmentIds <FRAGMENT_ID> -ImageIds <IMAGE1_ID>
```

### B4. Edit text

Change transcription text and save.

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-04-after-text' -FragmentIds <FRAGMENT_ID> -ImageIds <IMAGE1_ID>
```

The `text_md5`/length should change while `image_id` remains stable.

### B5. Move date

Change date and save; verify database, date-index behaviour visible in the UI, and retained Fragment date all agree.

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-05-after-date' -FragmentIds <FRAGMENT_ID> -ImageIds <IMAGE1_ID>
```

### B6. Mixed reorder

Reorder the IMAGE Fragment among MARQUEE Fragments. Verify normalised `sequence`/version values and unchanged `image_id`. Creation, reorder/update and later deletion must each leave the chronology normalised immediately after that operation.

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-06-after-reorder' -FragmentIds <FRAGMENT_ID> -ImageIds <IMAGE1_ID>
```

### B7. Replace the Image

Upload/catalogue Image 2 if needed, then **Select/replace Image**.

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-07-after-replace' -FragmentIds <FRAGMENT_ID> -ImageIds <IMAGE1_ID>,<IMAGE2_ID>
```

Expected: Fragment points to Image 2; both Image rows/topics/files still exist.

### B8. Delete guard for the old Image

If Image 1 has no remaining Fragment references, deleting it should now succeed. If another Fragment intentionally references Image 1, deletion must return 409 until that final reference is removed. Record which case you exercised. Capture both before and after the final-reference transition when testing the 409 path.

### B9. Clear Image

Use **Clear Image** and confirm the Fragment remains while `image_id` becomes null. Image 2 remains catalogued.

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-09-after-clear' -FragmentIds <FRAGMENT_ID> -ImageIds <IMAGE2_ID>
```

### B10. Reattach Image

Reattach Image 2 (or another disposable Image).

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-10-after-reattach' -FragmentIds <FRAGMENT_ID> -ImageIds <IMAGE2_ID>
```

### B11/B12. Delete the IMAGE Fragment; prove Image survives

Delete the Fragment. Then capture the deleted Fragment topic and Image state:

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-12-after-fragment-delete' -FragmentIds <FRAGMENT_ID> -ImageIds <IMAGE2_ID>
```

Expected: Fragment DB row absent; exact retained Fragment topic has no retained message; Image DB row/topic/file still exist. The surviving day must already have contiguous sequence values in PostgreSQL and retained Fragment topics; a responder restart must not be required to repair the chronology.

### B13. Delete the now-unreferenced Image

Delete Image 2 through the catalogue UI.

```powershell
& "$step13\step13-capture-state.ps1" -Label 'phase-b-13-after-image-delete' -ImageIds <IMAGE2_ID>
```

Expected: Image DB row absent, exact retained Image topic absent/tombstoned, physical file absent.

Save the Phase B browser console as `browser-phase-b.txt` in the run directory.

## 5. Representative MQTT request/reply evidence

Use the opt-in redacted client diagnostic capture implemented specifically for Step 13; do not use broad MQTT reply-topic credentials or copy authentication values into evidence. Full design/safety notes are in `step13-rpc-diagnostic-capture.md`.

In the browser DevTools console:

```javascript
window.__diariesStep13RpcDiagnostics.enable()
window.__diariesStep13RpcDiagnostics.clear()
window.__diariesStep13RpcDiagnostics.status()
```

The capture exists only in Angular development mode, is off by default, and only records `addImageFragment` / `updateFragment`. It allow-lists Fragment/Image identifiers, date/sequence/version, `imageId` state/value, `marqueeId` presence state and text length. It never stores access/refresh tokens, passwords, MQTT credentials or transcription text. Successful `addImageFragment` replies include a redacted committed Fragment summary.

Repeat only the small disposable sequence needed to obtain these five pairs:

- Phase A `addImageFragment` -> 403;
- Phase A `updateFragment` carrying a positive/null Image-reference mutation -> 403;
- Phase B `addImageFragment` -> 200 with a redacted committed Fragment reply;
- Phase B `updateFragment` with positive `imageId` -> 200;
- Phase B `updateFragment` with `imageId:null` -> 200.

Entries persist in browser `sessionStorage`, so switching the responder from disabled gate to enabled gate does not lose Phase A evidence. When all five pairs have been exercised:

```javascript
window.__diariesStep13RpcDiagnostics.download()
```

Import the downloaded JSON into the active Step 13 run:

```powershell
& "$step13\step13-import-rpc-diagnostics.ps1" `
  -Path "$env:USERPROFILE\Downloads\step13-rpc-diagnostics-<timestamp>.json"
```

The importer copies nothing unless all five required function/status/`imageId` combinations are present and the JSON contains no forbidden authentication/password keys or raw `text` field. On success it writes `rpc-diagnostics.json` and `rpc-diagnostics-validation.txt` into the current run.

Then disable the diagnostic capture:

```javascript
window.__diariesStep13RpcDiagnostics.disable()
```

Use `MANUAL-EVIDENCE.md` to record the validated file and the five correlation IDs.

## 6. Finish Phase B safely

When live verification is complete, stop the enabled responder. Restart it with the gate disabled if you continue development:

```powershell
& "$step13\run-responder-step13.ps1" -Gate disabled
```

Do not leave the development responder accidentally enabled when you no longer need IMAGE authoring tests.

The generated gate configs under `build/0027-step13/gate-*` are disposable and contain local secrets inherited from your responder config. They must never be copied into Git/change-control evidence.

## 7. Evidence needed to close Step 13

Return/capture:

- `preflight.txt`;
- `responder-gate-disabled.log` and `responder-gate-enabled.log`;
- Phase A/B browser console files;
- each labelled state-capture directory used above;
- representative redacted MQTT request/reply payloads;
- completed `CHECKLIST.md` / `MANUAL-EVIDENCE.md` notes.

Step 13 closes only when the client, responder, retained MQTT state, PostgreSQL rows and physical Files state agree after every exercised lifecycle transition.
